#!/usr/bin/env python
"""
Test script to verify deck dropdown order changes
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

User = get_user_model()

def create_test_data():
    """Create test data for deck dropdown testing"""
    print("🔧 Setting up test data for deck dropdown order testing...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='deck-dropdown-test@example.com',
        defaults={'is_active': True}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"✅ Using existing test user: {user.email}")
    
    # Create test decks to populate the dropdown
    test_decks = [
        'Basic Vocabulary',
        'Advanced Words',
        'IELTS Preparation',
        'Business English',
        'Daily Conversation'
    ]
    
    created_decks = []
    for deck_name in test_decks:
        deck, created = Deck.objects.get_or_create(
            name=deck_name,
            user=user
        )
        created_decks.append(deck)
        
        if created:
            print(f"✅ Created deck: {deck.name} (ID: {deck.id})")
        else:
            print(f"✅ Using existing deck: {deck.name} (ID: {deck.id})")
    
    return user, created_decks

def print_testing_guide():
    """Print comprehensive testing guide for deck dropdown changes"""
    print("\n🧪 DECK DROPDOWN ORDER TESTING GUIDE")
    print("=" * 70)
    
    print("\n🎯 CHANGES IMPLEMENTED:")
    print("-" * 50)
    print("✅ Moved 'Create new deck' option to top of dropdown (after 'Please select deck')")
    print("✅ Added visual styling with ✨ emoji and bold text")
    print("✅ Updated JavaScript to insert new decks in correct position")
    print("✅ Preserved all existing functionality")
    
    print("\n📋 TESTING PROCEDURE:")
    print("-" * 50)
    
    print("\n1️⃣ DROPDOWN ORDER TEST:")
    print("   • Navigate to: http://localhost:8000/add")
    print("   • Click on the deck selection dropdown")
    print("   • ✅ VERIFY: Options appear in this order:")
    print("     1. 'Please select deck' (placeholder)")
    print("     2. '✨ Create new deck' (with emoji and styling)")
    print("     3. 'Basic Vocabulary'")
    print("     4. 'Advanced Words'")
    print("     5. 'IELTS Preparation'")
    print("     6. 'Business English'")
    print("     7. 'Daily Conversation'")
    
    print("\n2️⃣ VISUAL STYLING TEST:")
    print("   • ✅ VERIFY: 'Create new deck' option has ✨ emoji prefix")
    print("   • ✅ VERIFY: 'Create new deck' option appears bold (if browser supports)")
    print("   • ✅ VERIFY: Option is visually distinct from regular deck options")
    
    print("\n3️⃣ FUNCTIONALITY TEST:")
    print("   • Select '✨ Create new deck' option")
    print("   • ✅ VERIFY: SweetAlert modal appears asking for deck name")
    print("   • Enter a test deck name (e.g., 'Test New Deck')")
    print("   • Click 'OK' to create the deck")
    print("   • ✅ VERIFY: Success message appears")
    print("   • ✅ VERIFY: New deck is selected in dropdown")
    print("   • ✅ VERIFY: New deck appears in correct position (after 'Create new deck')")
    
    print("\n4️⃣ POSITION VERIFICATION TEST:")
    print("   • After creating a new deck, open dropdown again")
    print("   • ✅ VERIFY: Order is now:")
    print("     1. 'Please select deck'")
    print("     2. '✨ Create new deck'")
    print("     3. 'Test New Deck' (newly created)")
    print("     4. 'Basic Vocabulary'")
    print("     5. ... (other existing decks)")
    
    print("\n5️⃣ MULTIPLE DECK CREATION TEST:")
    print("   • Create 2-3 more decks using the dropdown")
    print("   • ✅ VERIFY: Each new deck is inserted after 'Create new deck'")
    print("   • ✅ VERIFY: 'Create new deck' always remains at position 2")
    print("   • ✅ VERIFY: Newest decks appear first in the list")
    
    print("\n6️⃣ MOBILE RESPONSIVENESS TEST:")
    print("   • Test on mobile device or use browser dev tools mobile view")
    print("   • ✅ VERIFY: Dropdown works correctly on mobile")
    print("   • ✅ VERIFY: 'Create new deck' option is easily accessible")
    print("   • ✅ VERIFY: Touch interaction works properly")
    
    print("\n7️⃣ ERROR HANDLING TEST:")
    print("   • Try creating a deck with empty name")
    print("   • ✅ VERIFY: Validation error appears")
    print("   • Try creating a deck with duplicate name")
    print("   • ✅ VERIFY: Appropriate error message shows")
    print("   • ✅ VERIFY: Dropdown resets to empty selection on error")
    
    print("\n🔍 BROWSER CONSOLE CHECKS:")
    print("-" * 50)
    print("✅ No JavaScript errors during dropdown interaction")
    print("✅ Styling function executes without errors")
    print("✅ Deck creation API calls work correctly")
    print("✅ DOM manipulation for new deck insertion works")
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("-" * 50)
    print("• 'Create new deck' option appears at top of dropdown (position 2)")
    print("• Option is visually distinct with ✨ emoji and bold styling")
    print("• Clicking option opens deck creation modal")
    print("• New decks are inserted after 'Create new deck' option")
    print("• All existing functionality is preserved")
    print("• Mobile and desktop experience is consistent")
    
    print("\n⚠️ SIGNS OF ISSUES:")
    print("-" * 50)
    print("❌ 'Create new deck' appears at bottom of dropdown")
    print("❌ No visual styling (emoji/bold) on the option")
    print("❌ New decks inserted in wrong position")
    print("❌ Dropdown functionality broken")
    print("❌ JavaScript errors in console")
    print("❌ Mobile responsiveness issues")

def print_test_urls():
    """Print test URLs for manual testing"""
    print("\n🔗 TEST URLS:")
    print("-" * 30)
    print("📄 Add Flashcard Page: http://localhost:8000/add")
    print("📄 Deck List: http://localhost:8000/decks/")
    print("\n💡 TIP: Open browser dev tools to monitor console logs and network requests")

def print_debug_commands():
    """Print debug commands for troubleshooting"""
    print("\n🔧 DEBUG COMMANDS (Run in Browser Console):")
    print("-" * 60)
    print("// Check dropdown option order:")
    print("const selector = document.getElementById('deck-selector');")
    print("Array.from(selector.options).forEach((option, index) => {")
    print("  console.log(`${index}: ${option.textContent} (value: ${option.value})`);")
    print("});")
    print("")
    print("// Check if styling function exists:")
    print("console.log('styleCreateNewDeckOption function available:', ")
    print("  typeof styleCreateNewDeckOption === 'function');")
    print("")
    print("// Manually trigger styling:")
    print("if (typeof styleCreateNewDeckOption === 'function') {")
    print("  styleCreateNewDeckOption();")
    print("}")
    print("")
    print("// Check create new deck option styling:")
    print("const createOption = selector.querySelector('option[value=\"new_deck\"]');")
    print("console.log('Create new deck option:', {")
    print("  text: createOption?.textContent,")
    print("  hasEmoji: createOption?.textContent.includes('✨'),")
    print("  position: Array.from(selector.options).indexOf(createOption)")
    print("});")

if __name__ == '__main__':
    print("🚀 Deck Dropdown Order Testing Setup")
    print("=" * 60)
    
    try:
        user, decks = create_test_data()
        print_testing_guide()
        print_test_urls()
        print_debug_commands()
        
        print(f"\n🎉 Test setup completed successfully!")
        print(f"📊 Created/verified {len(decks)} test decks")
        print(f"👤 Test user: {user.email}")
        print(f"🔗 Test URL: http://localhost:8000/add")
        
        print("\n🚀 Ready for deck dropdown testing!")
        print("Start the development server and follow the testing guide above.")
        print("\nKey things to verify:")
        print("1. 'Create new deck' appears at top of dropdown (position 2)")
        print("2. Option has ✨ emoji and visual styling")
        print("3. New decks are inserted in correct position")
        print("4. All functionality works on desktop and mobile")
        
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        import traceback
        traceback.print_exc()
