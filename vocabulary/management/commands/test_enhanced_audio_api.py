"""
Management command to test enhanced audio API endpoints
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from vocabulary.models import Flashcard, Deck
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Test enhanced audio API endpoints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--card-id',
            type=int,
            help='Specific card ID to test with',
        )
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test data if it doesn\'t exist',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Testing Enhanced Audio API Endpoints'))
        self.stdout.write('=' * 60)

        # Get or create test user
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={'is_active': True}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Created test user: {user.email}'))
        else:
            self.stdout.write(f'✅ Using existing test user: {user.email}')

        # Get or create test data if requested
        if options['create_test_data']:
            deck, created = Deck.objects.get_or_create(
                name='API Test Deck',
                user=user
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created test deck: {deck.name}'))

            flashcard, created = Flashcard.objects.get_or_create(
                word='api_test',
                user=user,
                deck=deck,
                defaults={
                    'phonetic': '/ˈeɪ.pi.aɪ/',
                    'part_of_speech': 'noun',
                    'audio_url': 'https://original-audio.mp3'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created test flashcard: {flashcard.word}'))

        # Get card to test with
        card_id = options.get('card_id')
        if card_id:
            try:
                flashcard = Flashcard.objects.get(id=card_id, user=user)
                self.stdout.write(f'✅ Using specified flashcard: {flashcard.word} (ID: {flashcard.id})')
            except Flashcard.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Flashcard with ID {card_id} not found'))
                return
        else:
            flashcard = Flashcard.objects.filter(user=user).first()
            if not flashcard:
                self.stdout.write(self.style.ERROR('❌ No flashcards found. Use --create-test-data to create test data.'))
                return
            self.stdout.write(f'✅ Using first available flashcard: {flashcard.word} (ID: {flashcard.id})')

        # Create test client with proper server name
        client = Client(SERVER_NAME='localhost')
        client.force_login(user)

        self.stdout.write('\n🧪 Testing API Endpoints')
        self.stdout.write('-' * 40)

        # Test 1: Fetch Enhanced Audio
        self.stdout.write('\n1️⃣ Testing fetch-enhanced-audio endpoint...')
        try:
            response = client.post('/api/fetch-enhanced-audio/', {
                'card_id': flashcard.id,
                'word': flashcard.word
            }, content_type='application/json')

            self.stdout.write(f'   Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(self.style.SUCCESS(f'   ✅ Success: {data.get("success", False)}'))
                self.stdout.write(f'   Word: {data.get("word", "N/A")}')
                self.stdout.write(f'   Audio options found: {data.get("total_found", 0)}')
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Failed: {response.content.decode()}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Exception: {e}'))

        # Test 2: Update Flashcard Audio
        self.stdout.write('\n2️⃣ Testing update-flashcard-audio endpoint...')
        
        # Store original audio URL
        original_audio = flashcard.audio_url
        test_audio_url = 'https://test-updated-audio.mp3'
        
        try:
            response = client.post('/api/update-flashcard-audio/', {
                'card_id': flashcard.id,
                'audio_url': test_audio_url
            }, content_type='application/json')

            self.stdout.write(f'   Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(self.style.SUCCESS(f'   ✅ Success: {data.get("success", False)}'))
                self.stdout.write(f'   Card ID: {data.get("card_id", "N/A")}')
                self.stdout.write(f'   New audio URL: {data.get("audio_url", "N/A")}')
                
                # Verify database update
                flashcard.refresh_from_db()
                if flashcard.audio_url == test_audio_url:
                    self.stdout.write(self.style.SUCCESS('   ✅ Database update verified'))
                else:
                    self.stdout.write(self.style.ERROR(f'   ❌ Database update failed. Expected: {test_audio_url}, Got: {flashcard.audio_url}'))
                
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Failed: {response.content.decode()}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Exception: {e}'))

        # Test 3: Verify Database State
        self.stdout.write('\n3️⃣ Verifying final database state...')
        flashcard.refresh_from_db()
        self.stdout.write(f'   Original audio: {original_audio}')
        self.stdout.write(f'   Current audio: {flashcard.audio_url}')
        
        if flashcard.audio_url == test_audio_url:
            self.stdout.write(self.style.SUCCESS('   ✅ Database state is correct'))
        else:
            self.stdout.write(self.style.WARNING('   ⚠️ Database state differs from expected'))

        # Test 4: URL Routing Check
        self.stdout.write('\n4️⃣ Testing URL routing...')
        try:
            # Test if URLs are accessible
            response = client.get('/api/fetch-enhanced-audio/')
            if response.status_code == 405:  # Method not allowed (expected for GET)
                self.stdout.write(self.style.SUCCESS('   ✅ fetch-enhanced-audio URL is routed correctly'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠️ Unexpected response for fetch-enhanced-audio: {response.status_code}'))

            response = client.get('/api/update-flashcard-audio/')
            if response.status_code == 405:  # Method not allowed (expected for GET)
                self.stdout.write(self.style.SUCCESS('   ✅ update-flashcard-audio URL is routed correctly'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠️ Unexpected response for update-flashcard-audio: {response.status_code}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ URL routing error: {e}'))

        self.stdout.write('\n📊 Test Summary')
        self.stdout.write('=' * 30)
        self.stdout.write('If all tests passed, the backend API is working correctly.')
        self.stdout.write('If the frontend is still not working, check:')
        self.stdout.write('1. CSRF token handling in JavaScript')
        self.stdout.write('2. Network requests in browser dev tools')
        self.stdout.write('3. JavaScript console for errors')
        self.stdout.write('4. Frontend UI update logic')
        
        self.stdout.write(self.style.SUCCESS('\n✅ API testing completed!'))
