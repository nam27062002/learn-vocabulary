# Cambridge-First Pipeline + LLM Translation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace dictionaryapi.dev with Cambridge Dictionary scraping for phonetic/definition/CEFR data, and replace Google Translate with LLM-powered Vietnamese translation in the `/add` flow.

**Architecture:** Extend `EnhancedCambridgeAudioFetcher` with a new `fetch_word_data()` method that parses phonetic, definition, POS, CEFR level, and examples from the same HTML response already fetched for audio. Create a new `llm_translator.py` module with an abstract translator interface and a LiteLLM implementation. Refactor `word_details_service.py` into an orchestrator that tries Cambridge first, falls back to dictionaryapi.dev, then translates via LLM.

**Tech Stack:** Python 3.14, Django 5.x, lxml (XPath), requests, deep-translator (fallback), litellm proxy (Claude Haiku)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `vocabulary/audio_service.py` | Modify (lines 10-11, 164-352, 354-356) | Add `CambridgeWordData` dataclass, `fetch_word_data()` and `_parse_word_data()` methods |
| `vocabulary/llm_translator.py` | **Create** | `BaseLLMTranslator` ABC, `TranslationResult` dataclass, `LiteLLMTranslator` implementation |
| `vocabulary/word_details_service.py` | Rewrite (lines 64-140) | Cambridge-first orchestrator with dictionaryapi.dev fallback |
| `vocabulary/views.py` | Modify (line 964-968) | Add `cefr_level` to `save_flashcards` defaults |
| `vocabulary/templates/vocabulary/add_flashcard.html` | Modify (lines 1014-1016, 1087-1093, 1382-1469, 2259-2264) | CEFR badge HTML/CSS/JS, use flat fields, remove translate API call |
| `vocabulary/tests_cambridge_scraper.py` | **Create** | Unit tests for Cambridge HTML parser |
| `vocabulary/tests_llm_translator.py` | **Create** | Unit tests for LLM translator |
| `vocabulary/tests_word_details_service.py` | **Create** | Integration tests for orchestrator |

---

## Verified XPath Selectors (tested against live Cambridge HTML)

These selectors were verified against `resilient` (C2) and `happy` (A1):

| Field | XPath | Notes |
|---|---|---|
| UK Phonetic | `//span[contains(@class,"uk dpron-i")]//span[contains(@class,"ipa")]` | Returns text without `/` slashes — add them |
| US Phonetic | `//span[contains(@class,"us dpron-i")]//span[contains(@class,"ipa")]` | Same |
| Definition EN | `//div[contains(@class,"def ddef_d")]` | First element = primary definition |
| Part of Speech | `//span[contains(@class,"pos dpos")]` | First element = primary POS |
| CEFR Level | `//span[contains(@class,"epp-xref")]` | Text is "A1", "C2" etc. Also in class: `epp-xref dxref C2` |
| Example EN | `//span[contains(@class,"eg deg")]` | First element = primary example |
| Audio UK | `//*[@id="audio1"]/source[1]` | `src` is relative path, needs `urljoin` with base URL |
| Audio US | `//*[@id="audio2"]/source[1]` | Same |

---

## Task 1: Add `CambridgeWordData` dataclass to `audio_service.py`

**Files:**
- Modify: `vocabulary/audio_service.py:10-16`

- [ ] **Step 1: Add the dataclass after existing `AudioOption`**

In `vocabulary/audio_service.py`, after the `AudioOption` dataclass (line 22), add:

```python
@dataclass
class CambridgeWordData:
    """Complete word data scraped from Cambridge Dictionary in a single request."""
    word: str
    phonetic_uk: str = ""
    phonetic_us: str = ""
    audio_uk: str = ""
    audio_us: str = ""
    definition_en: str = ""
    part_of_speech: str = ""
    cefr_level: str = ""
    example_en: str = ""
    source: str = "cambridge"
```

- [ ] **Step 2: Verify import**

Run:
```bash
.venv\Scripts\python.exe -c "from vocabulary.audio_service import CambridgeWordData; print(CambridgeWordData(word='test'))"
```
Expected: `CambridgeWordData(word='test', phonetic_uk='', ...)`

- [ ] **Step 3: Commit**

```bash
git add vocabulary/audio_service.py
git commit -m "feat: add CambridgeWordData dataclass to audio_service"
```

---

## Task 2: Add `_parse_word_data()` to `EnhancedCambridgeAudioFetcher`

**Files:**
- Modify: `vocabulary/audio_service.py:164-352`
- Create: `vocabulary/tests_cambridge_scraper.py`

- [ ] **Step 1: Write tests for the parser**

Create `vocabulary/tests_cambridge_scraper.py`:

```python
from django.test import TestCase
from unittest.mock import patch, MagicMock
from lxml import html
from vocabulary.audio_service import EnhancedCambridgeAudioFetcher, CambridgeWordData


SAMPLE_CAMBRIDGE_HTML = """
<html>
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
.venv\Scripts\python.exe manage.py test vocabulary.tests_cambridge_scraper -v 2
```
Expected: FAIL — `_parse_word_data` not defined yet.

- [ ] **Step 3: Implement `_parse_word_data()` on `EnhancedCambridgeAudioFetcher`**

Add this method to `EnhancedCambridgeAudioFetcher` class in `vocabulary/audio_service.py`, after the existing `validate_audio_urls` method (after line 351):

```python
    def _parse_word_data(self, tree, word: str) -> Optional[CambridgeWordData]:
        """Parse all word data fields from a Cambridge Dictionary HTML tree.

        Pure parse method — no I/O. Returns None if the page has no dictionary entry.
        """
        pos_elements = tree.xpath('//span[contains(@class,"pos dpos")]')
        if not pos_elements:
            return None

        def _first_text(xpath: str) -> str:
            elems = tree.xpath(xpath)
            return elems[0].text_content().strip() if elems else ""

        def _first_src(xpath: str) -> str:
            elems = tree.xpath(xpath)
            if elems:
                src = elems[0].get("src", "")
                if src.startswith("/"):
                    return urljoin(self.BASE_URL, src)
                return src
            return ""

        phonetic_uk_raw = _first_text('//span[contains(@class,"uk dpron-i")]//span[contains(@class,"ipa")]')
        phonetic_us_raw = _first_text('//span[contains(@class,"us dpron-i")]//span[contains(@class,"ipa")]')

        cefr = ""
        cefr_elems = tree.xpath('//span[contains(@class,"epp-xref")]')
        if cefr_elems:
            cefr = cefr_elems[0].text_content().strip()

        definition_raw = _first_text('//div[contains(@class,"def ddef_d")]')
        definition_en = definition_raw.rstrip(": ")

        return CambridgeWordData(
            word=word,
            phonetic_uk=f"/{phonetic_uk_raw}/" if phonetic_uk_raw else "",
            phonetic_us=f"/{phonetic_us_raw}/" if phonetic_us_raw else "",
            audio_uk=_first_src('//*[@id="audio1"]/source[1]'),
            audio_us=_first_src('//*[@id="audio2"]/source[1]'),
            definition_en=definition_en,
            part_of_speech=_first_text('//span[contains(@class,"pos dpos")]'),
            cefr_level=cefr,
            example_en=_first_text('//span[contains(@class,"eg deg")]'),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
.venv\Scripts\python.exe manage.py test vocabulary.tests_cambridge_scraper -v 2
```
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add vocabulary/audio_service.py vocabulary/tests_cambridge_scraper.py
git commit -m "feat: add _parse_word_data method to EnhancedCambridgeAudioFetcher"
```

---

## Task 3: Add `fetch_word_data()` public method with caching

**Files:**
- Modify: `vocabulary/audio_service.py:164-221`
- Modify: `vocabulary/tests_cambridge_scraper.py`

- [ ] **Step 1: Write test for `fetch_word_data` with caching**

Add to `vocabulary/tests_cambridge_scraper.py`:

```python
class CambridgeFetchWordDataTest(TestCase):
    def setUp(self):
        self.fetcher = EnhancedCambridgeAudioFetcher()

    @patch.object(EnhancedCambridgeAudioFetcher, '_rate_limit')
    @patch('vocabulary.audio_service.cache')
    @patch('vocabulary.audio_service.requests.Session.get')
    def test_fetch_word_data_success(self, mock_get, mock_cache, mock_rate_limit):
        mock_cache.get.return_value = None  # no cache hit
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
```

Also add this import at the top of the test file:

```python
import requests
from django.core.cache import cache
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
.venv\Scripts\python.exe manage.py test vocabulary.tests_cambridge_scraper.CambridgeFetchWordDataTest -v 2
```
Expected: FAIL — `fetch_word_data` not defined.

- [ ] **Step 3: Implement `fetch_word_data()`**

Add this method to `EnhancedCambridgeAudioFetcher`, after `_parse_word_data`:

```python
    def fetch_word_data(self, word: str) -> Optional[CambridgeWordData]:
        """Fetch complete word data from Cambridge Dictionary.

        Checks cache first. On cache miss, makes a single HTTP request and parses
        all fields (phonetic, audio, definition, POS, CEFR, example). Caches the
        result for 24 hours.

        Returns None if the word is not found or on network error.
        """
        if not word or not word.strip():
            return None

        word = word.strip().lower()
        cache_key = f"cambridge_word:{word}"
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"Cambridge cache hit for '{word}'")
            return cached

        url = self.DICTIONARY_URL.format(word=word)
        logger.info(f"Fetching word data from Cambridge for: {word}")

        for attempt in range(self.MAX_RETRIES):
            try:
                self._rate_limit()
                response = self.session.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()

                tree = html.fromstring(response.content)
                result = self._parse_word_data(tree, word)

                if result:
                    cache.set(cache_key, result, timeout=86400)
                    logger.info(f"Cambridge data cached for '{word}': POS={result.part_of_speech}, CEFR={result.cefr_level}")
                else:
                    logger.info(f"No dictionary entry found on Cambridge for '{word}'")

                return result

            except requests.exceptions.RequestException as e:
                logger.warning(f"Cambridge fetch failed for '{word}' (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Cambridge fetch failed for '{word}' after {self.MAX_RETRIES} attempts")

            except Exception as e:
                logger.error(f"Unexpected error fetching Cambridge data for '{word}': {e}")
                break

        return None
```

Also add this import at the top of `audio_service.py` (near line 9):

```python
from django.core.cache import cache
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
.venv\Scripts\python.exe manage.py test vocabulary.tests_cambridge_scraper -v 2
```
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add vocabulary/audio_service.py vocabulary/tests_cambridge_scraper.py
git commit -m "feat: add fetch_word_data with caching to Cambridge scraper"
```

---

## Task 4: Create `llm_translator.py` — dataclasses and interface

**Files:**
- Create: `vocabulary/llm_translator.py`
- Create: `vocabulary/tests_llm_translator.py`

- [ ] **Step 1: Write tests for LLM translator**

Create `vocabulary/tests_llm_translator.py`:

```python
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

        # Should fallback to Google Translate
        with patch('vocabulary.llm_translator.GoogleTranslator') as mock_google_cls:
            mock_google_instance = MagicMock()
            mock_google_instance.translate.return_value = "fallback translation"
            mock_google_cls.return_value = mock_google_instance

            result = self.translator.translate_definition(self.word_data)

        self.assertEqual(result.source, "google_translate")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
.venv\Scripts\python.exe manage.py test vocabulary.tests_llm_translator -v 2
```
Expected: FAIL — module `vocabulary.llm_translator` does not exist.

- [ ] **Step 3: Implement `llm_translator.py`**

Create `vocabulary/llm_translator.py`:

```python
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

import requests
from deep_translator import GoogleTranslator
from django.conf import settings
from django.core.cache import cache

if TYPE_CHECKING:
    from vocabulary.audio_service import CambridgeWordData

logger = logging.getLogger(__name__)

TRANSLATION_CACHE_TIMEOUT = 60 * 60 * 24 * 7  # 7 days


@dataclass
class TranslationResult:
    """Result of translating a word's definition to Vietnamese."""
    definition_vi: str
    short_meaning_vi: str
    source: str  # "llm" or "google_translate"


class BaseLLMTranslator(ABC):
    """Abstract interface for LLM-based translation."""

    @abstractmethod
    def translate_definition(self, word_data: 'CambridgeWordData') -> TranslationResult:
        ...


class LiteLLMTranslator(BaseLLMTranslator):
    """Translator using a litellm-compatible chat completions endpoint."""

    SYSTEM_PROMPT = (
        "You are a Vietnamese language expert. Translate English vocabulary to Vietnamese. "
        "Always respond with valid JSON only, no markdown, no extra text."
    )

    USER_PROMPT_TEMPLATE = (
        "Translate this English word and its definition to Vietnamese.\n\n"
        "Word: {word}\n"
        "Part of speech: {part_of_speech}\n"
        "English definition: {definition_en}\n"
        "Example: {example_en}\n"
        "CEFR Level: {cefr_level}\n\n"
        'Respond in JSON: {{"definition_vi": "...", "short_meaning_vi": "..."}}\n\n'
        "Rules:\n"
        "- definition_vi: natural Vietnamese translation of the definition, include the Vietnamese equivalent word(s)\n"
        "- short_meaning_vi: 1-3 Vietnamese words, the core meaning only\n"
        "- Do NOT transliterate, provide actual Vietnamese meaning"
    )

    def _build_cache_key(self, word_data: 'CambridgeWordData') -> str:
        def_hash = hashlib.md5(word_data.definition_en.encode()).hexdigest()[:8]
        return f"llm_translation:{word_data.word}:{def_hash}"

    def translate_definition(self, word_data: 'CambridgeWordData') -> TranslationResult:
        cache_key = self._build_cache_key(word_data)
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"Translation cache hit for '{word_data.word}'")
            return cached

        result = self._call_llm(word_data)
        if result is None:
            result = self._fallback_google_translate(word_data)

        cache.set(cache_key, result, timeout=TRANSLATION_CACHE_TIMEOUT)
        return result

    def _call_llm(self, word_data: 'CambridgeWordData') -> TranslationResult | None:
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            word=word_data.word,
            part_of_speech=word_data.part_of_speech,
            definition_en=word_data.definition_en,
            example_en=word_data.example_en,
            cefr_level=word_data.cefr_level,
        )

        try:
            response = requests.post(
                settings.LLM_URL,
                json={
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200,
                },
                headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                timeout=settings.LLM_TIMEOUT,
                verify=False,
            )
            response.raise_for_status()

            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            definition_vi = parsed.get("definition_vi", "")
            short_meaning_vi = parsed.get("short_meaning_vi", "")

            if not definition_vi:
                logger.warning(f"LLM returned empty definition_vi for '{word_data.word}'")
                return None

            logger.info(f"LLM translation success for '{word_data.word}'")
            return TranslationResult(
                definition_vi=definition_vi,
                short_meaning_vi=short_meaning_vi,
                source="llm",
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"LLM response parse error for '{word_data.word}': {e}")
            return None
        except Exception as e:
            logger.warning(f"LLM translation failed for '{word_data.word}': {e}")
            return None

    def _fallback_google_translate(self, word_data: 'CambridgeWordData') -> TranslationResult:
        try:
            text = word_data.word
            translated = GoogleTranslator(source="auto", target="vi").translate(text)
            logger.info(f"Google Translate fallback for '{word_data.word}': {translated}")
            return TranslationResult(
                definition_vi=translated or "",
                short_meaning_vi=translated or "",
                source="google_translate",
            )
        except Exception as e:
            logger.error(f"Google Translate fallback also failed for '{word_data.word}': {e}")
            return TranslationResult(
                definition_vi="",
                short_meaning_vi="",
                source="google_translate",
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
.venv\Scripts\python.exe manage.py test vocabulary.tests_llm_translator -v 2
```
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add vocabulary/llm_translator.py vocabulary/tests_llm_translator.py
git commit -m "feat: add LLM translator with fallback to Google Translate"
```

---

## Task 5: Rewrite `word_details_service.py` as Cambridge-first orchestrator

**Files:**
- Rewrite: `vocabulary/word_details_service.py` (lines 64-140)
- Create: `vocabulary/tests_word_details_service.py`

- [ ] **Step 1: Write orchestrator tests**

Create `vocabulary/tests_word_details_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
.venv\Scripts\python.exe manage.py test vocabulary.tests_word_details_service -v 2
```
Expected: FAIL — the mocked functions don't exist yet.

- [ ] **Step 3: Rewrite `word_details_service.py`**

Replace the content of `vocabulary/word_details_service.py` with:

```python
import logging

import requests
from django.conf import settings

from .audio_service import EnhancedCambridgeAudioFetcher, CambridgeWordData
from .llm_translator import LiteLLMTranslator, TranslationResult

logger = logging.getLogger(__name__)

_cambridge_fetcher = EnhancedCambridgeAudioFetcher()
_translator = LiteLLMTranslator()


def get_word_details(word: str) -> dict:
    """Fetch word details using Cambridge Dictionary first, with dictionaryapi.dev fallback."""
    if not word or not word.strip():
        return {"error": "No word provided"}

    word = word.strip()

    cambridge_data = _fetch_from_cambridge(word)
    if cambridge_data:
        translation = _translate(cambridge_data)
        return _build_cambridge_response(cambridge_data, translation)

    fallback_data = _fetch_from_dictionary_api(word)
    if fallback_data:
        translation = _translate_fallback(word, fallback_data)
        return _build_fallback_response(fallback_data, translation)

    return {"error": f"Không tìm thấy từ '{word}'."}


def _fetch_from_cambridge(word: str) -> CambridgeWordData | None:
    try:
        return _cambridge_fetcher.fetch_word_data(word)
    except Exception as e:
        logger.warning(f"Cambridge fetch error for '{word}': {e}")
        return None


def _translate(cambridge_data: CambridgeWordData) -> TranslationResult:
    try:
        return _translator.translate_definition(cambridge_data)
    except Exception as e:
        logger.warning(f"Translation error for '{cambridge_data.word}': {e}")
        return TranslationResult(definition_vi="", short_meaning_vi="", source="error")


def _translate_fallback(word: str, fallback_data: dict) -> TranslationResult:
    """Translate using fallback data by constructing a minimal CambridgeWordData."""
    first_meaning = (fallback_data.get("meanings") or [{}])[0]
    first_def = (first_meaning.get("definitions") or [{}])[0]

    synthetic = CambridgeWordData(
        word=word,
        definition_en=first_def.get("en", ""),
        part_of_speech=first_meaning.get("part_of_speech", ""),
        example_en=first_def.get("example", ""),
    )
    return _translate(synthetic)


def _fetch_from_dictionary_api(word: str) -> dict | None:
    """Fetch word data from dictionaryapi.dev as fallback."""
    api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list) or not data:
            return None

        word_data = data[0]
        if not isinstance(word_data, dict):
            return None

        from .audio_service import EnhancedCambridgeAudioFetcher as _Fetcher

        cambridge_audio = ""
        try:
            fetcher = _Fetcher()
            audio_options = fetcher.fetch_multiple_audio_sources(word)
            for option in audio_options:
                if option.is_valid:
                    label_lower = option.label.lower()
                    if "uk" in label_lower or "british" in label_lower:
                        cambridge_audio = option.url
                        break
                    if not cambridge_audio:
                        cambridge_audio = option.url
        except Exception as e:
            logger.warning(f"Cambridge audio fetch failed during fallback for '{word}': {e}")

        phonetics = []
        for p in word_data.get("phonetics", []):
            if isinstance(p, dict):
                phonetics.append({
                    "text": p.get("text", ""),
                    "audio": cambridge_audio or p.get("audio", ""),
                })

        meanings = []
        for m in word_data.get("meanings", []):
            if not isinstance(m, dict):
                continue
            definitions = []
            for d in m.get("definitions", []):
                if isinstance(d, dict):
                    definitions.append({
                        "en": d.get("definition", ""),
                        "example": d.get("example", ""),
                    })
            meanings.append({
                "part_of_speech": m.get("partOfSpeech", ""),
                "definitions": definitions,
            })

        return {
            "word": word_data.get("word", word),
            "phonetics": phonetics,
            "meanings": meanings,
        }

    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            logger.info(f"Word '{word}' not found on dictionaryapi.dev")
        else:
            logger.warning(f"dictionaryapi.dev HTTP error for '{word}': {e}")
        return None
    except Exception as e:
        logger.error(f"dictionaryapi.dev error for '{word}': {e}")
        return None


def _build_cambridge_response(data: CambridgeWordData, translation: TranslationResult) -> dict:
    return {
        "word": data.word,
        "phonetic": data.phonetic_uk,
        "phonetic_us": data.phonetic_us,
        "phonetic_source": "cambridge_uk" if data.phonetic_uk else "",
        "audio_url": data.audio_uk,
        "definition_en": data.definition_en,
        "definition_vi": translation.definition_vi,
        "short_meaning_vi": translation.short_meaning_vi,
        "part_of_speech": data.part_of_speech,
        "cefr_level": data.cefr_level,
        "example_en": data.example_en,
        "source": "cambridge",
        # Backward compat
        "phonetics": [{"text": data.phonetic_uk, "audio": data.audio_uk}],
        "meanings": [{
            "part_of_speech": data.part_of_speech,
            "definitions": [{"en": data.definition_en, "example": data.example_en}],
        }],
    }


def _build_fallback_response(fallback_data: dict, translation: TranslationResult) -> dict:
    first_phonetic = (fallback_data.get("phonetics") or [{}])[0]
    first_meaning = (fallback_data.get("meanings") or [{}])[0]
    first_def = (first_meaning.get("definitions") or [{}])[0]

    return {
        "word": fallback_data.get("word", ""),
        "phonetic": first_phonetic.get("text", ""),
        "phonetic_us": "",
        "phonetic_source": "dictionary_api",
        "audio_url": first_phonetic.get("audio", ""),
        "definition_en": first_def.get("en", ""),
        "definition_vi": translation.definition_vi,
        "short_meaning_vi": translation.short_meaning_vi,
        "part_of_speech": first_meaning.get("part_of_speech", ""),
        "cefr_level": "",
        "example_en": first_def.get("example", ""),
        "source": "dictionary_api",
        # Backward compat
        "phonetics": fallback_data.get("phonetics", []),
        "meanings": fallback_data.get("meanings", []),
    }


# Keep for backward compatibility — other endpoints may import this
def get_cambridge_british_audio(word: str) -> str:
    """Fetch British English audio URL from Cambridge Dictionary.

    Deprecated: use EnhancedCambridgeAudioFetcher.fetch_word_data() instead.
    """
    if not word or not word.strip():
        return ""

    try:
        data = _cambridge_fetcher.fetch_word_data(word)
        if data and data.audio_uk:
            return data.audio_uk
        if data and data.audio_us:
            return data.audio_us
    except Exception as e:
        logger.error(f"Error in get_cambridge_british_audio for '{word}': {e}")

    return ""
```

- [ ] **Step 4: Run orchestrator tests**

Run:
```bash
.venv\Scripts\python.exe manage.py test vocabulary.tests_word_details_service -v 2
```
Expected: All 3 tests PASS.

- [ ] **Step 5: Run existing tests to check for regressions**

Run:
```bash
.venv\Scripts\python.exe manage.py test vocabulary.tests -v 2
```
Expected: All existing tests still PASS.

- [ ] **Step 6: Commit**

```bash
git add vocabulary/word_details_service.py vocabulary/tests_word_details_service.py
git commit -m "feat: rewrite word_details_service as Cambridge-first orchestrator"
```

---

## Task 6: Update `save_flashcards` in `views.py` to persist `cefr_level`

**Files:**
- Modify: `vocabulary/views.py:964-983`

- [ ] **Step 1: Add `cefr_level` to defaults in `save_flashcards`**

In `vocabulary/views.py`, find the `defaults` dict in `save_flashcards` (around line 964):

Current:
```python
            defaults = {
                'phonetic': card_data.get('phonetic'),
                'part_of_speech': card_data.get('part_of_speech'),
                'audio_url': card_data.get('audio_url'),
                'deck': deck
            }
```

Replace with:
```python
            defaults = {
                'phonetic': card_data.get('phonetic'),
                'part_of_speech': card_data.get('part_of_speech'),
                'audio_url': card_data.get('audio_url'),
                'deck': deck,
            }
            
            cefr_from_frontend = card_data.get('cefr_level', '').strip()
            if cefr_from_frontend:
                defaults['cefr_level'] = cefr_from_frontend
                defaults['cefr_level_auto'] = True
```

Also update the CEFR auto-assignment block (around line 981-983). Change:
```python
            # Update CEFR level for new or updated flashcards
            if created or not flashcard.cefr_level:
                flashcard.update_cefr_level(save=True)
```

To:
```python
            if not flashcard.cefr_level:
                flashcard.update_cefr_level(save=True)
```

This ensures Cambridge-provided CEFR data takes priority over the heuristic-based classifier.

- [ ] **Step 2: Run existing tests**

Run:
```bash
.venv\Scripts\python.exe manage.py test vocabulary.tests -v 2
```
Expected: All PASS.

- [ ] **Step 3: Commit**

```bash
git add vocabulary/views.py
git commit -m "feat: persist CEFR level from frontend in save_flashcards"
```

---

## Task 7: Update frontend — CEFR badge HTML + CSS

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html:1014-1016` (flashcard header)
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html` (CSS section)

- [ ] **Step 1: Add CEFR badge HTML to flashcard header**

In `add_flashcard.html`, find the flashcard header (around line 1014-1016):

```html
      <div class="flashcard-header">
        <span class="card-number">1</span>
        <div class="actions">
```

Replace with:
```html
      <div class="flashcard-header">
        <span class="card-number">1</span>
        <div class="cefr-badge" style="display:none;" data-level="">
          <span class="cefr-text"></span>
          <span class="cefr-tooltip"></span>
        </div>
        <div class="actions">
```

- [ ] **Step 2: Add CEFR badge CSS**

In the `<style>` section of the template (before the closing `</style>` tag, around line 939), add:

```css
    .cefr-badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 10px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #fff;
      box-shadow: 0 1px 4px rgba(0,0,0,0.18);
      position: relative;
      cursor: default;
      opacity: 0;
      transition: opacity 0.3s ease-in;
      margin-left: auto;
      margin-right: 8px;
    }

    .cefr-badge.visible {
      opacity: 1;
    }

    .cefr-badge[data-level="A1"] { background: #58CC02; }
    .cefr-badge[data-level="A2"] { background: #89E219; color: #1a1a2e; }
    .cefr-badge[data-level="B1"] { background: #FFC800; color: #1a1a2e; }
    .cefr-badge[data-level="B2"] { background: #FF9600; }
    .cefr-badge[data-level="C1"] { background: #FF4B4B; }
    .cefr-badge[data-level="C2"] { background: #8B0000; }

    .cefr-tooltip {
      display: none;
      position: absolute;
      top: calc(100% + 6px);
      left: 50%;
      transform: translateX(-50%);
      background: #1a1a2e;
      color: #e0e0e0;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.7rem;
      font-weight: 400;
      white-space: nowrap;
      z-index: 10;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    .cefr-badge:hover .cefr-tooltip {
      display: block;
    }

    @media (max-width: 600px) {
      .cefr-badge {
        padding: 1px 7px;
        font-size: 0.65rem;
      }
    }
```

- [ ] **Step 3: Make flashcard-header a flex container (if not already)**

Check if `.flashcard-header` already has `display: flex; align-items: center;`. If not, update:

```css
    .flashcard-header {
      display: flex;
      align-items: center;
      /* ...existing styles... */
    }
```

- [ ] **Step 4: Commit**

```bash
git add vocabulary/templates/vocabulary/add_flashcard.html
git commit -m "feat: add CEFR badge HTML and CSS to flashcard cards"
```

---

## Task 8: Update frontend — JavaScript `updateCardUI` and save logic

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html:1382-1470` (updateCardUI)
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html:2253-2264` (save formData)

- [ ] **Step 1: Add CEFR descriptions constant**

In the JavaScript section, near the top of the `<script>` block (after the existing variable declarations like `wordApiCache`), add:

```javascript
    const CEFR_DESCRIPTIONS = {
        'A1': 'A1 - Beginner',
        'A2': 'A2 - Elementary',
        'B1': 'B1 - Intermediate',
        'B2': 'B2 - Upper-Intermediate',
        'C1': 'C1 - Advanced',
        'C2': 'C2 - Proficiency',
    };
```

- [ ] **Step 2: Update `updateCardUI` to use flat fields and CEFR badge**

Find the `updateCardUI` function (around line 1382). Replace the function body. The new version:

```javascript
    function updateCardUI(card, data) {
        const phoneticInput = card.querySelector(".phonetic-input");
        const autoInfo = card.querySelector(".auto-info");
        const autoPos = card.querySelector(".auto-pos");
        const autoAudio = card.querySelector(".auto-audio");
        const definitionTextarea = card.querySelector(".definition-textarea");
        const vietnameseTextarea = card.querySelector(".vietnamese-textarea");
        const definitionSuggestions = card.querySelector('.definition-suggestions');
        const cefrBadge = card.querySelector('.cefr-badge');

        // Reset previous state first
        resetCardUI(card);

        // Phonetic — prefer flat Cambridge field, fallback to array
        const phoneticText = data.phonetic || data.phonetics?.find(p => p.text)?.text || "";
        phoneticInput.value = phoneticText;

        if (autoInfo) {
            autoInfo.style.display = 'flex';
            autoInfo.classList.remove('inactive');
        }

        // Part of Speech — prefer flat field
        const partOfSpeech = data.part_of_speech || data.meanings?.[0]?.part_of_speech || "";
        if (autoPos) autoPos.textContent = partOfSpeech;

        // Audio — prefer flat field
        const audioUrl = data.audio_url || data.phonetics?.find(p => p.audio)?.audio || "";
        if (autoAudio) {
            autoAudio.dataset.audioUrl = audioUrl;
            autoAudio.innerHTML = audioUrl ? `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"></path></svg>
                <span>{{ manual_texts.listen }}</span>` : "";
        }
        if (autoInfo) autoInfo.style.display = "flex";

        // CEFR Badge
        if (cefrBadge) {
            if (data.cefr_level && CEFR_DESCRIPTIONS[data.cefr_level]) {
                cefrBadge.dataset.level = data.cefr_level;
                cefrBadge.querySelector('.cefr-text').textContent = data.cefr_level;
                cefrBadge.querySelector('.cefr-tooltip').textContent = CEFR_DESCRIPTIONS[data.cefr_level];
                cefrBadge.style.display = '';
                // Trigger fade-in animation
                requestAnimationFrame(() => cefrBadge.classList.add('visible'));
            } else {
                cefrBadge.style.display = 'none';
                cefrBadge.classList.remove('visible');
            }
        }

        // Vietnamese Definition — use LLM-translated field directly
        if (data.definition_vi) {
            vietnameseTextarea.value = data.definition_vi;
        }

        // Handle Definitions — still populate suggestion dropdown from meanings array
        definitionSuggestions.innerHTML = '';
        const allDefinitions = data.meanings?.flatMap(m => m.definitions.map(d => ({ ...d, part_of_speech: m.part_of_speech }))) || [];

        if (allDefinitions.length > 0) {
            allDefinitions.forEach(def => {
                const item = document.createElement('div');
                item.className = 'suggestion-item';
                item.innerHTML = `<span style="color:#b0b0ff;font-style:italic;">(${def.part_of_speech})</span> ${def.en}`;
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    definitionTextarea.value = def.en;
                    definitionSuggestions.style.display = 'none';
                    validateCard(card);
                });
                definitionSuggestions.appendChild(item);
            });

            definitionTextarea.addEventListener('focus', () => {
                if(definitionSuggestions.innerHTML !== ''){
                   definitionSuggestions.style.display = 'block';
                }
            });
            definitionTextarea.addEventListener('blur', () => {
                setTimeout(() => {
                    definitionSuggestions.style.display = 'none';
                }, 200);
            });

            // Auto-fill first English definition
            const firstDefinition = data.definition_en || allDefinitions[0].en;
            definitionTextarea.value = firstDefinition;

            // If no LLM translation was provided, leave Vietnamese empty for user
            if (!data.definition_vi) {
                vietnameseTextarea.value = "";
            }

        } else {
            definitionTextarea.value = data.definition_en || '';
            if (!data.definition_vi) {
                vietnameseTextarea.value = '';
            }
        }

        // Validate card after updating UI
        validateCard(card);

        // Auto-generate image (async, non-blocking)
        const termValue = card.querySelector('.term-input').value.trim();
        const firstDef = data.definition_en || data.meanings?.[0]?.definitions?.[0]?.en || '';
        generateImageForCard(termValue, firstDef, card);
    }
```

- [ ] **Step 3: Update `resetCardUI` to also reset CEFR badge**

Find the `resetCardUI` function (around line 1470). Add at the end of the function body:

```javascript
        // Reset CEFR badge
        const cefrBadge = card.querySelector('.cefr-badge');
        if (cefrBadge) {
            cefrBadge.style.display = 'none';
            cefrBadge.classList.remove('visible');
            cefrBadge.dataset.level = '';
            cefrBadge.querySelector('.cefr-text').textContent = '';
            cefrBadge.querySelector('.cefr-tooltip').textContent = '';
        }
```

- [ ] **Step 4: Update save FormData to include `cefr_level`**

Find the save logic (around line 2264, after the `audio_url` append):

```javascript
                formData.append(`flashcards-${idx}-audio_url`, card.querySelector('.auto-audio').dataset.audioUrl || '');
```

Add after it:
```javascript
                formData.append(`flashcards-${idx}-cefr_level`, card.querySelector('.cefr-badge')?.dataset?.level || '');
```

- [ ] **Step 5: Update `createNewCardForWord` to reset CEFR badge on cloned cards**

Find `createNewCardForWord` (around line 1895, after `resetCardUI(newCard);`). Add:

```javascript
            // Reset CEFR badge on cloned card
            const cefrBadge = newCard.querySelector('.cefr-badge');
            if (cefrBadge) {
                cefrBadge.style.display = 'none';
                cefrBadge.classList.remove('visible');
                cefrBadge.dataset.level = '';
            }
```

- [ ] **Step 6: Commit**

```bash
git add vocabulary/templates/vocabulary/add_flashcard.html
git commit -m "feat: update frontend JS for Cambridge data, CEFR badge, and LLM translation"
```

---

## Task 9: End-to-end manual test

**Files:** None (testing only)

- [ ] **Step 1: Start development server**

Run:
```bash
.venv\Scripts\python.exe manage.py runserver
```

- [ ] **Step 2: Test with an A1 word**

Navigate to `/add`. Type "happy" in the word input. Verify:
- Phonetic shows `/ˈhæp.i/` (Cambridge UK)
- CEFR badge shows "A1" with green (`#58CC02`) background
- English definition is from Cambridge (e.g., "feeling, showing, or causing pleasure or satisfaction")
- Vietnamese definition is filled by LLM (not just "vui vẻ" from Google Translate)
- Audio plays UK pronunciation

- [ ] **Step 3: Test with a C2 word**

Type "resilient". Verify:
- Phonetic shows `/rɪˈzɪl.i.ənt/`
- CEFR badge shows "C2" with dark red (`#8B0000`) background
- Tooltip on hover shows "C2 - Proficiency"

- [ ] **Step 4: Test caching**

Type "happy" again (or in another card). Check browser DevTools Network tab — should NOT see a new request to `/word-details/` if `wordApiCache` hits. Check Django logs — should see "Cambridge cache hit" if server-side cache hits.

- [ ] **Step 5: Test save flow**

Select a deck, fill in a word, verify all fields populate. Click Save. Check the database (admin panel or shell) that `cefr_level` is persisted on the `Flashcard` model.

- [ ] **Step 6: Test fallback (optional)**

If you want to test the fallback path, temporarily break the Cambridge URL (e.g., change `DICTIONARY_URL` to a bad URL) and verify dictionaryapi.dev data still loads.

- [ ] **Step 7: Run full test suite**

```bash
.venv\Scripts\python.exe manage.py test -v 2
```
Expected: All tests PASS.

- [ ] **Step 8: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: address issues found during end-to-end testing"
```
