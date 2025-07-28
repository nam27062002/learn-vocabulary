#!/usr/bin/env python3
"""
Debug script to test the IncorrectWordReview model and API endpoints.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, IncorrectWordReview

User = get_user_model()  # This will get the CustomUser model

def test_incorrect_word_creation():
    """Test creating IncorrectWordReview records manually."""
    print("=" * 60)
    print("TESTING INCORRECT WORD REVIEW CREATION")
    print("=" * 60)
    
    # Get or create a test user
    try:
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("❌ No active users found in database")
            return False
        print(f"✅ Using user: {user.email} (ID: {user.id})")
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return False
    
    # Get a flashcard for this user
    try:
        flashcard = Flashcard.objects.filter(user=user).first()
        if not flashcard:
            print("❌ No flashcards found for this user")
            return False
        print(f"✅ Using flashcard: {flashcard.word} (ID: {flashcard.id})")
    except Exception as e:
        print(f"❌ Error getting flashcard: {e}")
        return False
    
    # Test creating an IncorrectWordReview record
    try:
        # Clean up any existing records for this test
        IncorrectWordReview.objects.filter(
            user=user,
            flashcard=flashcard,
            question_type='type'
        ).delete()
        
        # Create a new record
        incorrect_review, created = IncorrectWordReview.objects.get_or_create(
            user=user,
            flashcard=flashcard,
            question_type='type',
            defaults={'error_count': 1}
        )
        
        print(f"✅ IncorrectWordReview created: {created}")
        print(f"   Record ID: {incorrect_review.id}")
        print(f"   User: {incorrect_review.user.email}")
        print(f"   Flashcard: {incorrect_review.flashcard.word}")
        print(f"   Question Type: {incorrect_review.question_type}")
        print(f"   Error Count: {incorrect_review.error_count}")
        print(f"   Is Resolved: {incorrect_review.is_resolved}")
        
        # Test the count query
        total_count = IncorrectWordReview.objects.filter(
            user=user,
            is_resolved=False
        ).count()
        print(f"✅ Total unresolved incorrect words for user: {total_count}")
        
        # Test the grouped count query (same as in the API)
        from django.db.models import Count
        incorrect_words = IncorrectWordReview.objects.filter(
            user=user,
            is_resolved=False
        ).values('question_type').annotate(count=Count('id'))
        
        print(f"✅ Grouped count query result: {list(incorrect_words)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating IncorrectWordReview: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_api_endpoint():
    """Test the API endpoint directly."""
    print("\n" + "=" * 60)
    print("TESTING API ENDPOINT")
    print("=" * 60)
    
    try:
        from django.test import Client
        # User model already imported at top
        
        # Get a user
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("❌ No active users found")
            return False
        
        # Create a test client and login
        client = Client()
        client.force_login(user)
        
        # Test the API endpoint
        response = client.get('/api/incorrect-words/count/')
        print(f"✅ API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response Data: {data}")
            return True
        else:
            print(f"❌ API Error: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all tests."""
    print("DEBUGGING INCORRECT WORDS TRACKING SYSTEM")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Manual record creation
    if test_incorrect_word_creation():
        success_count += 1
    
    # Test 2: API endpoint
    if test_api_endpoint():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {success_count}/{total_tests} tests passed")
    print("=" * 60)
    
    if success_count == total_tests:
        print("🎉 All tests passed! The system should be working.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return success_count == total_tests

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
