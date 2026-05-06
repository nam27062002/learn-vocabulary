# tests/test_example_sentence.py
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
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

    @patch('vocabulary.word_details_service._generate_example_llm')
    @patch('vocabulary.word_details_service._cambridge_fetcher')
    @patch('vocabulary.word_details_service._translator')
    def test_empty_example_when_both_sources_fail(self, mock_translator, mock_fetcher, mock_llm):
        from vocabulary.audio_service import CambridgeWordData
        from vocabulary.llm_translator import TranslationResult
        mock_fetcher.fetch_word_data.return_value = CambridgeWordData(
            word='obscure',
            definition_en='not well known',
            example_en='',  # no Cambridge example
            part_of_speech='adjective',
        )
        mock_translator.translate_definition.return_value = TranslationResult(
            definition_vi='ít được biết đến', short_meaning_vi='ít biết', source='llm'
        )
        mock_llm.return_value = ''  # LLM also fails
        result = get_word_details('obscure')
        self.assertEqual(result['example_sentence'], '')
        self.assertEqual(result['example_source'], '')


class SaveFlashcardsExampleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='save@test.com', password='pass')
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')
        self.client.login(email='save@test.com', password='pass')

    def test_save_flashcard_persists_example(self):
        response = self.client.post(reverse('save_flashcards'), {
            'deck_id': self.deck.id,
            'flashcards-0-word': 'resilient',
            'flashcards-0-english_definition': 'able to recover quickly',
            'flashcards-0-vietnamese_definition': 'có khả năng phục hồi',
            'flashcards-0-example_sentence': 'She bounced back quickly.',
            'flashcards-0-example_source': 'cambridge',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        card = Flashcard.objects.get(user=self.user, word='resilient')
        self.assertEqual(card.example_sentence, 'She bounced back quickly.')
        self.assertEqual(card.example_source, 'cambridge')


class ApiNextQuestionExampleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='study@test.com', password='pass')
        self.deck = Deck.objects.create(user=self.user, name='Study Deck')
        from vocabulary.models import Definition
        self.card = Flashcard.objects.create(
            user=self.user, deck=self.deck, word='resilient',
            example_sentence='She bounced back quickly.',
            example_source='cambridge',
        )
        Definition.objects.create(
            flashcard=self.card,
            english_definition='able to recover quickly',
            vietnamese_definition='có khả năng phục hồi',
        )
        self.client.login(email='study@test.com', password='pass')

    def test_next_question_includes_example_sentence(self):
        response = self.client.post(
            reverse('api_next_question'),
            data=json.dumps({'deck_ids': [self.deck.id], 'study_mode': 'decks', 'seen_card_ids': []}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['done'])
        self.assertIn('example_sentence', data['question'])
        self.assertEqual(data['question']['example_sentence'], 'She bounced back quickly.')
