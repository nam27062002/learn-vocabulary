from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from vocabulary.audio_service import CambridgeWordData
from vocabulary.llm_translator import (
    BaseLLMTranslator,
    TranslationResult,
    LiteLLMTranslator,
)


LLM_TEST_SETTINGS = {
    'LLM_URL': 'https://test.example.com/v1/chat/completions',
    'LLM_MODEL': 'test-model',
    'LLM_API_KEY': 'test-key',
    'LLM_TIMEOUT': 10,
}


class TranslationResultTest(TestCase):
    def test_dataclass_fields(self):
        result = TranslationResult(
            definition_vi="kiên cường",
            short_meaning_vi="kiên cường",
            source="llm",
        )
        self.assertEqual(result.definition_vi, "kiên cường")
        self.assertEqual(result.source, "llm")


@override_settings(**LLM_TEST_SETTINGS)
class LiteLLMTranslatorTest(TestCase):
    def setUp(self):
        self.translator = LiteLLMTranslator()
        self.word_data = CambridgeWordData(
            word="resilient",
            phonetic_uk="/rɪˈzɪl.i.ənt/",
            definition_en="able to be happy again after something difficult",
            part_of_speech="adjective",
            cefr_level="C2",
            example_en="She's a resilient girl.",
        )

    @patch('vocabulary.llm_translator.cache')
    @patch('vocabulary.llm_translator.requests.post')
    def test_translate_success(self, mock_post, mock_cache):
        mock_cache.get.return_value = None
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"definition_vi": "kiên cường, có khả năng phục hồi", "short_meaning_vi": "kiên cường"}'
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.translator.translate_definition(self.word_data)

        self.assertEqual(result.definition_vi, "kiên cường, có khả năng phục hồi")
        self.assertEqual(result.short_meaning_vi, "kiên cường")
        self.assertEqual(result.source, "llm")
        mock_cache.set.assert_called_once()

    @patch('vocabulary.llm_translator.cache')
    def test_translate_cache_hit(self, mock_cache):
        cached = TranslationResult(
            definition_vi="kiên cường",
            short_meaning_vi="kiên cường",
            source="llm",
        )
        mock_cache.get.return_value = cached

        result = self.translator.translate_definition(self.word_data)

        self.assertEqual(result.definition_vi, "kiên cường")
        self.assertEqual(result.source, "llm")

    @patch('vocabulary.llm_translator.cache')
    @patch('vocabulary.llm_translator.requests.post')
    @patch('vocabulary.llm_translator.GoogleTranslator')
    def test_translate_llm_fail_fallback_to_google(self, mock_google_cls, mock_post, mock_cache):
        mock_cache.get.return_value = None
        mock_post.side_effect = Exception("LLM timeout")

        mock_google_instance = MagicMock()
        mock_google_instance.translate.return_value = "kiên cường (Google)"
        mock_google_cls.return_value = mock_google_instance

        result = self.translator.translate_definition(self.word_data)

        self.assertIn("kiên cường", result.definition_vi)
        self.assertEqual(result.source, "google_translate")
        mock_cache.set.assert_called_once()

    @patch('vocabulary.llm_translator.cache')
    @patch('vocabulary.llm_translator.requests.post')
    def test_translate_llm_returns_invalid_json(self, mock_post, mock_cache):
        mock_cache.get.return_value = None
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'not json at all'}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with patch('vocabulary.llm_translator.GoogleTranslator') as mock_google_cls:
            mock_google_instance = MagicMock()
            mock_google_instance.translate.return_value = "fallback translation"
            mock_google_cls.return_value = mock_google_instance

            result = self.translator.translate_definition(self.word_data)

        self.assertEqual(result.source, "google_translate")
