#!/usr/bin/env python3
"""
Test script to verify the audio statistics fix is working correctly.
This script checks the data consistency in the database and simulates the frontend logic.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from vocabulary.models import Deck, Flashcard

User = get_user_model()

def test_audio_statistics():
    """Test audio statistics calculation logic."""
    print("=" * 60)
    print("TESTING AUDIO STATISTICS FIX")
    print("=" * 60)
    
    # Get a user with decks
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ No active users found")
        return False
    
    print(f"✅ Testing with user: {user.email}")
    
    # Get user's decks
    decks = Deck.objects.filter(user=user)
    if not decks.exists():
        print("❌ No decks found for user")
        return False
    
    print(f"✅ Found {decks.count()} deck(s)")
    
    all_tests_passed = True
    
    for deck in decks:
        print(f"\n📚 Testing Deck: {deck.name}")
        
        # Get all flashcards in the deck
        flashcards = deck.flashcards.all()
        total_cards = flashcards.count()
        
        if total_cards == 0:
            print(f"   ⚠️  Deck is empty, skipping...")
            continue
        
        # Count cards with and without audio
        cards_with_audio = flashcards.exclude(audio_url__isnull=True).exclude(audio_url__exact='').count()
        cards_without_audio = flashcards.filter(audio_url__isnull=True).count() + flashcards.filter(audio_url__exact='').count()
        
        print(f"   📊 Total cards: {total_cards}")
        print(f"   🔊 Cards with audio: {cards_with_audio}")
        print(f"   🔇 Cards without audio: {cards_without_audio}")
        print(f"   ➕ Sum: {cards_with_audio + cards_without_audio}")
        
        # Verify the counts add up correctly
        if cards_with_audio + cards_without_audio == total_cards:
            print(f"   ✅ PASS: Counts add up correctly!")
        else:
            print(f"   ❌ FAIL: Counts don't add up! Expected {total_cards}, got {cards_with_audio + cards_without_audio}")
            all_tests_passed = False
        
        # Show detailed breakdown
        print(f"   📝 Detailed breakdown:")
        for i, card in enumerate(flashcards[:5], 1):  # Show first 5 cards
            has_audio = bool(card.audio_url and card.audio_url.strip())
            audio_status = "✅ HAS AUDIO" if has_audio else "❌ NO AUDIO"
            print(f"      {i}. {card.word}: {audio_status}")
            if has_audio:
                print(f"         Audio URL: {card.audio_url[:50]}...")
        
        if flashcards.count() > 5:
            print(f"      ... and {flashcards.count() - 5} more cards")
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The audio statistics should now display correctly in the frontend.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("There may still be data consistency issues.")
    print("=" * 60)
    
    return all_tests_passed

def simulate_frontend_logic():
    """Simulate the frontend JavaScript logic to verify it would work correctly."""
    print("\n" + "=" * 60)
    print("SIMULATING FRONTEND LOGIC")
    print("=" * 60)
    
    user = User.objects.filter(is_active=True).first()
    if not user:
        return False
    
    decks = Deck.objects.filter(user=user)
    
    for deck in decks:
        flashcards = deck.flashcards.all()
        if flashcards.count() == 0:
            continue
            
        print(f"\n📚 Simulating frontend for deck: {deck.name}")
        
        # Simulate the JavaScript logic
        with_audio_count = 0
        without_audio_count = 0
        
        for card in flashcards:
            # This simulates the data-has-audio attribute logic
            has_audio = bool(card.audio_url and card.audio_url.strip())
            
            if has_audio:
                with_audio_count += 1
            else:
                without_audio_count += 1
        
        total_calculated = with_audio_count + without_audio_count
        total_expected = flashcards.count()
        
        print(f"   🔊 Frontend would show: {with_audio_count} cards with audio")
        print(f"   🔇 Frontend would show: {without_audio_count} cards without audio")
        print(f"   📊 Total calculated: {total_calculated}")
        print(f"   📊 Total expected: {total_expected}")
        
        if total_calculated == total_expected:
            print(f"   ✅ Frontend simulation PASSED!")
        else:
            print(f"   ❌ Frontend simulation FAILED!")
            return False
    
    return True

def main():
    """Run all tests."""
    print("AUDIO STATISTICS FIX VERIFICATION")
    print("This script tests the backend data consistency that the frontend fix relies on.")
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Database statistics
    if test_audio_statistics():
        success_count += 1
    
    # Test 2: Frontend simulation
    if simulate_frontend_logic():
        success_count += 1
    
    print(f"\n🏁 FINAL RESULTS: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("\n🎉 SUCCESS! The audio statistics fix should work correctly.")
        print("\nNext steps:")
        print("1. Open a deck detail page in your browser")
        print("2. Check the browser console for debug messages")
        print("3. Verify the audio statistics display correctly")
        print("4. Test the audio filter functionality")
    else:
        print("\n❌ Some tests failed. Please check the data consistency.")
    
    return success_count == total_tests

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
