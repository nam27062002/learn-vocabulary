#!/usr/bin/env python
"""
Test script to verify the enhanced audio second-use fixes
"""
import os
import sys
import django


# Add the parent directory to Python path so we can import Django modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, Deck

User = get_user_model()

def create_test_scenario():
    """Create test scenario for second-use testing"""
    print("🔧 Setting up test scenario for second-use fixes...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='second-use-test@example.com',
        defaults={'is_active': True}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"✅ Using existing test user: {user.email}")
    
    # Get or create test deck
    deck, created = Deck.objects.get_or_create(
        name='Second Use Test Deck',
        user=user
    )
    if created:
        print(f"✅ Created test deck: {deck.name}")
    else:
        print(f"✅ Using existing test deck: {deck.name}")
    
    # Create multiple test flashcards for testing
    test_words = [
        {
            'word': 'first',
            'phonetic': '/fɜːrst/',
            'part_of_speech': 'adjective',
            'audio_url': 'https://old-audio-first.mp3'
        },
        {
            'word': 'second',
            'phonetic': '/ˈsek.ənd/',
            'part_of_speech': 'adjective',
            'audio_url': 'https://old-audio-second.mp3'
        },
        {
            'word': 'third',
            'phonetic': '/θɜːrd/',
            'part_of_speech': 'adjective',
            'audio_url': ''  # No audio initially
        },
        {
            'word': 'multiple',
            'phonetic': '/ˈmʌl.tɪ.pəl/',
            'part_of_speech': 'adjective',
            'audio_url': 'https://old-audio-multiple.mp3'
        }
    ]
    
    created_cards = []
    for word_data in test_words:
        flashcard, created = Flashcard.objects.get_or_create(
            word=word_data['word'],
            user=user,
            deck=deck,
            defaults=word_data
        )
        created_cards.append(flashcard)
        
        if created:
            print(f"✅ Created flashcard: {flashcard.word} (ID: {flashcard.id})")
        else:
            print(f"✅ Using existing flashcard: {flashcard.word} (ID: {flashcard.id})")
    
    return user, deck, created_cards

def print_testing_guide():
    """Print comprehensive testing guide for second-use fixes"""
    print("\n🧪 SECOND-USE FIXES TESTING GUIDE")
    print("=" * 60)
    
    print("\n🎯 ISSUES THAT WERE FIXED:")
    print("-" * 40)
    print("✅ Modal state not being properly reset between uses")
    print("✅ Audio playback conflicts and AbortError issues")
    print("✅ Event listener duplication and memory leaks")
    print("✅ Missing updateAudioStats function reference")
    print("✅ Card container not found errors")
    print("✅ Improved error handling and validation")
    
    print("\n📋 TESTING PROCEDURE:")
    print("-" * 40)
    print("1️⃣ FIRST USE TEST:")
    print("   • Open the Second Use Test Deck")
    print("   • Click enhanced audio button (🔍) on 'first' flashcard")
    print("   • Select an audio option and confirm")
    print("   • Verify success notification appears")
    print("   • Verify modal closes properly")
    
    print("\n2️⃣ SECOND USE TEST (Critical):")
    print("   • WITHOUT refreshing the page")
    print("   • Click enhanced audio button (🔍) on 'second' flashcard")
    print("   • Verify modal opens without errors")
    print("   • Verify audio options load correctly")
    print("   • Test audio preview functionality")
    print("   • Select different audio option and confirm")
    print("   • Verify success notification appears")
    
    print("\n3️⃣ MULTIPLE USE TEST:")
    print("   • Continue testing on 'third' and 'multiple' flashcards")
    print("   • Test rapid opening/closing of modal")
    print("   • Test audio preview on multiple options")
    print("   • Verify no console errors appear")
    
    print("\n4️⃣ AUDIO CONFLICT TEST:")
    print("   • Open modal and start audio preview")
    print("   • Immediately click another preview button")
    print("   • Verify no AbortError in console")
    print("   • Verify only one audio plays at a time")
    
    print("\n5️⃣ ERROR HANDLING TEST:")
    print("   • Try clicking 'Confirm Selection' without selecting option")
    print("   • Verify error notification appears")
    print("   • Test with network disconnected")
    print("   • Verify appropriate error messages")
    
    print("\n🔍 WHAT TO CHECK IN BROWSER CONSOLE:")
    print("-" * 40)
    print("✅ No 'Card container not found for cardId: null' errors")
    print("✅ No 'updateAudioStats function not available' warnings")
    print("✅ No 'AbortError: The play() request was interrupted' errors")
    print("✅ Proper state cleanup messages appear")
    print("✅ Event listener cleanup messages appear")
    print("✅ Audio cleanup completion messages appear")
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("-" * 40)
    print("• Modal opens smoothly on second and subsequent uses")
    print("• Audio previews work without conflicts")
    print("• State is properly reset between modal uses")
    print("• No memory leaks or duplicate event listeners")
    print("• Success/error notifications work consistently")
    print("• UI updates work on all uses")
    
    print("\n⚠️ SIGNS OF REMAINING ISSUES:")
    print("-" * 40)
    print("❌ Modal doesn't open on second use")
    print("❌ Audio preview buttons don't work")
    print("❌ Console shows JavaScript errors")
    print("❌ Success notifications don't appear")
    print("❌ UI doesn't update after audio selection")
    print("❌ Multiple audio streams playing simultaneously")

def print_debug_commands():
    """Print debug commands for troubleshooting"""
    print("\n🔧 DEBUG COMMANDS (Run in Browser Console):")
    print("-" * 50)
    print("// Check if Enhanced Audio Manager is initialized:")
    print("console.log('Enhanced Audio Manager:', window.EnhancedAudioManager);")
    print("")
    print("// Check current modal state:")
    print("console.log('Modal state:', {")
    print("  currentCardId: window.EnhancedAudioManager?.currentCardId,")
    print("  currentWord: window.EnhancedAudioManager?.currentWord,")
    print("  selectedAudioUrl: window.EnhancedAudioManager?.selectedAudioUrl,")
    print("  audioOptions: window.EnhancedAudioManager?.audioOptions?.length")
    print("});")
    print("")
    print("// Check for available functions:")
    print("console.log('Available functions:', {")
    print("  updateCardDisplayForAudio: typeof window.updateCardDisplayForAudio,")
    print("  updateAudioStats: typeof window.updateAudioStats,")
    print("  showMessage: typeof window.showMessage")
    print("});")
    print("")
    print("// Force cleanup (if needed):")
    print("if (window.EnhancedAudioManager) {")
    print("  window.EnhancedAudioManager.closeModal();")
    print("}")

if __name__ == '__main__':
    print("🚀 Enhanced Audio Second-Use Fixes Test Setup")
    print("=" * 60)
    
    try:
        user, deck, cards = create_test_scenario()
        print_testing_guide()
        print_debug_commands()
        
        print(f"\n🎉 Test setup completed successfully!")
        print(f"📊 Created/verified {len(cards)} test flashcards")
        print(f"👤 Test user: {user.email}")
        print(f"📚 Test deck: {deck.name} (ID: {deck.id})")
        print(f"🔗 Test URL: http://localhost:8000/deck/{deck.id}/")
        
        print("\n🚀 Ready for second-use testing!")
        print("Start the development server and follow the testing guide above.")
        
    except Exception as e:
        print(f"❌ Error setting up test scenario: {e}")
        import traceback
        traceback.print_exc()
