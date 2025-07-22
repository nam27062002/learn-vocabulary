from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import JsonResponse
from .models import Flashcard, Deck
import json

User = get_user_model()


class DuplicateCheckTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        self.deck = Deck.objects.create(
            user=self.user,
            name='Test Deck'
        )
        # Create an existing flashcard
        self.existing_flashcard = Flashcard.objects.create(
            user=self.user,
            deck=self.deck,
            word='serendipity'
        )

    def test_check_word_exists_api_existing_word(self):
        """Test that the API correctly identifies existing words"""
        self.client.login(email='testuser@example.com', password='testpass123')

        # Test with existing word (case insensitive)
        response = self.client.get(
            reverse('check_word_exists'),
            {'word': 'serendipity'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['exists'])

        # Test with existing word in different case
        response = self.client.get(
            reverse('check_word_exists'),
            {'word': 'SERENDIPITY'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['exists'])

    def test_check_word_exists_api_new_word(self):
        """Test that the API correctly identifies new words"""
        self.client.login(email='testuser@example.com', password='testpass123')

        # Test with non-existing word
        response = self.client.get(
            reverse('check_word_exists'),
            {'word': 'nonexistentword'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['exists'])

    def test_check_word_exists_api_empty_word(self):
        """Test API behavior with empty word"""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(
            reverse('check_word_exists'),
            {'word': ''}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['exists'])

    def test_check_word_exists_api_unauthenticated(self):
        """Test that unauthenticated users cannot access the API"""
        response = self.client.get(
            reverse('check_word_exists'),
            {'word': 'test'}
        )
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)

    def test_add_flashcard_page_loads(self):
        """Test that the add flashcard page loads correctly with duplicate check URL"""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(reverse('add_flashcard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-check-word-exists-url')
        self.assertContains(response, 'duplicate-warning')

    def test_user_isolation(self):
        """Test that duplicate checking is isolated per user"""
        # Create another user with the same word
        other_user = User.objects.create_user(
            email='otheruser@example.com',
            password='testpass123'
        )
        other_deck = Deck.objects.create(
            user=other_user,
            name='Other Deck'
        )

        self.client.login(email='otheruser@example.com', password='testpass123')

        # The word 'serendipity' exists for testuser but not for otheruser
        response = self.client.get(
            reverse('check_word_exists'),
            {'word': 'serendipity'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['exists'])  # Should be False for different user


class QuickAddWordsTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        self.deck = Deck.objects.create(
            user=self.user,
            name='Test Deck'
        )

    def test_quick_add_section_in_template(self):
        """Test that the quick add section is present in the add flashcard page"""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(reverse('add_flashcard'))
        self.assertEqual(response.status_code, 200)

        # Check for Quick Add elements
        self.assertContains(response, 'quick-add-section')
        self.assertContains(response, 'quick-add-input')
        self.assertContains(response, 'generate-cards-btn')
        self.assertContains(response, 'Quick Add Multiple Words')
        self.assertContains(response, 'separated by | (pipe)')

    def test_quick_add_javascript_functions(self):
        """Test that the JavaScript functions for Quick Add are included"""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(reverse('add_flashcard'))
        self.assertEqual(response.status_code, 200)

        # Check for JavaScript function names
        self.assertContains(response, 'parseQuickAddInput')
        self.assertContains(response, 'generateCardsFromWords')
        self.assertContains(response, 'createNewCardForWord')
        self.assertContains(response, 'showQuickAddResults')

    def test_quick_add_styling(self):
        """Test that the CSS styling for Quick Add is included"""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(reverse('add_flashcard'))
        self.assertEqual(response.status_code, 200)

        # Check for CSS classes
        self.assertContains(response, '.quick-add-section')
        self.assertContains(response, '.generate-cards-btn')
        self.assertContains(response, '.processing-indicator')
        self.assertContains(response, '.spinner')

    def test_quick_add_clearing_functionality(self):
        """Test that the JavaScript includes card clearing functionality"""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(reverse('add_flashcard'))
        self.assertEqual(response.status_code, 200)

        # Check for clearing-related functions and text
        self.assertContains(response, 'clearAllCardsExceptFirst')
        self.assertContains(response, 'Clearing existing cards')
        self.assertContains(response, 'Replace Existing Cards?')
        self.assertContains(response, 'clear all current cards')

    def test_quick_add_confirmation_dialog(self):
        """Test that confirmation dialog elements are present"""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(reverse('add_flashcard'))
        self.assertEqual(response.status_code, 200)

        # Check for confirmation dialog text
        self.assertContains(response, 'Yes, Replace All')
        self.assertContains(response, 'hasContent')
        self.assertContains(response, 'showCancelButton: true')
