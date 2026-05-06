# tests/test_example_sentence.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, Deck

User = get_user_model()

class ExampleSentenceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.com', password='pass')
        self.deck = Deck.objects.create(user=self.user, name='Test')

    def test_flashcard_has_example_sentence_field(self):
        card = Flashcard.objects.create(user=self.user, deck=self.deck, word='resilient')
        card.example_sentence = 'She is a resilient person.'
        card.example_source = 'cambridge'
        card.save()
        card.refresh_from_db()
        self.assertEqual(card.example_sentence, 'She is a resilient person.')
        self.assertEqual(card.example_source, 'cambridge')

    def test_example_fields_nullable(self):
        card = Flashcard.objects.create(user=self.user, deck=self.deck, word='brave')
        self.assertIsNone(card.example_sentence)
        self.assertIsNone(card.example_source)


from unittest.mock import patch, MagicMock
from vocabulary.word_details_service import get_word_details

class ExampleSentenceServiceTest(TestCase):
    @patch('vocabulary.word_details_service._cambridge_fetcher')
    @patch('vocabulary.word_details_service._translator')
    def test_cambridge_example_used_when_present(self, mock_translator, mock_fetcher):
        from vocabulary.audio_service import CambridgeWordData
        from vocabulary.llm_translator import TranslationResult
        mock_fetcher.fetch_word_data.return_value = CambridgeWordData(
            word='resilient',
            definition_en='able to recover quickly',
            example_en='She bounced back quickly.',
            part_of_speech='adjective',
        )
        mock_translator.translate_definition.return_value = TranslationResult(
            definition_vi='có khả năng phục hồi', short_meaning_vi='phục hồi', source='llm'
        )
        result = get_word_details('resilient')
        self.assertEqual(result['example_sentence'], 'She bounced back quickly.')
        self.assertEqual(result['example_source'], 'cambridge')

    @patch('vocabulary.word_details_service._generate_example_llm')
    @patch('vocabulary.word_details_service._cambridge_fetcher')
    @patch('vocabulary.word_details_service._translator')
    def test_llm_fallback_when_cambridge_has_no_example(self, mock_translator, mock_fetcher, mock_llm):
        from vocabulary.audio_service import CambridgeWordData
        from vocabulary.llm_translator import TranslationResult
        mock_fetcher.fetch_word_data.return_value = CambridgeWordData(
            word='test',
            definition_en='a procedure to assess',
            example_en='',  # empty — LLM should be called
            part_of_speech='noun',
        )
        mock_translator.translate_definition.return_value = TranslationResult(
            definition_vi='bài kiểm tra', short_meaning_vi='kiểm tra', source='llm'
        )
        mock_llm.return_value = 'The teacher gave a test on Friday.'
        result = get_word_details('test')
        self.assertEqual(result['example_sentence'], 'The teacher gave a test on Friday.')
        self.assertEqual(result['example_source'], 'llm')
        mock_llm.assert_called_once_with('test', 'a procedure to assess')
