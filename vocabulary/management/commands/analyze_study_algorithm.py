from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard
from django.db.models import Avg, Count, Q
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Analyze the performance of the enhanced study algorithm'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to analyze (optional, analyzes all users if not provided)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back for analysis (default: 7)',
        )

    def handle(self, *args, **options):
        username = options.get('user')
        days = options.get('days')
        
        # Filter users
        if username:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" not found')
                )
                return
        else:
            users = User.objects.filter(flashcards__isnull=False).distinct()

        self.stdout.write(
            self.style.SUCCESS(f'Analyzing study algorithm performance for the last {days} days')
        )
        self.stdout.write('=' * 80)

        total_stats = {
            'total_cards': 0,
            'total_reviews': 0,
            'total_correct': 0,
            'avg_difficulty': 0,
            'cards_with_reviews': 0
        }

        for user in users:
            self.analyze_user(user, days, total_stats)

        # Overall statistics
        if total_stats['cards_with_reviews'] > 0:
            overall_accuracy = (total_stats['total_correct'] / total_stats['total_reviews']) * 100 if total_stats['total_reviews'] > 0 else 0
            avg_difficulty = total_stats['avg_difficulty'] / total_stats['cards_with_reviews']
            
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('OVERALL STATISTICS'))
            self.stdout.write('=' * 80)
            self.stdout.write(f"Total Users Analyzed: {len(users)}")
            self.stdout.write(f"Total Cards: {total_stats['total_cards']}")
            self.stdout.write(f"Cards with Reviews: {total_stats['cards_with_reviews']}")
            self.stdout.write(f"Total Reviews: {total_stats['total_reviews']}")
            self.stdout.write(f"Overall Accuracy: {overall_accuracy:.1f}%")
            self.stdout.write(f"Average Difficulty Score: {avg_difficulty:.2f}")

    def analyze_user(self, user, days, total_stats):
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get user's flashcards
        cards = Flashcard.objects.filter(user=user)
        cards_with_reviews = cards.filter(total_reviews__gt=0)
        
        if not cards_with_reviews.exists():
            return

        # Calculate statistics
        total_cards = cards.count()
        total_reviews = sum(card.total_reviews for card in cards_with_reviews)
        total_correct = sum(card.correct_reviews for card in cards_with_reviews)
        accuracy = (total_correct / total_reviews * 100) if total_reviews > 0 else 0
        
        # Difficulty analysis
        avg_difficulty = cards_with_reviews.aggregate(avg_diff=Avg('difficulty_score'))['avg_diff'] or 0
        
        # Cards by difficulty level
        very_easy = cards_with_reviews.filter(difficulty_score__lte=0.2).count()
        easy = cards_with_reviews.filter(difficulty_score__gt=0.2, difficulty_score__lte=0.4).count()
        medium = cards_with_reviews.filter(difficulty_score__gt=0.4, difficulty_score__lte=0.6).count()
        hard = cards_with_reviews.filter(difficulty_score__gt=0.6, difficulty_score__lte=0.8).count()
        very_hard = cards_with_reviews.filter(difficulty_score__gt=0.8).count()
        
        # Recent activity
        recently_reviewed = cards.filter(last_reviewed__gte=cutoff_date).count()
        due_today = cards.filter(next_review__lte=datetime.now().date()).count()
        
        # Update total stats
        total_stats['total_cards'] += total_cards
        total_stats['total_reviews'] += total_reviews
        total_stats['total_correct'] += total_correct
        total_stats['avg_difficulty'] += avg_difficulty
        total_stats['cards_with_reviews'] += cards_with_reviews.count()

        # Display user statistics
        self.stdout.write(f"\nUser: {user.username}")
        self.stdout.write('-' * 40)
        self.stdout.write(f"Total Cards: {total_cards}")
        self.stdout.write(f"Cards with Reviews: {cards_with_reviews.count()}")
        self.stdout.write(f"Total Reviews: {total_reviews}")
        self.stdout.write(f"Accuracy: {accuracy:.1f}%")
        self.stdout.write(f"Average Difficulty: {avg_difficulty:.2f}")
        self.stdout.write(f"Recently Reviewed ({days} days): {recently_reviewed}")
        self.stdout.write(f"Due Today: {due_today}")
        
        self.stdout.write("\nDifficulty Distribution:")
        self.stdout.write(f"  Very Easy (≤0.2): {very_easy}")
        self.stdout.write(f"  Easy (0.2-0.4): {easy}")
        self.stdout.write(f"  Medium (0.4-0.6): {medium}")
        self.stdout.write(f"  Hard (0.6-0.8): {hard}")
        self.stdout.write(f"  Very Hard (>0.8): {very_hard}")
