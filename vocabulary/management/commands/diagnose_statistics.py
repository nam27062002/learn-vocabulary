"""
Django management command to diagnose statistics tracking issues.
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
from vocabulary.statistics_utils import get_user_statistics_summary


class Command(BaseCommand):
    help = 'Diagnose statistics tracking issues and identify inflated question counts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to diagnose (if not provided, will check all users)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix identified issues',
        )

    def handle(self, *args, **options):
        username = options.get('user')
        days = options.get('days', 30)
        fix_issues = options.get('fix', False)

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
            self.stdout.write(f"DIAGNOSING USER: {user.username}")
            self.stdout.write(f"{'='*60}")
            
            self.diagnose_user_statistics(user, days, fix_issues)

    def diagnose_user_statistics(self, user, days, fix_issues):
        """Diagnose statistics issues for a specific user."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)

        # 1. Check StudySession data
        self.stdout.write(f"\n1. STUDY SESSIONS ANALYSIS:")
        sessions = StudySession.objects.filter(
            user=user,
            session_start__date__range=[start_date, end_date]
        )
        
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(session_end__isnull=False).count()
        incomplete_sessions = sessions.filter(session_end__isnull=True).count()
        
        self.stdout.write(f"   Total sessions: {total_sessions}")
        self.stdout.write(f"   Completed sessions: {completed_sessions}")
        self.stdout.write(f"   Incomplete sessions: {incomplete_sessions}")
        
        if incomplete_sessions > 0:
            self.stdout.write(
                self.style.WARNING(f"   ⚠️  Found {incomplete_sessions} incomplete sessions")
            )
            if fix_issues:
                self.stdout.write("   🔧 Ending incomplete sessions...")
                from vocabulary.statistics_utils import end_study_session
                for session in sessions.filter(session_end__isnull=True):
                    end_study_session(session)
                self.stdout.write(f"   ✅ Ended {incomplete_sessions} incomplete sessions")

        # 2. Check StudySessionAnswer data
        self.stdout.write(f"\n2. STUDY SESSION ANSWERS ANALYSIS:")
        answers = StudySessionAnswer.objects.filter(
            session__user=user,
            session__session_start__date__range=[start_date, end_date]
        )
        
        total_answers = answers.count()
        session_questions_sum = sessions.aggregate(
            total=Sum('total_questions')
        )['total'] or 0
        
        self.stdout.write(f"   Total StudySessionAnswer records: {total_answers}")
        self.stdout.write(f"   Sum of session.total_questions: {session_questions_sum}")
        
        if total_answers != session_questions_sum:
            self.stdout.write(
                self.style.ERROR(
                    f"   ❌ MISMATCH: Answer records ({total_answers}) != "
                    f"Session totals ({session_questions_sum})"
                )
            )
        else:
            self.stdout.write("   ✅ Answer records match session totals")

        # 3. Check for duplicate answers
        self.stdout.write(f"\n3. DUPLICATE ANSWERS CHECK:")
        duplicate_answers = answers.values(
            'session', 'flashcard', 'answered_at'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicate_answers.exists():
            duplicate_count = duplicate_answers.count()
            self.stdout.write(
                self.style.ERROR(f"   ❌ Found {duplicate_count} potential duplicate answer groups")
            )
            
            # Show some examples
            for dup in duplicate_answers[:5]:
                self.stdout.write(f"      Session {dup['session']}, Card {dup['flashcard']}: {dup['count']} records")
                
            if fix_issues:
                self.stdout.write("   🔧 Removing duplicate answers...")
                # Keep only the first answer for each session/flashcard/time combination
                for dup in duplicate_answers:
                    dup_answers = answers.filter(
                        session=dup['session'],
                        flashcard=dup['flashcard'],
                        answered_at=dup['answered_at']
                    ).order_by('id')
                    
                    # Delete all but the first
                    dup_answers[1:].delete()
                
                self.stdout.write(f"   ✅ Removed duplicate answers")
        else:
            self.stdout.write("   ✅ No duplicate answers found")

        # 4. Check DailyStatistics data
        self.stdout.write(f"\n4. DAILY STATISTICS ANALYSIS:")
        daily_stats = DailyStatistics.objects.filter(
            user=user,
            date__range=[start_date, end_date]
        )
        
        daily_questions_sum = daily_stats.aggregate(
            total=Sum('total_questions_answered')
        )['total'] or 0
        
        self.stdout.write(f"   Daily stats records: {daily_stats.count()}")
        self.stdout.write(f"   Sum of daily questions: {daily_questions_sum}")
        self.stdout.write(f"   Session questions sum: {session_questions_sum}")
        
        if daily_questions_sum != session_questions_sum:
            self.stdout.write(
                self.style.ERROR(
                    f"   ❌ MISMATCH: Daily stats ({daily_questions_sum}) != "
                    f"Session totals ({session_questions_sum})"
                )
            )
            
            if fix_issues:
                self.stdout.write("   🔧 Recalculating daily statistics...")
                from vocabulary.statistics_utils import update_daily_statistics
                
                # Recalculate for each day in the period
                current_date = start_date
                while current_date <= end_date:
                    update_daily_statistics(user, current_date)
                    current_date += timedelta(days=1)
                
                self.stdout.write("   ✅ Recalculated daily statistics")
        else:
            self.stdout.write("   ✅ Daily statistics match session totals")

        # 5. Check for sessions with unrealistic question counts
        self.stdout.write(f"\n5. UNREALISTIC SESSION CHECK:")
        high_question_sessions = sessions.filter(total_questions__gt=1000)
        
        if high_question_sessions.exists():
            self.stdout.write(
                self.style.ERROR(f"   ❌ Found {high_question_sessions.count()} sessions with >1000 questions")
            )
            
            for session in high_question_sessions[:5]:
                self.stdout.write(
                    f"      Session {session.id}: {session.total_questions} questions "
                    f"({session.session_start})"
                )
                
                # Check actual answer count for this session
                actual_answers = StudySessionAnswer.objects.filter(session=session).count()
                self.stdout.write(f"        Actual answers: {actual_answers}")
                
                if fix_issues and actual_answers != session.total_questions:
                    self.stdout.write(f"        🔧 Fixing session question count...")
                    session.total_questions = actual_answers
                    session.correct_answers = StudySessionAnswer.objects.filter(
                        session=session, is_correct=True
                    ).count()
                    session.incorrect_answers = StudySessionAnswer.objects.filter(
                        session=session, is_correct=False
                    ).count()
                    session.save()
                    self.stdout.write(f"        ✅ Fixed session {session.id}")
        else:
            self.stdout.write("   ✅ No sessions with unrealistic question counts")

        # 6. Show current statistics summary
        self.stdout.write(f"\n6. CURRENT STATISTICS SUMMARY:")
        stats = get_user_statistics_summary(user, days)
        self.stdout.write(f"   Questions answered (last {days} days): {stats['total_questions_answered']}")
        self.stdout.write(f"   Correct answers: {stats['correct_answers']}")
        self.stdout.write(f"   Incorrect answers: {stats['incorrect_answers']}")
        self.stdout.write(f"   Accuracy: {stats['accuracy_percentage']}%")
        self.stdout.write(f"   Study sessions: {stats['study_sessions_count']}")
        self.stdout.write(f"   Study time: {stats['total_study_time_hours']} hours")

        # 7. Check for recent activity patterns
        self.stdout.write(f"\n7. RECENT ACTIVITY PATTERNS:")
        recent_sessions = sessions.filter(
            session_start__gte=timezone.now() - timedelta(days=7)
        ).order_by('-session_start')[:10]
        
        if recent_sessions.exists():
            self.stdout.write("   Recent sessions (last 7 days):")
            for session in recent_sessions:
                duration = session.duration_formatted if session.session_end else "ongoing"
                self.stdout.write(
                    f"      {session.session_start.strftime('%Y-%m-%d %H:%M')} - "
                    f"{session.total_questions} questions, {duration}"
                )
        else:
            self.stdout.write("   No recent sessions found")

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"DIAGNOSIS COMPLETE FOR {user.username}")
        self.stdout.write(f"{'='*60}")
