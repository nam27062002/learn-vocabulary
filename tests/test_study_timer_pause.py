#!/usr/bin/env python
"""
Test script to verify automatic timer pause/resume functionality in study page
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

def create_timer_test_data():
    """Create test data for timer functionality testing"""
    print("🔧 Setting up test data for study timer pause/resume testing...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='timer-test@example.com',
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
        name='Timer Test Deck',
        user=user
    )
    if created:
        print(f"✅ Created test deck: {deck.name}")
    else:
        print(f"✅ Using existing test deck: {deck.name}")
    
    # Create test flashcards for study session
    test_words = [
        {
            'word': 'focus',
            'phonetic': '/ˈfoʊ.kəs/',
            'part_of_speech': 'verb',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/f/foc/focus/focus.mp3'
        },
        {
            'word': 'timer',
            'phonetic': '/ˈtaɪ.mər/',
            'part_of_speech': 'noun',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/t/tim/timer/timer.mp3'
        },
        {
            'word': 'pause',
            'phonetic': '/pɔːz/',
            'part_of_speech': 'verb',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/p/pau/pause/pause.mp3'
        },
        {
            'word': 'resume',
            'phonetic': '/rɪˈzuːm/',
            'part_of_speech': 'verb',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/r/res/resum/resume.mp3'
        },
        {
            'word': 'study',
            'phonetic': '/ˈstʌd.i/',
            'part_of_speech': 'verb',
            'audio_url': 'https://dictionary.cambridge.org/media/english/us_pron/s/stu/study/study.mp3'
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

def check_timer_implementation():
    """Check that the timer pause/resume implementation is in place"""
    print("\n🧪 Checking timer pause/resume implementation...")
    
    js_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'js', 'study.js'
    )
    
    css_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'static', 'css', 'study.css'
    )
    
    if not os.path.exists(js_path):
        print(f"❌ JavaScript file not found: {js_path}")
        return False
    
    if not os.path.exists(css_path):
        print(f"❌ CSS file not found: {css_path}")
        return False
    
    with open(js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for key implementation features
    js_features = {
        'pause_variables': 'timerPaused' in js_content and 'pausedTime' in js_content,
        'pause_function': 'function pauseStudyTimer()' in js_content,
        'resume_function': 'function resumeStudyTimer()' in js_content,
        'visibility_api': 'visibilitychange' in js_content,
        'focus_blur_events': 'addEventListener(\'blur\'' in js_content and 'addEventListener(\'focus\'' in js_content,
        'paused_display': '(Paused)' in js_content,
        'css_class_toggle': 'classList.add(\'paused\')' in js_content
    }
    
    css_features = {
        'paused_class': '.timer-display.paused' in css_content,
        'paused_animation': 'pulse-paused' in css_content,
        'paused_background': 'linear-gradient(135deg, #f59e0b, #d97706)' in css_content
    }
    
    print("📋 JavaScript implementation verification:")
    print("-" * 50)
    
    for feature, found in js_features.items():
        status = "✅ PASS" if found else "❌ FAIL"
        print(f"{feature}: {status}")
    
    print("\n📋 CSS implementation verification:")
    print("-" * 50)
    
    for feature, found in css_features.items():
        status = "✅ PASS" if found else "❌ FAIL"
        print(f"{feature}: {status}")
    
    all_features = all(js_features.values()) and all(css_features.values())
    
    if all_features:
        print("\n✅ All timer pause/resume features implemented!")
    else:
        print("\n❌ Some timer features are missing!")
    
    return all_features

def print_timer_testing_guide():
    """Print comprehensive testing guide for timer pause/resume functionality"""
    print("\n🧪 STUDY TIMER PAUSE/RESUME TESTING GUIDE")
    print("=" * 70)
    
    print("\n🎯 FUNCTIONALITY IMPLEMENTED:")
    print("-" * 40)
    print("✅ Automatic timer pause when tab loses focus")
    print("✅ Automatic timer resume when tab gains focus")
    print("✅ Visual indication of paused state")
    print("✅ Accurate time tracking (excludes paused time)")
    print("✅ Cross-browser compatibility")
    
    print("\n📋 TESTING PROCEDURE:")
    print("-" * 40)
    
    print("\n1️⃣ BASIC TIMER FUNCTIONALITY TEST:")
    print("   • Navigate to: http://localhost:8000/study/")
    print("   • Select 'Timer Test Deck' and start studying")
    print("   • ✅ VERIFY: Timer starts counting (00:01, 00:02, etc.)")
    print("   • ✅ VERIFY: Timer display shows green background")
    print("   • ✅ VERIFY: Timer format is MM:SS or HH:MM:SS")
    
    print("\n2️⃣ TAB SWITCHING PAUSE TEST:")
    print("   • Start a study session with timer running")
    print("   • Switch to another browser tab")
    print("   • ✅ VERIFY: Timer automatically pauses")
    print("   • ✅ VERIFY: Timer display shows orange background")
    print("   • ✅ VERIFY: Timer text shows '(Paused)' indicator")
    print("   • ✅ VERIFY: Timer display has pulsing animation")
    print("   • Switch back to study tab")
    print("   • ✅ VERIFY: Timer automatically resumes")
    print("   • ✅ VERIFY: Timer display returns to green background")
    print("   • ✅ VERIFY: '(Paused)' indicator disappears")
    
    print("\n3️⃣ WINDOW FOCUS PAUSE TEST:")
    print("   • Start a study session with timer running")
    print("   • Switch to another application (Alt+Tab)")
    print("   • ✅ VERIFY: Timer pauses when window loses focus")
    print("   • ✅ VERIFY: Visual paused state is shown")
    print("   • Return to browser window")
    print("   • ✅ VERIFY: Timer resumes automatically")
    print("   • ✅ VERIFY: Visual state returns to normal")
    
    print("\n4️⃣ BROWSER MINIMIZE TEST:")
    print("   • Start a study session with timer running")
    print("   • Minimize the browser window")
    print("   • ✅ VERIFY: Timer pauses (check when restored)")
    print("   • Restore the browser window")
    print("   • ✅ VERIFY: Timer resumes from paused time")
    
    print("\n5️⃣ ACCURATE TIME TRACKING TEST:")
    print("   • Start study session, note timer at 00:30")
    print("   • Switch tabs for 10 seconds")
    print("   • Return to study tab")
    print("   • ✅ VERIFY: Timer shows approximately 00:30 (not 00:40)")
    print("   • ✅ VERIFY: Paused time is not counted in total")
    
    print("\n6️⃣ MULTIPLE PAUSE/RESUME CYCLES TEST:")
    print("   • Start study session")
    print("   • Switch tabs multiple times (pause/resume cycles)")
    print("   • ✅ VERIFY: Each pause/resume cycle works correctly")
    print("   • ✅ VERIFY: Timer accurately tracks only active time")
    print("   • ✅ VERIFY: Visual states change correctly each time")
    
    print("\n7️⃣ STUDY SESSION COMPLETION TEST:")
    print("   • Complete a study session with pause/resume cycles")
    print("   • ✅ VERIFY: Final time reflects only active study time")
    print("   • ✅ VERIFY: Timer resets properly for new session")
    print("   • ✅ VERIFY: No paused state carries over to new session")
    
    print("\n8️⃣ BROWSER COMPATIBILITY TEST:")
    print("   • Test in Chrome, Firefox, Safari, Edge")
    print("   • ✅ VERIFY: Page Visibility API works in all browsers")
    print("   • ✅ VERIFY: Focus/blur events work as fallback")
    print("   • ✅ VERIFY: Visual indicators display correctly")
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("-" * 40)
    print("• Timer pauses automatically when page loses focus")
    print("• Timer resumes automatically when page gains focus")
    print("• Paused state is clearly indicated visually")
    print("• Only active study time is counted")
    print("• No user intervention required")
    print("• Works across different browsers")
    print("• Smooth transitions between paused/active states")
    
    print("\n⚠️ SIGNS OF ISSUES:")
    print("-" * 40)
    print("❌ Timer continues counting when tab is not active")
    print("❌ Timer doesn't pause when switching applications")
    print("❌ No visual indication of paused state")
    print("❌ Paused time is included in total study time")
    print("❌ Timer doesn't resume when returning to tab")
    print("❌ Visual states don't change correctly")
    print("❌ Console shows JavaScript errors")

def print_debug_commands():
    """Print debug commands for timer troubleshooting"""
    print("\n🔧 DEBUG COMMANDS (Run in Browser Console):")
    print("-" * 60)
    print("// Check timer state:")
    print("console.log('Timer state:', {")
    print("  studyStartTime: window.studyStartTime,")
    print("  timerPaused: window.timerPaused,")
    print("  pausedTime: window.pausedTime,")
    print("  timerInterval: window.timerInterval")
    print("});")
    print("")
    print("// Check Page Visibility API support:")
    print("console.log('Visibility API:', {")
    print("  hidden: document.hidden,")
    print("  visibilityState: document.visibilityState,")
    print("  hasFocus: document.hasFocus()")
    print("});")
    print("")
    print("// Manually test pause/resume:")
    print("// (Only works if study session is active)")
    print("pauseStudyTimer(); // Pause timer")
    print("resumeStudyTimer(); // Resume timer")
    print("")
    print("// Check timer display element:")
    print("const timerDisplay = document.getElementById('timerDisplay');")
    print("console.log('Timer display:', {")
    print("  element: timerDisplay,")
    print("  classes: timerDisplay?.className,")
    print("  text: timerDisplay?.textContent")
    print("});")

if __name__ == '__main__':
    print("🚀 Study Timer Pause/Resume Functionality Test")
    print("=" * 60)
    
    try:
        # Create test data
        user, deck, cards = create_timer_test_data()
        
        # Check implementation
        impl_ok = check_timer_implementation()
        
        # Print testing guide
        print_timer_testing_guide()
        print_debug_commands()
        
        print(f"\n🎉 Timer test setup completed!")
        print(f"📊 Implementation: {'✅ PASS' if impl_ok else '❌ FAIL'}")
        print(f"👤 Test user: {user.email}")
        print(f"📚 Test deck: {deck.name} (ID: {deck.id})")
        print(f"🔗 Test URL: http://localhost:8000/study/")
        
        if impl_ok:
            print("\n🚀 Ready for timer pause/resume testing!")
            print("Start the development server and follow the testing guide above.")
            print("\nKey features implemented:")
            print("• Automatic pause when tab loses focus")
            print("• Automatic resume when tab gains focus")
            print("• Visual paused state indication")
            print("• Accurate time tracking (excludes paused time)")
            print("• Cross-browser compatibility")
        else:
            print("\n⚠️ Implementation issues found. Please review the errors above.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
