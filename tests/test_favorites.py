#!/usr/bin/env python
"""
Quick script to add some test favorites for debugging the favorites study mode.
Run this script to add a few flashcards to favorites for testing.
"""

import os
import django


# Add the parent directory to Python path so we can import Django modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, FavoriteFlashcard

User = get_user_model()

def add_test_favorites():
    """Add some test favorites for the first user."""
    try:
        # Get the first user
        user = User.objects.first()
        if not user:
            print("❌ No users found. Please create a user first.")
            return
        
        print(f"👤 Adding favorites for user: {user.email}")
        
        # Get some flashcards
        flashcards = Flashcard.objects.filter(user=user)[:5]  # Get first 5 flashcards
        
        if not flashcards:
            print("❌ No flashcards found. Please create some flashcards first.")
            return
        
        print(f"📚 Found {flashcards.count()} flashcards")
        
        # Add them to favorites
        favorites_added = 0
        for flashcard in flashcards:
            favorite, created = FavoriteFlashcard.objects.get_or_create(
                user=user,
                flashcard=flashcard
            )
            if created:
                favorites_added += 1
                print(f"❤️ Added '{flashcard.word}' to favorites")
            else:
                print(f"💙 '{flashcard.word}' already in favorites")
        
        total_favorites = FavoriteFlashcard.objects.filter(user=user).count()
        print(f"\n✅ Success! User now has {total_favorites} favorite words")
        print(f"🆕 Added {favorites_added} new favorites")
        
        # List all favorites
        print("\n📋 Current favorites:")
        for i, fav in enumerate(FavoriteFlashcard.objects.filter(user=user), 1):
            print(f"  {i}. {fav.flashcard.word}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_test_favorites()
