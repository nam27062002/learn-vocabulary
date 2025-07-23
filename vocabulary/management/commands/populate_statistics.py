"""
Management command to populate statistics from existing flashcard data.
This is useful for migrating existing data to the new statistics system.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta, date
from vocabulary.models import Flashcard, DailyStatistics, WeeklyStatistics
from vocabulary.statistics_utils import update_daily_statistics, update_weekly_statistics

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate statistics from existing flashcard data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days back to populate statistics (default: 90)'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username to populate statistics for (default: all users)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing statistics'
        )

    def handle(self, *args, **options):
        days = options['days']
        username = options.get('user')
        force = options['force']
        
        self.stdout.write(f"Populating statistics for the last {days} days...")
        
        # Get users to process
        if username:
            try:
                users = [User.objects.get(username=username)]
                self.stdout.write(f"Processing user: {username}")
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User '{username}' not found")
                )
                return
        else:
            users = User.objects.all()
            self.stdout.write(f"Processing {users.count()} users")
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        total_days_processed = 0
        total_weeks_processed = 0
        
        for user in users:
            self.stdout.write(f"\nProcessing user: {user.username}")
            
            # Get user's flashcards
            user_cards = Flashcard.objects.filter(user=user)
            if not user_cards.exists():
                self.stdout.write(f"  No flashcards found for {user.username}")
                continue
            
            days_processed = 0
            weeks_processed = 0
            
            # Process each day
            current_date = start_date
            while current_date <= end_date:
                # Check if daily stats already exist
                daily_stat_exists = DailyStatistics.objects.filter(
                    user=user, 
                    date=current_date
                ).exists()
                
                if daily_stat_exists and not force:
                    current_date += timedelta(days=1)
                    continue
                
                # Get cards created on this day
                cards_created = user_cards.filter(
                    created_at__date=current_date
                ).count()
                
                # Get cards reviewed on this day (approximate from last_reviewed)
                cards_reviewed = user_cards.filter(
                    last_reviewed__date=current_date
                ).count()
                
                # Create or update daily statistics
                if cards_created > 0 or cards_reviewed > 0:
                    daily_stat, created = DailyStatistics.objects.get_or_create(
                        user=user,
                        date=current_date,
                        defaults={
                            'is_study_day': cards_reviewed > 0,
                            'total_study_time_seconds': cards_reviewed * 30,  # Estimate 30 seconds per review
                            'total_questions_answered': cards_reviewed,
                            'correct_answers': int(cards_reviewed * 0.7),  # Estimate 70% accuracy
                            'incorrect_answers': int(cards_reviewed * 0.3),
                            'unique_words_studied': cards_reviewed,
                            'study_sessions_count': 1 if cards_reviewed > 0 else 0,
                            'average_session_duration': cards_reviewed * 30 if cards_reviewed > 0 else 0,
                            'new_cards_created': cards_created,
                        }
                    )
                    
                    if not created and force:
                        # Update existing record
                        daily_stat.is_study_day = cards_reviewed > 0
                        daily_stat.total_study_time_seconds = cards_reviewed * 30
                        daily_stat.total_questions_answered = cards_reviewed
                        daily_stat.correct_answers = int(cards_reviewed * 0.7)
                        daily_stat.incorrect_answers = int(cards_reviewed * 0.3)
                        daily_stat.unique_words_studied = cards_reviewed
                        daily_stat.study_sessions_count = 1 if cards_reviewed > 0 else 0
                        daily_stat.average_session_duration = cards_reviewed * 30 if cards_reviewed > 0 else 0
                        daily_stat.new_cards_created = cards_created
                        daily_stat.save()
                    
                    if created or force:
                        days_processed += 1
                
                current_date += timedelta(days=1)
            
            # Update weekly statistics
            current_date = start_date
            processed_weeks = set()
            
            while current_date <= end_date:
                year, week_number, _ = current_date.isocalendar()
                week_key = (year, week_number)
                
                if week_key not in processed_weeks:
                    # Check if weekly stats already exist
                    weekly_stat_exists = WeeklyStatistics.objects.filter(
                        user=user,
                        year=year,
                        week_number=week_number
                    ).exists()
                    
                    if not weekly_stat_exists or force:
                        update_weekly_statistics(user, current_date)
                        weeks_processed += 1
                        processed_weeks.add(week_key)
                
                current_date += timedelta(days=1)
            
            self.stdout.write(
                f"  Processed {days_processed} days and {weeks_processed} weeks for {user.username}"
            )
            total_days_processed += days_processed
            total_weeks_processed += weeks_processed
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Processed {total_days_processed} daily records "
                f"and {total_weeks_processed} weekly records across all users."
            )
        )
        
        # Show summary statistics
        total_daily_stats = DailyStatistics.objects.count()
        total_weekly_stats = WeeklyStatistics.objects.count()
        
        self.stdout.write(f"\nDatabase now contains:")
        self.stdout.write(f"  - {total_daily_stats} daily statistics records")
        self.stdout.write(f"  - {total_weekly_stats} weekly statistics records")
