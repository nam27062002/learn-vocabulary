from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import CustomUser
import os


class Command(BaseCommand):
    help = 'Clean up orphaned avatar references in database'

    def handle(self, *args, **options):
        users_with_avatars = CustomUser.objects.exclude(avatar='').exclude(avatar=None)
        cleaned = 0
        
        for user in users_with_avatars:
            avatar_path = os.path.join(settings.MEDIA_ROOT, str(user.avatar))
            
            if not os.path.exists(avatar_path):
                self.stdout.write(
                    f'Cleaning orphaned avatar for user {user.email}: {user.avatar}'
                )
                user.avatar = None
                user.save(update_fields=['avatar'])
                cleaned += 1
            else:
                self.stdout.write(
                    f'Valid avatar for user {user.email}: {user.avatar}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned {cleaned} orphaned avatar references')
        )