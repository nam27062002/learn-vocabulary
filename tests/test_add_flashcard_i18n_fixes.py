#!/usr/bin/env python
"""
Test script to verify the two specific i18n fixes in add_flashcard.html:
1. Deck creation success message localization
2. Flashcard save success popup localization
"""
import os
import sys
import django

# Add the parent directory to Python path so we can import Django modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from vocabulary.context_processors import i18n_compatible_translations

def test_new_translation_keys():
    """Test that the new translation keys for the fixes are present"""
    print("🧪 Testing new translation keys for i18n fixes...")
    
    # Create mock request for context processor
    factory = RequestFactory()
    request = factory.get('/')
    
    # Add session middleware
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    # Test English translations
    request.session['django_language'] = 'en'
    en_context = i18n_compatible_translations(request)
    en_texts = en_context['manual_texts']
    
    # Test Vietnamese translations  
    request.session['django_language'] = 'vi'
    vi_context = i18n_compatible_translations(request)
    vi_texts = vi_context['manual_texts']
    
    # New translation keys that were added for the fixes
    new_keys = [
        'saved_successfully',
        'words_added_to_collection'
    ]
    
    print(f"✅ Testing {len(new_keys)} new translation keys...")
    
    missing_en = []
    missing_vi = []
    
    for key in new_keys:
        if key not in en_texts:
            missing_en.append(key)
        if key not in vi_texts:
            missing_vi.append(key)
    
    if missing_en:
        print(f"❌ Missing English translations: {missing_en}")
    else:
        print("✅ All new English translations present")
        
    if missing_vi:
        print(f"❌ Missing Vietnamese translations: {missing_vi}")
    else:
        print("✅ All new Vietnamese translations present")
    
    return len(missing_en) == 0 and len(missing_vi) == 0

def test_translation_content():
    """Test the actual content of the new translations"""
    print("\n🧪 Testing translation content...")
    
    factory = RequestFactory()
    request = factory.get('/')
    
    # Add session middleware
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    # English
    request.session['django_language'] = 'en'
    en_context = i18n_compatible_translations(request)
    en_texts = en_context['manual_texts']
    
    # Vietnamese
    request.session['django_language'] = 'vi'
    vi_context = i18n_compatible_translations(request)
    vi_texts = vi_context['manual_texts']
    
    print("📋 New translation keys verification:")
    print("-" * 60)
    
    test_keys = [
        'saved_successfully',
        'words_added_to_collection',
        'deck_created_success'  # Existing key that should work correctly
    ]
    
    for key in test_keys:
        print(f"🔑 {key}:")
        print(f"   🇺🇸 EN: {en_texts.get(key, 'MISSING')}")
        print(f"   🇻🇳 VI: {vi_texts.get(key, 'MISSING')}")
        print()

def check_template_fixes():
    """Check that the template has been properly updated"""
    print("🧪 Checking template fixes...")
    
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'vocabulary', 'templates', 'vocabulary', 'add_flashcard.html'
    )
    
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for fixes
    fixes_found = {
        'deck_success_localized': '{{ manual_texts.deck_created_success }}' in content,
        'flashcard_save_title_localized': '{{ manual_texts.saved_successfully }}' in content,
        'flashcard_save_text_localized': '{{ manual_texts.words_added_to_collection }}' in content,
        'no_hardcoded_vietnamese_success': 'Đã lưu thành công!' not in content,
        'no_hardcoded_vietnamese_collection': 'Các từ đã được thêm vào bộ sưu tập:' not in content
    }
    
    print("📋 Template fixes verification:")
    print("-" * 50)
    
    for fix_name, found in fixes_found.items():
        status = "✅ PASS" if found else "❌ FAIL"
        print(f"{fix_name}: {status}")
    
    all_fixes_applied = all(fixes_found.values())
    
    if all_fixes_applied:
        print("\n✅ All template fixes have been applied correctly!")
    else:
        print("\n❌ Some template fixes are missing!")
    
    return all_fixes_applied

def print_manual_testing_guide():
    """Print manual testing guide for the specific fixes"""
    print("\n🧪 MANUAL TESTING GUIDE FOR I18N FIXES")
    print("=" * 60)
    
    print("\n🎯 SPECIFIC ISSUES FIXED:")
    print("-" * 40)
    print("1. Deck creation success message localization")
    print("2. Flashcard save success popup localization")
    
    print("\n📋 TESTING PROCEDURE:")
    print("-" * 40)
    
    print("\n1️⃣ DECK CREATION SUCCESS MESSAGE TEST:")
    print("   🇺🇸 ENGLISH MODE:")
    print("   • Navigate to: http://localhost:8000/en/add-flashcard/")
    print("   • Click 'Create new deck' in deck selector")
    print("   • Enter a deck name (e.g., 'Test Deck')")
    print("   • Click 'OK' to create the deck")
    print("   • ✅ VERIFY: Success popup shows 'Deck \"Test Deck\" has been created successfully.'")
    print("   • ✅ VERIFY: Message is in English")
    print("")
    print("   🇻🇳 VIETNAMESE MODE:")
    print("   • Navigate to: http://localhost:8000/vi/add-flashcard/")
    print("   • Click 'Tạo bộ thẻ mới' in deck selector")
    print("   • Enter a deck name (e.g., 'Bộ thẻ test')")
    print("   • Click 'OK' to create the deck")
    print("   • ✅ VERIFY: Success popup shows 'Bộ thẻ \"Bộ thẻ test\" đã được tạo thành công.'")
    print("   • ✅ VERIFY: Message is in Vietnamese")
    
    print("\n2️⃣ FLASHCARD SAVE SUCCESS MESSAGE TEST:")
    print("   🇺🇸 ENGLISH MODE:")
    print("   • Navigate to: http://localhost:8000/en/add-flashcard/")
    print("   • Fill in flashcard details (word, definition, etc.)")
    print("   • Click 'Save All Flashcards'")
    print("   • ✅ VERIFY: Success popup title shows 'Saved successfully!'")
    print("   • ✅ VERIFY: Success popup text shows 'Words have been added to the collection: [word list]'")
    print("   • ✅ VERIFY: All text is in English")
    print("")
    print("   🇻🇳 VIETNAMESE MODE:")
    print("   • Navigate to: http://localhost:8000/vi/add-flashcard/")
    print("   • Fill in flashcard details (word, definition, etc.)")
    print("   • Click 'Lưu tất cả flashcard'")
    print("   • ✅ VERIFY: Success popup title shows 'Đã lưu thành công!'")
    print("   • ✅ VERIFY: Success popup text shows 'Các từ đã được thêm vào bộ sưu tập: [word list]'")
    print("   • ✅ VERIFY: All text is in Vietnamese")
    
    print("\n3️⃣ LANGUAGE SWITCHING TEST:")
    print("   • Test both features in English mode")
    print("   • Switch to Vietnamese mode (change URL from /en/ to /vi/)")
    print("   • Test both features again in Vietnamese mode")
    print("   • ✅ VERIFY: Messages change language correctly")
    print("   • ✅ VERIFY: No hardcoded English text appears in Vietnamese mode")
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("-" * 40)
    print("• Deck creation success messages are fully localized")
    print("• Flashcard save success messages are fully localized")
    print("• No hardcoded Vietnamese text remains in template")
    print("• Messages display correctly in both languages")
    print("• Language switching works properly for both features")
    
    print("\n⚠️ SIGNS OF REMAINING ISSUES:")
    print("-" * 40)
    print("❌ Deck creation shows English message in Vietnamese mode")
    print("❌ Flashcard save shows hardcoded Vietnamese text")
    print("❌ Messages don't change when switching languages")
    print("❌ Console shows template rendering errors")

def print_debug_commands():
    """Print debug commands for troubleshooting"""
    print("\n🔧 DEBUG COMMANDS (Run in Browser Console):")
    print("-" * 60)
    print("// Check if new translation keys are available:")
    print("console.log('New translation keys:', {")
    print("  saved_successfully: window.manual_texts?.saved_successfully,")
    print("  words_added_to_collection: window.manual_texts?.words_added_to_collection,")
    print("  deck_created_success: window.manual_texts?.deck_created_success")
    print("});")
    print("")
    print("// Test deck creation message replacement:")
    print("const testDeckName = 'Test Deck';")
    print("const message = `${window.manual_texts?.deck_created_success}`.replace('{deck_name}', testDeckName);")
    print("console.log('Deck creation message:', message);")
    print("")
    print("// Test flashcard save message replacement:")
    print("const testWords = ['word1', 'word2', 'word3'];")
    print("const saveMessage = `${window.manual_texts?.words_added_to_collection}`.replace('{words}', testWords.join(', '));")
    print("console.log('Save message:', saveMessage);")

if __name__ == '__main__':
    print("🚀 Add Flashcard I18n Fixes Verification")
    print("=" * 60)
    
    try:
        # Test new translation keys
        keys_ok = test_new_translation_keys()
        
        # Test translation content
        test_translation_content()
        
        # Check template fixes
        template_ok = check_template_fixes()
        
        # Print testing guide
        print_manual_testing_guide()
        print_debug_commands()
        
        print(f"\n🎉 I18n fixes verification completed!")
        print(f"📊 Translation keys: {'✅ PASS' if keys_ok else '❌ FAIL'}")
        print(f"📊 Template fixes: {'✅ PASS' if template_ok else '❌ FAIL'}")
        
        if keys_ok and template_ok:
            print("\n🚀 Ready for manual testing!")
            print("Both i18n issues should now be fixed.")
            print("Start the development server and follow the testing guide above.")
        else:
            print("\n⚠️ Issues found. Please review the errors above.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
