from django.test import TestCase
from unittest.mock import patch, MagicMock
from vocabulary.audio_service import CambridgeWordData
from vocabulary.llm_translator import TranslationResult
from vocabulary.word_details_service import get_word_details


class WordDetailsServiceTest(TestCase):

    @patch('vocabulary.word_details_service._translate')
    @patch('vocabulary.word_details_service._fetch_from_cambridge')
    def test_cambridge_success(self, mock_cambridge, mock_translate):
        mock_cambridge.return_value = CambridgeWordData(
            word="resilient",
            phonetic_uk="/rɪˈzɪl.i.ənt/",
            phonetic_us="/rɪˈzɪl.jənt/",
            audio_uk="https://dictionary.cambridge.org/media/uk.mp3",
            audio_us="https://dictionary.cambridge.org/media/us.mp3",
            definition_en="able to recover quickly",
            part_of_speech="adjective",
            cefr_level="C2",
            example_en="She is resilient.",
        )
        mock_translate.return_value = TranslationResult(
            definition_vi="kiên cường",
            short_meaning_vi="kiên cường",
            source="llm",
        )

        result = get_word_details("resilient")

        self.assertEqual(result["word"], "resilient")
        self.assertEqual(result["phonetic"], "/rɪˈzɪl.i.ənt/")
        self.assertEqual(result["audio_url"], "https://dictionary.cambridge.org/media/uk.mp3")
        self.assertEqual(result["definition_en"], "able to recover quickly")
        self.assertEqual(result["definition_vi"], "kiên cường")
        self.assertEqual(result["cefr_level"], "C2")
        self.assertEqual(result["source"], "cambridge")
        # Backward compat fields
        self.assertIn("phonetics", result)
        self.assertIn("meanings", result)

    @patch('vocabulary.word_details_service._translate_fallback')
    @patch('vocabulary.word_details_service._fetch_from_dictionary_api')
    @patch('vocabulary.word_details_service._fetch_from_cambridge')
    def test_cambridge_fail_fallback_to_dictionary_api(self, mock_cambridge, mock_dict_api, mock_translate):
        mock_cambridge.return_value = None
        mock_dict_api.return_value = {
            "word": "test",
            "phonetics": [{"text": "/tɛst/", "audio": ""}],
            "meanings": [{"part_of_speech": "noun", "definitions": [{"en": "a procedure", "example": ""}]}],
        }
        mock_translate.return_value = TranslationResult(
            definition_vi="bài kiểm tra",
            short_meaning_vi="kiểm tra",
            source="google_translate",
        )

        result = get_word_details("test")

        self.assertEqual(result["source"], "dictionary_api")
        self.assertIn("phonetics", result)

    @patch('vocabulary.word_details_service._fetch_from_dictionary_api')
    @patch('vocabulary.word_details_service._fetch_from_cambridge')
    def test_both_sources_fail(self, mock_cambridge, mock_dict_api):
        mock_cambridge.return_value = None
        mock_dict_api.return_value = None

        result = get_word_details("xyznotaword")

        self.assertIn("error", result)
