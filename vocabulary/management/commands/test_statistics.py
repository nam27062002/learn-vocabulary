"""
Management command to test the statistics functionality.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from vocabulary.statistics_utils import get_user_statistics_summary

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the statistics functionality'

    def handle(self, *args, **options):
        self.stdout.write("Testing statistics functionality...")
        
        # Get first user
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found"))
            return
        
        self.stdout.write(f"Testing with user: {user.username}")
        
        try:
            # Test statistics summary
            stats = get_user_statistics_summary(user, 30)
            self.stdout.write("Statistics summary:")
            for key, value in stats.items():
                self.stdout.write(f"  {key}: {value}")
            
            self.stdout.write(self.style.SUCCESS("Statistics test completed successfully!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error testing statistics: {str(e)}"))
            import traceback
            traceback.print_exc()
