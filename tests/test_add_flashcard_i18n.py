#!/usr/bin/env python
"""
Test script to verify add_flashcard.html internationalization (i18n) implementation
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
from vocabulary.models import Deck
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils import translation
from vocabulary.context_processors import i18n_compatible_translations

User = get_user_model()

def test_translation_keys():
    """Test that all required translation keys exist in both languages"""
    print("🧪 Testing translation keys for add_flashcard.html...")
    
    # Create mock request for context processor
    factory = RequestFactory()
    request = factory.get('/')

    # Add session middleware
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()

    # Test English translations
    request.session['django_language'] = 'en'
    translation.activate('en')
    en_context = i18n_compatible_translations(request)
    en_texts = en_context['manual_texts']

    # Test Vietnamese translations
    request.session['django_language'] = 'vi'
    translation.activate('vi')
    vi_context = i18n_compatible_translations(request)
    vi_texts = vi_context['manual_texts']
    
    # Required translation keys for add_flashcard.html
    required_keys = [
        # Existing keys
        'add_flashcard',
        'add_new_flashcard', 
        'add_vocabulary_description',
        'select_deck',
        'please_select_deck',
        'create_new_deck',
        'term_label',
        'phonetic_label',
        'english_definition_label',
        'vietnamese_definition_label',
        'term_placeholder',
        'phonetic_placeholder',
        'definition_placeholder',
        'vietnamese_placeholder',
        'upload_image',
        'add_new_card',
        'save_all_flashcards',
        'drag_to_move',
        'delete_card',
        'part_of_speech',
        'listen',
        
        # New keys added for i18n
        'quick_add_multiple_words',
        'quick_add_placeholder',
        'quick_add_info',
        'generate_cards',
        'processing_words',
        'processing_word_individual',
        'create_new_deck_title',
        'deck_name_label',
        'deck_name_placeholder',
        'deck_name_required',
        'cancel',
        'created',
        'deck_created_success',
        'cannot_create_deck',
        'unknown_error',
        'duplicate_word_detected',
        'word_already_exists',
        'use_different_word',
        'no_words_found',
        'enter_words_pipe',
        'no_deck_selected',
        'select_deck_before_adding',
        'cannot_delete_only_card',
        'translating',
        'translation_not_available',
        'translation_error',
        'quick_add_results',
        'words_added_successfully',
        'duplicate_words_skipped',
        'words_with_errors',
        'no_words_processed'
    ]
    
    print(f"✅ Testing {len(required_keys)} translation keys...")
    
    missing_en = []
    missing_vi = []
    
    for key in required_keys:
        if key not in en_texts:
            missing_en.append(key)
        if key not in vi_texts:
            missing_vi.append(key)
    
    if missing_en:
        print(f"❌ Missing English translations: {missing_en}")
    else:
        print("✅ All English translations present")
        
    if missing_vi:
        print(f"❌ Missing Vietnamese translations: {missing_vi}")
    else:
        print("✅ All Vietnamese translations present")
    
    return len(missing_en) == 0 and len(missing_vi) == 0

def test_template_rendering():
    """Test that the template renders without errors in both languages"""
    print("\n🧪 Testing template rendering in both languages...")
    
    from django.test import Client
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Create test user
    user, created = User.objects.get_or_create(
        email='i18n-test@example.com',
        defaults={'is_active': True}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    client = Client()
    client.force_login(user)
    
    # Test English version
    response_en = client.get('/en/add-flashcard/')
    if response_en.status_code == 200:
        print("✅ English template renders successfully")
        
        # Check for some key translated content
        content = response_en.content.decode('utf-8')
        if 'Quick Add Multiple Words' in content:
            print("✅ English quick add section found")
        else:
            print("❌ English quick add section not found")
            
    else:
        print(f"❌ English template failed to render: {response_en.status_code}")
    
    # Test Vietnamese version
    response_vi = client.get('/vi/add-flashcard/')
    if response_vi.status_code == 200:
        print("✅ Vietnamese template renders successfully")
        
        # Check for some key translated content
        content = response_vi.content.decode('utf-8')
        if 'Thêm nhanh nhiều từ' in content:
            print("✅ Vietnamese quick add section found")
        else:
            print("❌ Vietnamese quick add section not found")
            
    else:
        print(f"❌ Vietnamese template failed to render: {response_vi.status_code}")
    
    return response_en.status_code == 200 and response_vi.status_code == 200

def print_sample_translations():
    """Print sample translations to verify quality"""
    print("\n📋 Sample translations verification:")
    print("-" * 60)
    
    factory = RequestFactory()
    request = factory.get('/')

    # Add session middleware
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()

    # English
    request.session['django_language'] = 'en'
    translation.activate('en')
    en_context = i18n_compatible_translations(request)
    en_texts = en_context['manual_texts']

    # Vietnamese
    request.session['django_language'] = 'vi'
    translation.activate('vi')
    vi_context = i18n_compatible_translations(request)
    vi_texts = vi_context['manual_texts']
    
    sample_keys = [
        'quick_add_multiple_words',
        'quick_add_placeholder',
        'generate_cards',
        'duplicate_word_detected',
        'words_added_successfully',
        'processing_word_individual'
    ]
    
    for key in sample_keys:
        print(f"🔑 {key}:")
        print(f"   🇺🇸 EN: {en_texts.get(key, 'MISSING')}")
        print(f"   🇻🇳 VI: {vi_texts.get(key, 'MISSING')}")
        print()

def print_testing_guide():
    """Print manual testing guide"""
    print("\n🧪 MANUAL TESTING GUIDE FOR ADD FLASHCARD I18N")
    print("=" * 70)
    
    print("\n📋 TESTING PROCEDURE:")
    print("-" * 50)
    
    print("\n1️⃣ ENGLISH LANGUAGE TEST:")
    print("   • Navigate to: http://localhost:8000/en/add-flashcard/")
    print("   • ✅ VERIFY: Page title shows 'Add Flashcard - Learn English'")
    print("   • ✅ VERIFY: Quick Add section shows 'Quick Add Multiple Words'")
    print("   • ✅ VERIFY: Placeholder text is in English")
    print("   • ✅ VERIFY: Button shows 'Generate Cards'")
    print("   • ✅ VERIFY: Form labels are in English")
    
    print("\n2️⃣ VIETNAMESE LANGUAGE TEST:")
    print("   • Navigate to: http://localhost:8000/vi/add-flashcard/")
    print("   • ✅ VERIFY: Page title shows 'Thêm Flashcard - Learn English'")
    print("   • ✅ VERIFY: Quick Add section shows 'Thêm nhanh nhiều từ'")
    print("   • ✅ VERIFY: Placeholder text is in Vietnamese")
    print("   • ✅ VERIFY: Button shows 'Tạo thẻ'")
    print("   • ✅ VERIFY: Form labels are in Vietnamese")
    
    print("\n3️⃣ INTERACTIVE FEATURES TEST:")
    print("   • Test 'Create new deck' functionality")
    print("   • ✅ VERIFY: SweetAlert popup shows localized text")
    print("   • Test Quick Add with multiple words")
    print("   • ✅ VERIFY: Processing messages are localized")
    print("   • ✅ VERIFY: Results popup shows localized text")
    print("   • Test duplicate word detection")
    print("   • ✅ VERIFY: Warning messages are localized")
    
    print("\n4️⃣ ERROR HANDLING TEST:")
    print("   • Try to delete the only card")
    print("   • ✅ VERIFY: Alert message is localized")
    print("   • Try Quick Add without selecting deck")
    print("   • ✅ VERIFY: Warning popup is localized")
    print("   • Test translation functionality")
    print("   • ✅ VERIFY: Loading and error messages are localized")
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("-" * 50)
    print("• All user-facing text should be properly localized")
    print("• No hardcoded English text should appear in Vietnamese mode")
    print("• SweetAlert popups should use localized text")
    print("• Form validation messages should be localized")
    print("• Processing indicators should show localized text")
    print("• Error messages should be in the selected language")

if __name__ == '__main__':
    print("🚀 Add Flashcard Internationalization (i18n) Test")
    print("=" * 70)
    
    try:
        # Test translation keys
        keys_ok = test_translation_keys()
        
        # Test template rendering
        render_ok = test_template_rendering()
        
        # Show sample translations
        print_sample_translations()
        
        # Print testing guide
        print_testing_guide()
        
        print(f"\n🎉 I18n implementation test completed!")
        print(f"📊 Translation keys: {'✅ PASS' if keys_ok else '❌ FAIL'}")
        print(f"📊 Template rendering: {'✅ PASS' if render_ok else '❌ FAIL'}")
        
        if keys_ok and render_ok:
            print("\n🚀 Ready for manual testing!")
            print("Start the development server and follow the testing guide above.")
        else:
            print("\n⚠️ Issues found. Please review the errors above.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
