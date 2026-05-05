from django.test import TestCase
from unittest.mock import patch, MagicMock
from lxml import html
from vocabulary.audio_service import EnhancedCambridgeAudioFetcher, CambridgeWordData
import requests


SAMPLE_CAMBRIDGE_HTML = """
<html>
<head><meta charset="utf-8"></head>
<body>
<div class="entry-body__el">
  <div class="pos-header dpos-h">
    <span class="pos dpos">adjective</span>
    <span class="epp-xref dxref C2">C2</span>
    <span class="uk dpron-i">
      <span class="region dreg">uk</span>
      <span class="pron dpron">/<span class="ipa dipa lpr-2 lc-3">rɪˈzɪl.i.ənt</span>/</span>
    </span>
    <span class="us dpron-i">
      <span class="region dreg">us</span>
      <span class="pron dpron">/<span class="ipa dipa lpr-2 lc-3">rɪˈzɪl.jənt</span>/</span>
    </span>
  </div>
  <div class="def-block ddef_block">
    <div class="def ddef_d db">able to be happy, successful, etc. again after something difficult or bad has happened: </div>
    <div class="examp dexamp">
      <span class="eg deg">She's a resilient girl - she won't be unhappy for long.</span>
    </div>
  </div>
</div>
<amp-audio id="audio1"><source src="/media/english/uk_pron/u/ukr/ukres/ukresid009.mp3" type="audio/mpeg"></amp-audio>
<amp-audio id="audio2"><source src="/media/english/us_pron/r/res/resil/resilient.mp3" type="audio/mpeg"></amp-audio>
</body>
</html>
"""

SAMPLE_CAMBRIDGE_HTML_NO_CEFR = """
<html>
<body>
<div class="entry-body__el">
  <div class="pos-header dpos-h">
    <span class="pos dpos">noun</span>
    <span class="uk dpron-i">
      <span class="ipa dipa lpr-2 lc-3">ˈsɛr.ən.dɪp.ɪ.ti</span>
    </span>
  </div>
  <div class="def-block ddef_block">
    <div class="def ddef_d db">the fact of finding interesting things by chance: </div>
  </div>
</div>
</body>
</html>
"""

SAMPLE_CAMBRIDGE_HTML_EMPTY = """
<html><body><div>No dictionary entry found</div></body></html>
"""


class CambridgeParserTest(TestCase):
    def setUp(self):
        self.fetcher = EnhancedCambridgeAudioFetcher()

    def test_parse_word_data_full(self):
        tree = html.fromstring(SAMPLE_CAMBRIDGE_HTML)
        result = self.fetcher._parse_word_data(tree, "resilient")

        self.assertIsNotNone(result)
        self.assertEqual(result.word, "resilient")
        self.assertEqual(result.phonetic_uk, "/rɪˈzɪl.i.ənt/")
        self.assertEqual(result.phonetic_us, "/rɪˈzɪl.jənt/")
        self.assertEqual(result.part_of_speech, "adjective")
        self.assertEqual(result.cefr_level, "C2")
        self.assertIn("able to be happy", result.definition_en)
        self.assertIn("resilient girl", result.example_en)
        self.assertEqual(result.source, "cambridge")
        self.assertIn("/uk_pron/", result.audio_uk)
        self.assertIn("/us_pron/", result.audio_us)

    def test_parse_word_data_no_cefr(self):
        tree = html.fromstring(SAMPLE_CAMBRIDGE_HTML_NO_CEFR)
        result = self.fetcher._parse_word_data(tree, "serendipity")

        self.assertIsNotNone(result)
        self.assertEqual(result.word, "serendipity")
        self.assertEqual(result.cefr_level, "")
        self.assertEqual(result.part_of_speech, "noun")
        self.assertIn("finding interesting things", result.definition_en)

    def test_parse_word_data_empty_page(self):
        tree = html.fromstring(SAMPLE_CAMBRIDGE_HTML_EMPTY)
        result = self.fetcher._parse_word_data(tree, "xyznotaword")

        self.assertIsNone(result)

    def test_parse_word_data_strips_trailing_colon(self):
        tree = html.fromstring(SAMPLE_CAMBRIDGE_HTML)
        result = self.fetcher._parse_word_data(tree, "resilient")

        self.assertFalse(result.definition_en.endswith(":"))
        self.assertFalse(result.definition_en.endswith(": "))


class CambridgeFetchWordDataTest(TestCase):
    def setUp(self):
        self.fetcher = EnhancedCambridgeAudioFetcher()

    @patch.object(EnhancedCambridgeAudioFetcher, '_rate_limit')
    @patch('vocabulary.audio_service.cache')
    @patch('vocabulary.audio_service.requests.Session.get')
    def test_fetch_word_data_success(self, mock_get, mock_cache, mock_rate_limit):
        mock_cache.get.return_value = None
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = SAMPLE_CAMBRIDGE_HTML.encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = self.fetcher.fetch_word_data("resilient")

        self.assertIsNotNone(result)
        self.assertEqual(result.word, "resilient")
        self.assertEqual(result.phonetic_uk, "/rɪˈzɪl.i.ənt/")
        mock_cache.set.assert_called_once()

    @patch('vocabulary.audio_service.cache')
    def test_fetch_word_data_cache_hit(self, mock_cache):
        cached_data = CambridgeWordData(
            word="resilient",
            phonetic_uk="/rɪˈzɪl.i.ənt/",
            definition_en="able to recover",
            part_of_speech="adjective",
            cefr_level="C2",
        )
        mock_cache.get.return_value = cached_data

        result = self.fetcher.fetch_word_data("resilient")

        self.assertEqual(result.word, "resilient")
        self.assertEqual(result.phonetic_uk, "/rɪˈzɪl.i.ənt/")

    @patch.object(EnhancedCambridgeAudioFetcher, '_rate_limit')
    @patch('vocabulary.audio_service.cache')
    @patch('vocabulary.audio_service.requests.Session.get')
    def test_fetch_word_data_network_error(self, mock_get, mock_cache, mock_rate_limit):
        mock_cache.get.return_value = None
        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        result = self.fetcher.fetch_word_data("resilient")

        self.assertIsNone(result)
