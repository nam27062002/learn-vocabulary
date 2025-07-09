from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Xóa user khỏi database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email của user cần xóa',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='ID của user cần xóa',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Liệt kê tất cả users',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Xác nhận xóa không cần hỏi',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_users()
            return

        if not options['email'] and not options['id']:
            raise CommandError('Phải cung cấp --email hoặc --id để xóa user')

        if options['email'] and options['id']:
            raise CommandError('Chỉ có thể sử dụng --email HOẶC --id, không thể dùng cả hai')

        try:
            if options['email']:
                user = User.objects.get(email=options['email'])
            else:
                user = User.objects.get(id=options['id'])

            self.stdout.write(f"🔍 Tìm thấy user:")
            self.stdout.write(f"  - ID: {user.id}")
            self.stdout.write(f"  - Email: {user.email}")
            self.stdout.write(f"  - Ngày tham gia: {user.date_joined}")
            self.stdout.write(f"  - Số flashcards: {user.flashcards.count()}")

            if not options['confirm']:
                confirm = input("\n⚠️  Bạn có chắc muốn xóa user này? (yes/no): ")
                if confirm.lower() != 'yes':
                    self.stdout.write(self.style.WARNING('❌ Đã hủy thao tác xóa'))
                    return

            with transaction.atomic():
                user.delete()

            self.stdout.write(
                self.style.SUCCESS(f'✅ Đã xóa thành công user: {user.email}')
            )

        except User.DoesNotExist:
            if options['email']:
                raise CommandError(f'❌ Không tìm thấy user với email: {options["email"]}')
            else:
                raise CommandError(f'❌ Không tìm thấy user với ID: {options["id"]}')

    def list_users(self):
        users = User.objects.all()
        self.stdout.write(f"\n📋 Danh sách tất cả users ({users.count()} users):")
        
        if not users.exists():
            self.stdout.write("  (Không có user nào)")
            return

        for user in users:
            flashcard_count = user.flashcards.count()
            self.stdout.write(
                f"  - ID: {user.id} | Email: {user.email} | "
                f"Flashcards: {flashcard_count} | Joined: {user.date_joined.strftime('%d/%m/%Y')}"
            ) 