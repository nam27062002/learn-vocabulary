"""
Django management command to fix inflated statistics by recalculating from actual data.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from vocabulary.models import (
    StudySession, StudySessionAnswer, DailyStatistics, 
    WeeklyStatistics, Flashcard
)
from vocabulary.statistics_utils import update_daily_statistics, update_weekly_statistics


class Command(BaseCommand):
    help = 'Fix inflated statistics by recalculating from actual session data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to fix (if not provided, will fix all users)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Number of days to recalculate (default: 365)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        username = options.get('user')
        days = options.get('days', 365)
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        if username:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" not found')
                )
                return
        else:
            users = User.objects.all()

        for user in users:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"FIXING STATISTICS FOR USER: {user.username}")
            self.stdout.write(f"{'='*60}")
            
            self.fix_user_statistics(user, days, dry_run)

    def fix_user_statistics(self, user, days, dry_run):
        """Fix statistics issues for a specific user."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)

        # 1. Fix StudySession data first
        self.stdout.write(f"\n1. FIXING STUDY SESSIONS:")
        sessions = StudySession.objects.filter(
            user=user,
            session_start__date__range=[start_date, end_date]
        )
        
        fixed_sessions = 0
        for session in sessions:
            # Get actual answer count for this session
            actual_answers = StudySessionAnswer.objects.filter(session=session).count()
            actual_correct = StudySessionAnswer.objects.filter(
                session=session, is_correct=True
            ).count()
            actual_incorrect = StudySessionAnswer.objects.filter(
                session=session, is_correct=False
            ).count()
            
            # Check if session data is incorrect
            if (session.total_questions != actual_answers or 
                session.correct_answers != actual_correct or 
                session.incorrect_answers != actual_incorrect):
                
                self.stdout.write(
                    f"   Session {session.id}: {session.total_questions} -> {actual_answers} questions"
                )
                
                if not dry_run:
                    session.total_questions = actual_answers
                    session.correct_answers = actual_correct
                    session.incorrect_answers = actual_incorrect
                    
                    # Recalculate unique words
                    unique_words = StudySessionAnswer.objects.filter(
                        session=session
                    ).values('flashcard').distinct().count()
                    session.words_studied = unique_words
                    
                    # Recalculate average response time
                    if actual_answers > 0:
                        avg_response_time = StudySessionAnswer.objects.filter(
                            session=session
                        ).aggregate(avg=Sum('response_time_seconds'))['avg'] or 0
                        session.average_response_time = avg_response_time / actual_answers
                    else:
                        session.average_response_time = 0
                    
                    session.save(update_fields=[
                        'total_questions', 'correct_answers', 'incorrect_answers',
                        'words_studied', 'average_response_time'
                    ])
                
                fixed_sessions += 1
        
        self.stdout.write(f"   Fixed {fixed_sessions} sessions")

        # 2. End incomplete sessions
        self.stdout.write(f"\n2. ENDING INCOMPLETE SESSIONS:")
        incomplete_sessions = sessions.filter(session_end__isnull=True)
        if incomplete_sessions.exists():
            self.stdout.write(f"   Found {incomplete_sessions.count()} incomplete sessions")
            if not dry_run:
                from vocabulary.statistics_utils import end_study_session
                for session in incomplete_sessions:
                    end_study_session(session)
                self.stdout.write(f"   Ended {incomplete_sessions.count()} incomplete sessions")
        else:
            self.stdout.write("   No incomplete sessions found")

        # 3. Remove duplicate StudySessionAnswer records
        self.stdout.write(f"\n3. REMOVING DUPLICATE ANSWERS:")
        answers = StudySessionAnswer.objects.filter(
            session__user=user,
            session__session_start__date__range=[start_date, end_date]
        )
        
        # Find duplicates based on session, flashcard, and timestamp (within 1 second)
        duplicate_count = 0
        processed_combinations = set()
        
        for answer in answers.order_by('session', 'flashcard', 'answered_at'):
            # Create a key for this answer (session, flashcard, rounded timestamp)
            timestamp_key = int(answer.answered_at.timestamp())
            key = (answer.session_id, answer.flashcard_id, timestamp_key)
            
            if key in processed_combinations:
                # This is a duplicate
                self.stdout.write(
                    f"   Removing duplicate: Session {answer.session_id}, "
                    f"Card {answer.flashcard_id}, Time {answer.answered_at}"
                )
                if not dry_run:
                    answer.delete()
                duplicate_count += 1
            else:
                processed_combinations.add(key)
        
        self.stdout.write(f"   Removed {duplicate_count} duplicate answers")

        # 4. Recalculate daily statistics
        self.stdout.write(f"\n4. RECALCULATING DAILY STATISTICS:")
        if not dry_run:
            current_date = start_date
            recalculated_days = 0
            while current_date <= end_date:
                update_daily_statistics(user, current_date)
                recalculated_days += 1
                current_date += timedelta(days=1)
            
            self.stdout.write(f"   Recalculated {recalculated_days} days of statistics")
        else:
            self.stdout.write(f"   Would recalculate {days} days of statistics")

        # 5. Recalculate weekly statistics
        self.stdout.write(f"\n5. RECALCULATING WEEKLY STATISTICS:")
        if not dry_run:
            # Get all unique weeks in the date range
            weeks_to_update = set()
            current_date = start_date
            while current_date <= end_date:
                year, week_number, _ = current_date.isocalendar()
                weeks_to_update.add((year, week_number))
                current_date += timedelta(days=1)
            
            for year, week_number in weeks_to_update:
                # Calculate week start date
                week_start = timezone.datetime.strptime(f'{year}-W{week_number}-1', "%Y-W%W-%w").date()
                update_weekly_statistics(user, week_start)
            
            self.stdout.write(f"   Recalculated {len(weeks_to_update)} weeks of statistics")
        else:
            self.stdout.write("   Would recalculate weekly statistics")

        # 6. Show corrected statistics
        self.stdout.write(f"\n6. CORRECTED STATISTICS SUMMARY:")
        from vocabulary.statistics_utils import get_user_statistics_summary
        
        if not dry_run:
            stats = get_user_statistics_summary(user, 30)
            self.stdout.write(f"   Questions answered (last 30 days): {stats['total_questions_answered']}")
            self.stdout.write(f"   Correct answers: {stats['correct_answers']}")
            self.stdout.write(f"   Incorrect answers: {stats['incorrect_answers']}")
            self.stdout.write(f"   Accuracy: {stats['accuracy_percentage']}%")
            self.stdout.write(f"   Study sessions: {stats['study_sessions_count']}")
        else:
            self.stdout.write("   Statistics would be recalculated after fixes")

        # 7. Validation check
        self.stdout.write(f"\n7. VALIDATION CHECK:")
        sessions_after = StudySession.objects.filter(
            user=user,
            session_start__date__range=[start_date, end_date],
            session_end__isnull=False
        )
        
        total_session_questions = sessions_after.aggregate(
            total=Sum('total_questions')
        )['total'] or 0
        
        total_answer_records = StudySessionAnswer.objects.filter(
            session__user=user,
            session__session_start__date__range=[start_date, end_date]
        ).count()
        
        if total_session_questions == total_answer_records:
            self.stdout.write("   ✅ Session totals match answer records")
        else:
            self.stdout.write(
                f"   ❌ STILL MISMATCHED: Sessions ({total_session_questions}) != "
                f"Answers ({total_answer_records})"
            )

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"STATISTICS FIX COMPLETE FOR {user.username}")
        self.stdout.write(f"{'='*60}")
