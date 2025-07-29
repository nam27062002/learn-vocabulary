"""
Unit tests for enhanced audio service functionality
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from lxml import html
import json

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, Deck

from .audio_service import (
    AudioOption, 
    EnhancedCambridgeAudioFetcher, 
    get_enhanced_audio_fetcher,
    fetch_multiple_audio_options,
    AUDIO_SELECTORS
)

User = get_user_model()


class TestAudioOption(unittest.TestCase):
    """Test AudioOption dataclass"""
    
    def test_audio_option_creation(self):
        """Test AudioOption creation with valid data"""
        option = AudioOption(
            url="https://example.com/audio.mp3",
            label="US pronunciation",
            selector_source="audio1",
            is_valid=True
        )
        
        self.assertEqual(option.url, "https://example.com/audio.mp3")
        self.assertEqual(option.label, "US pronunciation")
        self.assertEqual(option.selector_source, "audio1")
        self.assertTrue(option.is_valid)
        self.assertIsNone(option.error_message)
    
    def test_audio_option_with_error(self):
        """Test AudioOption with error message"""
        option = AudioOption(
            url="https://example.com/audio.mp3",
            label="UK pronunciation",
            selector_source="audio2",
            is_valid=False,
            error_message="HTTP 404"
        )
        
        self.assertFalse(option.is_valid)
        self.assertEqual(option.error_message, "HTTP 404")


class TestEnhancedCambridgeAudioFetcher(unittest.TestCase):
    """Test EnhancedCambridgeAudioFetcher class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.fetcher = EnhancedCambridgeAudioFetcher()
    
    def test_initialization(self):
        """Test fetcher initializes correctly"""
        self.assertIsInstance(self.fetcher, EnhancedCambridgeAudioFetcher)
        self.assertEqual(self.fetcher.audio_selectors, AUDIO_SELECTORS)
    
    @patch('vocabulary.audio_service.requests.Session.get')
    def test_fetch_multiple_audio_sources_success(self, mock_get):
        """Test successful fetching of multiple audio sources"""
        # Mock HTML response with both audio1 and audio2
        mock_html = '''
        <html>
            <div id="audio1">
                <source src="/us/audio.mp3">
                <span class="region">US</span>
            </div>
            <div id="audio2">
                <source src="/uk/audio.mp3">
                <span class="region">UK</span>
            </div>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the method
        options = self.fetcher.fetch_multiple_audio_sources("test")
        
        # Verify results
        self.assertEqual(len(options), 2)
        self.assertTrue(all(option.is_valid for option in options))
        
        # Check URLs are properly constructed
        urls = [option.url for option in options]
        self.assertIn("https://dictionary.cambridge.org/us/audio.mp3", urls)
        self.assertIn("https://dictionary.cambridge.org/uk/audio.mp3", urls)
    
    @patch('vocabulary.audio_service.requests.Session.get')
    def test_fetch_multiple_audio_sources_partial_failure(self, mock_get):
        """Test fetching with only one audio source available"""
        # Mock HTML response with only audio1
        mock_html = '''
        <html>
            <div id="audio1">
                <source src="/us/audio.mp3">
                <span class="region">US</span>
            </div>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the method
        options = self.fetcher.fetch_multiple_audio_sources("test")
        
        # Verify results
        self.assertEqual(len(options), 1)
        self.assertTrue(options[0].is_valid)
        self.assertEqual(options[0].selector_source, "audio1")
    
    def test_extract_audio_from_multiple_selectors(self):
        """Test extraction from HTML tree"""
        # Create mock HTML tree
        mock_html = '''
        <html>
            <div id="audio1">
                <source src="/us/audio.mp3">
                <span class="region">US</span>
            </div>
            <div id="audio2">
                <source src="/uk/audio.mp3">
                <span class="region">UK</span>
            </div>
        </html>
        '''
        
        tree = html.fromstring(mock_html)
        audio_data = self.fetcher.extract_audio_from_multiple_selectors(tree)
        
        # Verify extraction
        self.assertEqual(len(audio_data), 2)
        
        # Check first audio source
        self.assertEqual(audio_data[0]['url'], 'https://dictionary.cambridge.org/us/audio.mp3')
        self.assertEqual(audio_data[0]['selector_source'], 'audio1')
        
        # Check second audio source
        self.assertEqual(audio_data[1]['url'], 'https://dictionary.cambridge.org/uk/audio.mp3')
        self.assertEqual(audio_data[1]['selector_source'], 'audio2')
    
    def test_get_pronunciation_labels(self):
        """Test pronunciation label extraction"""
        # Create mock HTML tree
        mock_html = '''
        <html>
            <div id="audio1">
                <source src="/us/audio.mp3">
                <span class="region">US</span>
            </div>
        </html>
        '''
        
        tree = html.fromstring(mock_html)
        selector_config = AUDIO_SELECTORS[0]  # audio1 config
        
        label = self.fetcher.get_pronunciation_labels(tree, selector_config)
        self.assertEqual(label, "US pronunciation")
    
    def test_validate_audio_urls(self):
        """Test audio URL validation"""
        audio_data = [
            {
                'url': 'https://example.com/valid.mp3',
                'label': 'US pronunciation',
                'selector_source': 'audio1'
            },
            {
                'url': 'invalid-url',
                'label': 'Invalid',
                'selector_source': 'audio2'
            }
        ]
        
        validated_options = self.fetcher.validate_audio_urls(audio_data)
        
        # Should return only the valid URL
        valid_options = [opt for opt in validated_options if opt.is_valid]
        self.assertEqual(len(valid_options), 1)
        self.assertEqual(valid_options[0].url, 'https://example.com/valid.mp3')


class TestEnhancedAudioAPI(TestCase):
    """Test enhanced audio API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.deck = Deck.objects.create(
            name='Test Deck',
            user=self.user
        )
        self.flashcard = Flashcard.objects.create(
            word='test',
            user=self.user,
            deck=self.deck
        )
        # Login using email since CustomUser uses email as username
        self.client.login(email='test@example.com', password='testpass123')
    
    @patch('vocabulary.audio_service.fetch_multiple_audio_options')
    def test_api_fetch_enhanced_audio_success(self, mock_fetch):
        """Test successful enhanced audio fetching"""
        # Mock audio options
        mock_options = [
            AudioOption(
                url="https://example.com/us.mp3",
                label="US pronunciation",
                selector_source="audio1",
                is_valid=True
            ),
            AudioOption(
                url="https://example.com/uk.mp3",
                label="UK pronunciation",
                selector_source="audio2",
                is_valid=True
            )
        ]
        mock_fetch.return_value = mock_options
        
        # Make API request
        response = self.client.post('/api/fetch-enhanced-audio/', {
            'card_id': self.flashcard.id,
            'word': 'test'
        }, content_type='application/json')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['word'], 'test')
        self.assertEqual(len(data['audio_options']), 2)
        self.assertEqual(data['total_found'], 2)
    
    def test_api_fetch_enhanced_audio_invalid_card(self):
        """Test API with invalid card ID"""
        response = self.client.post('/api/fetch-enhanced-audio/', {
            'card_id': 99999,
            'word': 'test'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Flashcard not found')
    
    def test_api_update_flashcard_audio_success(self):
        """Test successful flashcard audio update"""
        response = self.client.post('/api/update-flashcard-audio/', {
            'card_id': self.flashcard.id,
            'audio_url': 'https://example.com/new-audio.mp3'
        }, content_type='application/json')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['card_id'], self.flashcard.id)
        self.assertEqual(data['audio_url'], 'https://example.com/new-audio.mp3')
        
        # Verify database update
        self.flashcard.refresh_from_db()
        self.assertEqual(self.flashcard.audio_url, 'https://example.com/new-audio.mp3')
    
    def test_api_update_flashcard_audio_invalid_url(self):
        """Test API with invalid audio URL"""
        response = self.client.post('/api/update-flashcard-audio/', {
            'card_id': self.flashcard.id,
            'audio_url': 'invalid-url'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Invalid audio URL format')


class TestAudioSelectors(unittest.TestCase):
    """Test audio selector configuration"""
    
    def test_audio_selectors_structure(self):
        """Test that AUDIO_SELECTORS has correct structure"""
        self.assertEqual(len(AUDIO_SELECTORS), 2)
        
        # Test audio1 selector
        audio1 = AUDIO_SELECTORS[0]
        self.assertEqual(audio1['id'], 'audio1')
        self.assertEqual(audio1['xpath'], '//*[@id="audio1"]/source[1]')
        self.assertIn('label_xpath', audio1)
        self.assertIn('default_label', audio1)
        
        # Test audio2 selector
        audio2 = AUDIO_SELECTORS[1]
        self.assertEqual(audio2['id'], 'audio2')
        self.assertEqual(audio2['xpath'], '//*[@id="audio2"]/source[1]')
        self.assertIn('label_xpath', audio2)
        self.assertIn('default_label', audio2)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    def test_get_enhanced_audio_fetcher(self):
        """Test enhanced audio fetcher factory function"""
        fetcher = get_enhanced_audio_fetcher()
        self.assertIsInstance(fetcher, EnhancedCambridgeAudioFetcher)
    
    @patch('vocabulary.audio_service.enhanced_cambridge_audio_fetcher.fetch_multiple_audio_sources')
    def test_fetch_multiple_audio_options(self, mock_fetch):
        """Test convenience function for fetching multiple options"""
        mock_options = [
            AudioOption(
                url="https://example.com/test.mp3",
                label="Test pronunciation",
                selector_source="audio1",
                is_valid=True
            )
        ]
        mock_fetch.return_value = mock_options
        
        options = fetch_multiple_audio_options("test")
        
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0].url, "https://example.com/test.mp3")
        mock_fetch.assert_called_once_with("test")


if __name__ == '__main__':
    unittest.main()
