#!/usr/bin/env python
"""
Test script to verify deck navigation functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, Deck

User = get_user_model()

def create_deck_navigation_test_data():
    """Create test data specifically for deck navigation testing"""
    print("🔧 Setting up test data for deck navigation functionality...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='deck-navigation-test@example.com',
        defaults={'is_active': True}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"✅ Using existing test user: {user.email}")
    
    # Create multiple test decks for navigation testing
    test_decks = [
        {
            'name': 'First Navigation Deck',
            'words': ['first', 'beginning', 'start', 'initial']
        },
        {
            'name': 'Second Navigation Deck', 
            'words': ['second', 'middle', 'between', 'intermediate']
        },
        {
            'name': 'Third Navigation Deck',
            'words': ['third', 'final', 'end', 'last']
        },
        {
            'name': 'Fourth Navigation Deck',
            'words': ['fourth', 'extra', 'additional', 'bonus']
        },
        {
            'name': 'Fifth Navigation Deck',
            'words': ['fifth', 'ultimate', 'complete', 'finished']
        }
    ]
    
    created_decks = []
    for deck_data in test_decks:
        deck, created = Deck.objects.get_or_create(
            name=deck_data['name'],
            user=user
        )
        created_decks.append(deck)
        
        if created:
            print(f"✅ Created deck: {deck.name} (ID: {deck.id})")
            
            # Add flashcards to each deck
            for word in deck_data['words']:
                flashcard, card_created = Flashcard.objects.get_or_create(
                    word=word,
                    user=user,
                    deck=deck,
                    defaults={
                        'phonetic': f'/test-{word}/',
                        'part_of_speech': 'noun',
                        'audio_url': f'https://test-audio-{word}.mp3'
                    }
                )
                if card_created:
                    print(f"  ✅ Added flashcard: {word}")
        else:
            print(f"✅ Using existing deck: {deck.name} (ID: {deck.id})")
    
    return user, created_decks

def print_navigation_testing_guide():
    """Print comprehensive testing guide for deck navigation"""
    print("\n🧪 DECK NAVIGATION FUNCTIONALITY TESTING GUIDE")
    print("=" * 80)
    
    print("\n🎯 FEATURES IMPLEMENTED:")
    print("-" * 60)
    print("✅ Previous/Next deck navigation buttons")
    print("✅ Deck position indicator (X / Y)")
    print("✅ Keyboard shortcuts (Ctrl+← / Ctrl+→)")
    print("✅ Responsive design for mobile devices")
    print("✅ Edge case handling (first/last deck)")
    print("✅ User-specific deck filtering")
    print("✅ Preserved existing functionality")
    
    print("\n📋 TESTING PROCEDURE:")
    print("-" * 60)
    
    print("\n1️⃣ BASIC NAVIGATION TEST:")
    print("   • Open any deck from the navigation test decks")
    print("   • ✅ VERIFY: Navigation controls appear in top-right header")
    print("   • ✅ VERIFY: Position indicator shows correct deck number (e.g., '2 / 5')")
    print("   • ✅ VERIFY: Previous button (←) and Next button (→) are visible")
    print("   • ✅ VERIFY: Buttons have hover effects and tooltips")
    
    print("\n2️⃣ FORWARD NAVIGATION TEST:")
    print("   • Start with 'First Navigation Deck'")
    print("   • ✅ VERIFY: Previous button is disabled (grayed out)")
    print("   • ✅ VERIFY: Next button is enabled and clickable")
    print("   • Click Next button")
    print("   • ✅ VERIFY: Navigates to 'Second Navigation Deck'")
    print("   • ✅ VERIFY: URL changes to correct deck ID")
    print("   • ✅ VERIFY: Position indicator updates (2 / 5)")
    
    print("\n3️⃣ BACKWARD NAVIGATION TEST:")
    print("   • From 'Second Navigation Deck', click Previous button")
    print("   • ✅ VERIFY: Navigates back to 'First Navigation Deck'")
    print("   • ✅ VERIFY: Position indicator shows (1 / 5)")
    print("   • ✅ VERIFY: Previous button becomes disabled again")
    
    print("\n4️⃣ EDGE CASES TEST:")
    print("   • Navigate to 'Fifth Navigation Deck' (last deck)")
    print("   • ✅ VERIFY: Next button is disabled (grayed out)")
    print("   • ✅ VERIFY: Previous button is enabled")
    print("   • ✅ VERIFY: Position indicator shows (5 / 5)")
    
    print("\n5️⃣ KEYBOARD SHORTCUTS TEST:")
    print("   • Go to any middle deck (e.g., 'Third Navigation Deck')")
    print("   • Press Ctrl+← (or Cmd+← on Mac)")
    print("   • ✅ VERIFY: Navigates to previous deck")
    print("   • Press Ctrl+→ (or Cmd+→ on Mac)")
    print("   • ✅ VERIFY: Navigates to next deck")
    print("   • ✅ VERIFY: Keyboard shortcuts don't work when editing deck name")
    
    print("\n6️⃣ RESPONSIVE DESIGN TEST:")
    print("   • Resize browser to mobile size (< 640px)")
    print("   • ✅ VERIFY: Navigation controls remain visible and usable")
    print("   • ✅ VERIFY: Buttons scale appropriately")
    print("   • ✅ VERIFY: Layout stacks vertically on very small screens")
    print("   • ✅ VERIFY: Touch targets are adequate for mobile")
    
    print("\n7️⃣ FUNCTIONALITY PRESERVATION TEST:")
    print("   • ✅ VERIFY: Flashcard carousel still works within each deck")
    print("   • ✅ VERIFY: Enhanced audio selection still works")
    print("   • ✅ VERIFY: Card editing functionality preserved")
    print("   • ✅ VERIFY: Favorite button functionality preserved")
    print("   • ✅ VERIFY: Deck name editing still works")
    
    print("\n8️⃣ SINGLE DECK USER TEST:")
    print("   • Create a user with only one deck")
    print("   • ✅ VERIFY: Navigation controls are hidden (has_navigation = False)")
    print("   • ✅ VERIFY: Only 'Back to all decks' link is shown")
    
    print("\n🔍 BROWSER CONSOLE CHECKS:")
    print("-" * 60)
    print("✅ 'Deck navigation initialized' message appears")
    print("✅ No JavaScript errors during navigation")
    print("✅ Keyboard event handlers work correctly")
    print("✅ Hover effects apply smoothly")
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("-" * 60)
    print("• Navigation controls appear only for users with multiple decks")
    print("• Previous/Next buttons work correctly with proper state management")
    print("• Position indicator shows accurate deck position")
    print("• Keyboard shortcuts provide quick navigation")
    print("• Responsive design works on all screen sizes")
    print("• All existing functionality is preserved")
    print("• Edge cases (first/last deck) are handled gracefully")
    
    print("\n⚠️ SIGNS OF ISSUES:")
    print("-" * 60)
    print("❌ Navigation buttons don't appear")
    print("❌ Clicking buttons doesn't navigate to correct deck")
    print("❌ Position indicator shows wrong numbers")
    print("❌ Keyboard shortcuts don't work")
    print("❌ Layout breaks on mobile devices")
    print("❌ Existing functionality is broken")
    print("❌ Console shows JavaScript errors")

def print_test_urls(decks):
    """Print test URLs for manual testing"""
    print("\n🔗 TEST URLS FOR MANUAL TESTING:")
    print("-" * 50)
    
    for i, deck in enumerate(decks, 1):
        print(f"{i}. {deck.name}: http://localhost:8000/deck/{deck.id}/")
    
    print(f"\n📄 Deck List: http://localhost:8000/decks/")
    print("\n💡 TIP: Open browser dev tools to monitor console logs and network requests")

def print_debug_commands():
    """Print debug commands for troubleshooting"""
    print("\n🔧 DEBUG COMMANDS (Run in Browser Console):")
    print("-" * 70)
    print("// Check navigation elements:")
    print("console.log('Navigation elements:', {")
    print("  prevBtn: document.querySelector('.deck-nav-prev'),")
    print("  nextBtn: document.querySelector('.deck-nav-next'),")
    print("  position: document.querySelector('.deck-position')?.textContent,")
    print("  hasNavigation: document.querySelector('.deck-navigation') !== null")
    print("});")
    print("")
    print("// Test keyboard navigation manually:")
    print("document.dispatchEvent(new KeyboardEvent('keydown', {")
    print("  key: 'ArrowLeft',")
    print("  ctrlKey: true")
    print("}));")
    print("")
    print("// Check responsive design:")
    print("console.log('Window width:', window.innerWidth);")
    print("console.log('Navigation visible:', ")
    print("  getComputedStyle(document.querySelector('.deck-navigation')).display);")

if __name__ == '__main__':
    print("🚀 Deck Navigation Functionality Test Setup")
    print("=" * 70)
    
    try:
        user, decks = create_deck_navigation_test_data()
        print_navigation_testing_guide()
        print_test_urls(decks)
        print_debug_commands()
        
        print(f"\n🎉 Test setup completed successfully!")
        print(f"📊 Created/verified {len(decks)} test decks")
        print(f"👤 Test user: {user.email}")
        print(f"🔗 Start testing at: http://localhost:8000/deck/{decks[0].id}/")
        
        print("\n🚀 Ready for deck navigation testing!")
        print("Start the development server and follow the testing guide above.")
        print("\nKey things to verify:")
        print("1. Navigation controls appear in deck detail header")
        print("2. Previous/Next buttons work correctly")
        print("3. Keyboard shortcuts (Ctrl+←/→) function properly")
        print("4. Responsive design works on mobile")
        print("5. All existing functionality is preserved")
        
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        import traceback
        traceback.print_exc()
