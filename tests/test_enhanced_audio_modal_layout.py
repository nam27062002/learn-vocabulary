#!/usr/bin/env python
"""
Test script to verify enhanced audio modal layout fixes
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

def create_modal_test_data():
    """Create test data for modal layout testing"""
    print("🔧 Setting up test data for enhanced audio modal layout testing...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='modal-layout-test@example.com',
        defaults={'is_active': True}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"✅ Using existing test user: {user.email}")
    
    # Create test deck
    deck, created = Deck.objects.get_or_create(
        name='Enhanced Audio Modal Test Deck',
        user=user
    )
    if created:
        print(f"✅ Created test deck: {deck.name}")
    else:
        print(f"✅ Using existing test deck: {deck.name}")
    
    # Create test flashcards with various word lengths to test modal layout
    test_words = [
        {
            'word': 'test',
            'phonetic': '/test/',
            'part_of_speech': 'noun',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/t/tes/test_/test.mp3'
        },
        {
            'word': 'pronunciation',
            'phonetic': '/prəˌnʌn.siˈeɪ.ʃən/',
            'part_of_speech': 'noun',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/p/pro/pronu/pronunciation.mp3'
        },
        {
            'word': 'internationalization',
            'phonetic': '/ˌɪn.tɚˌnæʃ.ən.əl.əˈzeɪ.ʃən/',
            'part_of_speech': 'noun',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/i/int/inter/internationalization.mp3'
        },
        {
            'word': 'modal',
            'phonetic': '/ˈmoʊ.dəl/',
            'part_of_speech': 'adjective',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/m/mod/modal/modal.mp3'
        },
        {
            'word': 'layout',
            'phonetic': '/ˈleɪ.aʊt/',
            'part_of_speech': 'noun',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/l/lay/layou/layout.mp3'
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

def check_css_improvements():
    """Check that the CSS improvements have been applied"""
    print("\n🧪 Checking CSS improvements...")
    
    css_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'css', 'enhanced-audio-modal.css'
    )
    
    if not os.path.exists(css_path):
        print(f"❌ CSS file not found: {css_path}")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key improvements
    improvements = {
        'flexbox_layout': 'display: flex' in content and 'flex-direction: column' in content,
        'improved_modal_size': 'max-width: 700px' in content,
        'flex_body': 'flex: 1' in content,
        'overflow_handling': 'overflow-y: auto' in content and 'overflow-x: hidden' in content,
        'button_improvements': 'min-width: 120px' in content,
        'responsive_mobile': 'width: 98%' in content,
        'content_containment': 'max-height: 300px' in content,
        'title_overflow': 'text-overflow: ellipsis' in content,
        'flex_shrink': 'flex-shrink: 0' in content
    }
    
    print("📋 CSS improvements verification:")
    print("-" * 50)
    
    for improvement, found in improvements.items():
        status = "✅ PASS" if found else "❌ FAIL"
        print(f"{improvement}: {status}")
    
    all_improvements = all(improvements.values())
    
    if all_improvements:
        print("\n✅ All CSS improvements have been applied!")
    else:
        print("\n❌ Some CSS improvements are missing!")
    
    return all_improvements

def print_modal_testing_guide():
    """Print comprehensive testing guide for modal layout"""
    print("\n🧪 ENHANCED AUDIO MODAL LAYOUT TESTING GUIDE")
    print("=" * 70)
    
    print("\n🎯 LAYOUT ISSUES FIXED:")
    print("-" * 40)
    print("✅ Button overflow outside popup container")
    print("✅ Modal sizing for different content lengths")
    print("✅ Responsive design for all screen sizes")
    print("✅ Button layout and alignment")
    print("✅ Content containment and scrolling")
    
    print("\n📋 TESTING PROCEDURE:")
    print("-" * 40)
    
    print("\n1️⃣ DESKTOP LAYOUT TEST (> 1024px):")
    print("   • Navigate to: http://localhost:8000/deck/[deck_id]/")
    print("   • Click enhanced audio button (🔍) on any flashcard")
    print("   • ✅ VERIFY: Modal opens with proper size (max 700px width)")
    print("   • ✅ VERIFY: All buttons stay within modal boundaries")
    print("   • ✅ VERIFY: Footer buttons are properly aligned")
    print("   • ✅ VERIFY: Content scrolls if needed without overflow")
    print("   • ✅ VERIFY: Modal title doesn't overflow with long words")
    
    print("\n2️⃣ TABLET LAYOUT TEST (641px - 1024px):")
    print("   • Resize browser to tablet size")
    print("   • Open enhanced audio modal")
    print("   • ✅ VERIFY: Modal width adjusts to 90% of screen")
    print("   • ✅ VERIFY: Buttons remain properly sized")
    print("   • ✅ VERIFY: Content is fully contained")
    print("   • ✅ VERIFY: Footer buttons stay in horizontal layout")
    
    print("\n3️⃣ MOBILE LAYOUT TEST (≤ 640px):")
    print("   • Resize browser to mobile size")
    print("   • Open enhanced audio modal")
    print("   • ✅ VERIFY: Modal takes 98% of screen width")
    print("   • ✅ VERIFY: Footer buttons stack vertically")
    print("   • ✅ VERIFY: All buttons are full width on mobile")
    print("   • ✅ VERIFY: Audio controls stack vertically")
    print("   • ✅ VERIFY: Touch targets are adequate (44px+)")
    
    print("\n4️⃣ SMALL MOBILE TEST (≤ 480px):")
    print("   • Resize to very small mobile size")
    print("   • Open enhanced audio modal")
    print("   • ✅ VERIFY: Modal takes full screen (100% width/height)")
    print("   • ✅ VERIFY: No border radius on very small screens")
    print("   • ✅ VERIFY: All content is accessible")
    print("   • ✅ VERIFY: Buttons are properly sized for touch")
    
    print("\n5️⃣ CONTENT OVERFLOW TEST:")
    print("   • Test with 'internationalization' flashcard (long word)")
    print("   • ✅ VERIFY: Modal title handles long words gracefully")
    print("   • ✅ VERIFY: Audio options list scrolls if many options")
    print("   • ✅ VERIFY: No horizontal scrolling occurs")
    print("   • ✅ VERIFY: All buttons remain visible and clickable")
    
    print("\n6️⃣ BUTTON FUNCTIONALITY TEST:")
    print("   • Test all buttons in the modal")
    print("   • ✅ VERIFY: Preview buttons work correctly")
    print("   • ✅ VERIFY: Cancel button closes modal")
    print("   • ✅ VERIFY: Keep Current button works")
    print("   • ✅ VERIFY: Confirm Selection button works")
    print("   • ✅ VERIFY: Close button (×) works")
    
    print("\n7️⃣ RESPONSIVE BEHAVIOR TEST:")
    print("   • Open modal and resize browser window")
    print("   • ✅ VERIFY: Modal adapts to new screen size")
    print("   • ✅ VERIFY: Layout changes smoothly")
    print("   • ✅ VERIFY: No content is cut off during resize")
    print("   • ✅ VERIFY: Buttons remain accessible")
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("-" * 40)
    print("• Modal properly contains all content")
    print("• Buttons never overflow outside modal boundaries")
    print("• Responsive design works on all screen sizes")
    print("• Content scrolls vertically when needed")
    print("• No horizontal scrolling occurs")
    print("• Touch targets are adequate for mobile")
    print("• Modal adapts to different content lengths")
    
    print("\n⚠️ SIGNS OF REMAINING ISSUES:")
    print("-" * 40)
    print("❌ Buttons appear outside modal boundaries")
    print("❌ Horizontal scrolling occurs")
    print("❌ Content is cut off or inaccessible")
    print("❌ Modal doesn't resize properly on mobile")
    print("❌ Touch targets are too small")
    print("❌ Layout breaks with long words")
    print("❌ Footer buttons overlap or are misaligned")

def print_debug_commands():
    """Print debug commands for modal layout troubleshooting"""
    print("\n🔧 DEBUG COMMANDS (Run in Browser Console):")
    print("-" * 60)
    print("// Check modal dimensions:")
    print("const modal = document.querySelector('.audio-modal-content');")
    print("if (modal) {")
    print("  const rect = modal.getBoundingClientRect();")
    print("  console.log('Modal dimensions:', {")
    print("    width: rect.width,")
    print("    height: rect.height,")
    print("    top: rect.top,")
    print("    left: rect.left")
    print("  });")
    print("}")
    print("")
    print("// Check for overflow:")
    print("const body = document.querySelector('.audio-modal-body');")
    print("if (body) {")
    print("  console.log('Body scroll info:', {")
    print("    scrollHeight: body.scrollHeight,")
    print("    clientHeight: body.clientHeight,")
    print("    scrollTop: body.scrollTop,")
    print("    hasOverflow: body.scrollHeight > body.clientHeight")
    print("  });")
    print("}")
    print("")
    print("// Check button positions:")
    print("const buttons = document.querySelectorAll('.audio-modal-footer button');")
    print("buttons.forEach((btn, i) => {")
    print("  const rect = btn.getBoundingClientRect();")
    print("  console.log(`Button ${i}:`, {")
    print("    width: rect.width,")
    print("    right: rect.right,")
    print("    bottom: rect.bottom")
    print("  });")
    print("});")

if __name__ == '__main__':
    print("🚀 Enhanced Audio Modal Layout Testing")
    print("=" * 60)
    
    try:
        # Create test data
        user, deck, cards = create_modal_test_data()
        
        # Check CSS improvements
        css_ok = check_css_improvements()
        
        # Print testing guide
        print_modal_testing_guide()
        print_debug_commands()
        
        print(f"\n🎉 Modal layout test setup completed!")
        print(f"📊 CSS improvements: {'✅ PASS' if css_ok else '❌ FAIL'}")
        print(f"👤 Test user: {user.email}")
        print(f"📚 Test deck: {deck.name} (ID: {deck.id})")
        print(f"🔗 Test URL: http://localhost:8000/deck/{deck.id}/")
        
        if css_ok:
            print("\n🚀 Ready for modal layout testing!")
            print("Start the development server and follow the testing guide above.")
            print("\nKey improvements made:")
            print("• Flexbox layout for proper content containment")
            print("• Improved modal sizing (700px max width)")
            print("• Better responsive design for all screen sizes")
            print("• Proper button layout and overflow prevention")
            print("• Content scrolling without horizontal overflow")
        else:
            print("\n⚠️ CSS issues found. Please review the errors above.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
