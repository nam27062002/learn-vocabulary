#!/usr/bin/env python
"""
Debug script to test enhanced audio fetching database updates
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, Deck
import json

User = get_user_model()

def test_database_update():
    """Test the database update functionality"""
    print("🔍 Testing Enhanced Audio Database Update")
    print("=" * 50)
    
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={'is_active': True}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created test user: {user.email}")
        else:
            print(f"✅ Using existing test user: {user.email}")
        
        # Get or create a test deck
        deck, created = Deck.objects.get_or_create(
            name='Enhanced Audio Test Deck',
            user=user
        )
        if created:
            print(f"✅ Created test deck: {deck.name}")
        else:
            print(f"✅ Using existing test deck: {deck.name}")
        
        # Get or create a test flashcard
        flashcard, created = Flashcard.objects.get_or_create(
            word='example',
            user=user,
            deck=deck,
            defaults={
                'phonetic': '/ɪɡˈzæm.pəl/',
                'part_of_speech': 'noun',
                'audio_url': 'https://old-audio-url.mp3'
            }
        )
        if created:
            print(f"✅ Created test flashcard: {flashcard.word}")
        else:
            print(f"✅ Using existing test flashcard: {flashcard.word}")
        
        print(f"\n📋 Initial flashcard state:")
        print(f"   ID: {flashcard.id}")
        print(f"   Word: {flashcard.word}")
        print(f"   Current audio URL: {flashcard.audio_url}")
        
        # Test database update
        new_audio_url = 'https://new-enhanced-audio-url.mp3'
        print(f"\n🔄 Updating audio URL to: {new_audio_url}")
        
        # Simulate the API update process
        old_audio_url = flashcard.audio_url
        flashcard.audio_url = new_audio_url
        flashcard.save(update_fields=['audio_url'])
        
        # Verify the update
        flashcard.refresh_from_db()
        
        print(f"\n✅ Database update results:")
        print(f"   Old URL: {old_audio_url}")
        print(f"   New URL: {flashcard.audio_url}")
        print(f"   Update successful: {flashcard.audio_url == new_audio_url}")
        
        if flashcard.audio_url == new_audio_url:
            print("🎉 Database update is working correctly!")
        else:
            print("❌ Database update failed!")
            
        # Test API endpoint simulation
        print(f"\n🧪 Testing API endpoint logic...")
        
        # Simulate API request data
        api_data = {
            'card_id': flashcard.id,
            'audio_url': 'https://api-test-audio-url.mp3'
        }
        
        print(f"   Simulating API request: {api_data}")
        
        # Simulate the API logic
        card = Flashcard.objects.get(id=api_data['card_id'], user=user)
        old_url = card.audio_url
        card.audio_url = api_data['audio_url']
        card.save(update_fields=['audio_url'])
        card.refresh_from_db()
        
        print(f"   API simulation results:")
        print(f"     Old URL: {old_url}")
        print(f"     New URL: {card.audio_url}")
        print(f"     API update successful: {card.audio_url == api_data['audio_url']}")
        
        if card.audio_url == api_data['audio_url']:
            print("🎉 API endpoint logic is working correctly!")
            return True
        else:
            print("❌ API endpoint logic failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flashcard_query():
    """Test flashcard querying"""
    print("\n🔍 Testing Flashcard Query")
    print("=" * 30)
    
    try:
        # Get test user
        user = User.objects.get(email='test@example.com')
        print(f"✅ Found user: {user.email}")
        
        # Query flashcards
        flashcards = Flashcard.objects.filter(user=user)
        print(f"✅ Found {flashcards.count()} flashcards for user")
        
        for card in flashcards[:5]:  # Show first 5
            print(f"   - {card.word} (ID: {card.id}) - Audio: {card.audio_url}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error querying flashcards: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Enhanced Audio Debug Script")
    print("=" * 50)
    
    # Run tests
    db_test_passed = test_database_update()
    query_test_passed = test_flashcard_query()
    
    print("\n📊 Test Results Summary")
    print("=" * 30)
    print(f"Database Update Test: {'✅ PASSED' if db_test_passed else '❌ FAILED'}")
    print(f"Flashcard Query Test: {'✅ PASSED' if query_test_passed else '❌ FAILED'}")
    
    if db_test_passed and query_test_passed:
        print("\n🎉 All tests passed! The database functionality is working correctly.")
        print("\nIf the frontend is still not working, the issue is likely in:")
        print("1. JavaScript API call")
        print("2. CSRF token handling")
        print("3. URL routing")
        print("4. Frontend UI update logic")
    else:
        print("\n❌ Some tests failed. Check the database configuration and models.")
