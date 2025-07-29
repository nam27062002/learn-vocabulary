#!/usr/bin/env python
"""
Test script to verify current audio preview and UI layout fixes
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

def create_current_audio_test_data():
    """Create test data specifically for current audio preview and UI layout testing"""
    print("🔧 Setting up test data for current audio preview and UI layout fixes...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='current-audio-test@example.com',
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
        name='Current Audio & UI Test Deck',
        user=user
    )
    if created:
        print(f"✅ Created test deck: {deck.name}")
    else:
        print(f"✅ Using existing test deck: {deck.name}")
    
    # Create test flashcards with different audio states for comprehensive testing
    test_words = [
        {
            'word': 'preview',
            'phonetic': '/ˈpriː.vjuː/',
            'part_of_speech': 'verb',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/p/pre/previ/preview.mp3'
        },
        {
            'word': 'current',
            'phonetic': '/ˈkɜːr.ənt/',
            'part_of_speech': 'adjective',
            'audio_url': 'https://dictionary.cambridge.org/media/english/uk_pron/u/ukc/ukcur/ukcurre_028.mp3'
        },
        {
            'word': 'layout',
            'phonetic': '/ˈleɪ.aʊt/',
            'part_of_speech': 'noun',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/l/lay/layou/layout.mp3'
        },
        {
            'word': 'button',
            'phonetic': '/ˈbʌt.ən/',
            'part_of_speech': 'noun',
            'audio_url': ''  # No audio initially to test creation
        },
        {
            'word': 'interface',
            'phonetic': '/ˈɪn.tɚ.feɪs/',
            'part_of_speech': 'noun',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/i/int/inter/interface.mp3'
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
            print(f"✅ Created flashcard: {flashcard.word} (ID: {flashcard.id}) - Audio: {'Yes' if flashcard.audio_url else 'No'}")
        else:
            print(f"✅ Using existing flashcard: {flashcard.word} (ID: {flashcard.id}) - Audio: {'Yes' if flashcard.audio_url else 'No'}")
    
    return user, deck, created_cards

def print_testing_guide():
    """Print comprehensive testing guide for both fixes"""
    print("\n🧪 CURRENT AUDIO PREVIEW & UI LAYOUT FIXES TESTING GUIDE")
    print("=" * 80)
    
    print("\n🎯 ISSUES THAT WERE FIXED:")
    print("-" * 60)
    print("✅ Current audio preview button not working in enhanced audio modal")
    print("✅ Event handlers not bound to current audio section")
    print("✅ Scattered button layout (favorite, enhanced audio, edit)")
    print("✅ Inconsistent button styling and positioning")
    print("✅ Poor mobile responsiveness for button layout")
    
    print("\n📋 TESTING PROCEDURE:")
    print("-" * 60)
    
    print("\n1️⃣ CURRENT AUDIO PREVIEW FIX TEST:")
    print("   • Open the Current Audio & UI Test Deck")
    print("   • Click enhanced audio button (🔍) on 'preview' flashcard")
    print("   • ✅ VERIFY: Modal opens with current audio section at top")
    print("   • ✅ VERIFY: Current audio section shows the existing audio URL")
    print("   • ✅ VERIFY: Current audio preview button is clickable")
    print("   • ✅ VERIFY: Clicking current audio preview button plays audio")
    print("   • ✅ VERIFY: Button changes to 'Playing' state with pause icon")
    print("   • ✅ VERIFY: Audio stops and button resets when audio ends")
    print("   • ✅ VERIFY: Console shows 'Current audio preview clicked: [URL]'")
    
    print("\n2️⃣ UI LAYOUT IMPROVEMENT TEST:")
    print("   • Look at any flashcard in the deck")
    print("   • ✅ VERIFY: Three buttons are grouped in top-right corner:")
    print("     - Enhanced Audio button (🔍) - leftmost")
    print("     - Favorite button (🤍) - middle") 
    print("     - Edit button (✏️) - rightmost")
    print("   • ✅ VERIFY: Buttons are aligned horizontally with consistent spacing")
    print("   • ✅ VERIFY: All buttons have consistent size and styling")
    print("   • ✅ VERIFY: Hover effects work on all buttons")
    print("   • ✅ VERIFY: Word title no longer has favorite button next to it")
    
    print("\n3️⃣ BUTTON FUNCTIONALITY TEST:")
    print("   • Test each button in the top-right group:")
    print("   • ✅ Enhanced Audio button: Opens audio selection modal")
    print("   • ✅ Favorite button: Toggles favorite status (🤍 ↔ ❤️)")
    print("   • ✅ Edit button: Enters edit mode for the card")
    print("   • ✅ VERIFY: All buttons maintain their original functionality")
    
    print("\n4️⃣ RESPONSIVE DESIGN TEST:")
    print("   • Resize browser window to mobile size (< 640px)")
    print("   • ✅ VERIFY: Button group remains visible and usable")
    print("   • ✅ VERIFY: Buttons scale down appropriately on small screens")
    print("   • ✅ VERIFY: No overlap with card content")
    print("   • ✅ VERIFY: Touch targets are adequate for mobile")
    
    print("\n5️⃣ CURRENT AUDIO WITH DIFFERENT STATES TEST:")
    print("   • Test 'current' flashcard (has audio)")
    print("   • Test 'button' flashcard (no audio initially)")
    print("   • ✅ VERIFY: Cards with audio show current audio in modal")
    print("   • ✅ VERIFY: Cards without audio show 'No current audio'")
    print("   • ✅ VERIFY: After updating audio, current audio section updates")
    
    print("\n🔍 BROWSER CONSOLE CHECKS:")
    print("-" * 60)
    print("✅ 'Current audio event listeners bound' message appears")
    print("✅ 'Current audio preview clicked: [URL]' when clicking current audio")
    print("✅ 'Rendering current audio: [URL]' when modal opens")
    print("✅ No 'current audio preview button has no audio URL' warnings")
    print("✅ No JavaScript errors during current audio preview")
    
    print("\n🎯 EXPECTED BEHAVIOR (Now Fixed):")
    print("-" * 60)
    print("• Current audio preview button works in enhanced audio modal")
    print("• Three action buttons are grouped together in top-right corner")
    print("• Consistent button styling and hover effects")
    print("• Responsive design works on all screen sizes")
    print("• All button functionality preserved")
    print("• Clean, organized card layout")
    
    print("\n⚠️ SIGNS OF REMAINING ISSUES:")
    print("-" * 60)
    print("❌ Current audio preview button doesn't respond to clicks")
    print("❌ Buttons are still scattered around the card")
    print("❌ Inconsistent button sizes or styling")
    print("❌ Layout breaks on mobile devices")
    print("❌ Console shows event binding errors")
    print("❌ Button functionality is broken")

def print_debug_commands():
    """Print debug commands for troubleshooting"""
    print("\n🔧 DEBUG COMMANDS (Run in Browser Console):")
    print("-" * 70)
    print("// Check if current audio events are bound:")
    print("if (window.EnhancedAudioManager) {")
    print("  const manager = window.EnhancedAudioManager;")
    print("  console.log('Current audio handler:', manager.currentAudioClickHandler);")
    print("}")
    print("")
    print("// Test current audio section manually:")
    print("const currentAudioBtn = document.querySelector('.current-audio-content .btn-preview');")
    print("if (currentAudioBtn) {")
    print("  console.log('Current audio button found:', currentAudioBtn.dataset.audioUrl);")
    print("} else {")
    print("  console.log('Current audio button not found');")
    print("}")
    print("")
    print("// Check button layout:")
    print("const buttonGroup = document.querySelector('.absolute.top-4.right-4');")
    print("if (buttonGroup) {")
    print("  console.log('Button group found with', buttonGroup.children.length, 'buttons');")
    print("  Array.from(buttonGroup.children).forEach((btn, i) => {")
    print("    console.log(`Button ${i}:`, btn.className);")
    print("  });")
    print("} else {")
    print("  console.log('Button group not found');")
    print("}")
    print("")
    print("// Force rebind current audio events (if needed):")
    print("if (window.EnhancedAudioManager) {")
    print("  window.EnhancedAudioManager.bindCurrentAudioEvents();")
    print("}")

if __name__ == '__main__':
    print("🚀 Current Audio Preview & UI Layout Fixes Test Setup")
    print("=" * 70)
    
    try:
        user, deck, cards = create_current_audio_test_data()
        print_testing_guide()
        print_debug_commands()
        
        print(f"\n🎉 Test setup completed successfully!")
        print(f"📊 Created/verified {len(cards)} test flashcards")
        print(f"👤 Test user: {user.email}")
        print(f"📚 Test deck: {deck.name} (ID: {deck.id})")
        print(f"🔗 Test URL: http://localhost:8000/deck/{deck.id}/")
        
        print("\n🚀 Ready for comprehensive testing!")
        print("Start the development server and follow the testing guide above.")
        print("\nKey things to verify:")
        print("1. Current audio preview button works in enhanced audio modal")
        print("2. Three action buttons are grouped in top-right corner")
        print("3. Responsive design works on all screen sizes")
        print("4. All button functionality is preserved")
        
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        import traceback
        traceback.print_exc()
