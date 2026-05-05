# Cambridge-First Pipeline + LLM Translation — Design Spec

## Overview

Upgrade the `/add` word auto-fill pipeline to use Cambridge Dictionary as the primary data source (phonetic, definition, audio, CEFR level) via a single HTTP request, and replace Google Translate with LLM-powered Vietnamese translation.

## Current State

- **Phonetic**: `dictionaryapi.dev` — doesn't match UK audio from Cambridge
- **Audio**: Cambridge Dictionary scrape via `EnhancedCambridgeAudioFetcher` — working
- **Definition EN**: `dictionaryapi.dev`
- **Definition VI**: `deep-translator` (GoogleTranslator) — word-level, no context
- **CEFR level**: Not shown in `/add` flow (model field exists but not populated here)

## Architecture

### Approach: Extend existing `EnhancedCambridgeAudioFetcher`

Reuse the existing class's HTTP session, headers, rate-limiting, and retry logic. Add a new method `fetch_word_data()` that parses additional fields from the same HTML response already fetched for audio. This maintains SRP ("extract data from Cambridge HTML") and guarantees a single HTTP request per word.

### File Changes

| Component | File | Change |
|---|---|---|
| Cambridge scraper | `vocabulary/audio_service.py` | Add `CambridgeWordData` dataclass + `fetch_word_data()` + `_parse_word_data()` |
| LLM translator | `vocabulary/llm_translator.py` (new) | `BaseLLMTranslator` ABC + `LiteLLMTranslator` + `TranslationResult` dataclass |
| Orchestrator | `vocabulary/word_details_service.py` | Rewrite `get_word_details()` as Cambridge-first orchestrator with fallback |
| API | `vocabulary/views.py` | Add `cefr_level` to `save_flashcards` defaults |
| Frontend | `vocabulary/templates/vocabulary/add_flashcard.html` | Use flat fields, CEFR badge, remove translate API call |
| DB | No migration needed | `cefr_level` and `part_of_speech` already exist on `Flashcard` model |

## Detailed Design

### 1. Cambridge Scraper — `audio_service.py`

**New dataclass:**

```python
@dataclass
class CambridgeWordData:
    word: str
    phonetic_uk: str          # "/rɪˈzɪl.i.ənt/"
    phonetic_us: str          # "/rɪˈzɪl.jənt/"
    audio_uk: str             # URL mp3
    audio_us: str             # URL mp3
    definition_en: str        # first definition from primary POS
    part_of_speech: str       # "adjective"
    cefr_level: str           # "C1"
    example_en: str           # first example sentence
    source: str = "cambridge"
```

**New methods on `EnhancedCambridgeAudioFetcher`:**

- `fetch_word_data(word: str) -> CambridgeWordData | None` — public, fetches page + calls parser
- `_parse_word_data(tree, word: str) -> CambridgeWordData | None` — private, pure parse, no I/O

**XPath selectors:**

| Field | XPath |
|---|---|
| `phonetic_uk` | `//span[@class='uk dpron-i']//span[@class='ipa dipa lpr-2 lc-3']` |
| `phonetic_us` | `//span[@class='us dpron-i']//span[@class='ipa dipa lpr-2 lc-3']` |
| `definition_en` | `//div[@class='def ddef_d db']` |
| `part_of_speech` | `//span[@class='pos dpos']` |
| `cefr_level` | `//span[contains(@class,'epp-xref')]` or `//span[@class='dxref']` |
| `example_en` | `//span[@class='eg deg']` |

Audio parsing reuses existing `extract_audio_from_multiple_selectors()` logic.

Existing method `fetch_multiple_audio_sources()` is unchanged — no breaking changes.

### 2. LLM Translator — `llm_translator.py` (new file)

**Abstract base:**

```python
class BaseLLMTranslator(ABC):
    @abstractmethod
    def translate_definition(self, word_data: CambridgeWordData) -> TranslationResult: ...
```

**`TranslationResult` dataclass:**

```python
@dataclass
class TranslationResult:
    definition_vi: str       # full Vietnamese translation
    short_meaning_vi: str    # 1-3 word core meaning
    source: str              # "llm" or "google_translate"
```

**`LiteLLMTranslator(BaseLLMTranslator)` implementation:**

- Uses `settings.LLM_URL`, `settings.LLM_MODEL`, `settings.LLM_API_KEY`
- Calls litellm endpoint via `requests.post()` (same pattern as `image_service.py`)
- Prompt includes: word, part_of_speech, definition_en, example_en, cefr_level
- Requests JSON response: `{"definition_vi": "...", "short_meaning_vi": "..."}`
- On failure: logs warning, falls back to `GoogleTranslator(source='auto', target='vi')` from deep-translator
- Fallback result has `source: "google_translate"`

**Caching:**

- Key: `llm_translation:{word}:{md5(definition_en)[:8]}`
- Timeout: 7 days
- Checks cache before calling LLM
- Caches both LLM and fallback results

### 3. Orchestrator — `word_details_service.py`

**Rewritten `get_word_details(word)` flow:**

```
1. Try Cambridge → fetch_word_data(word) → CambridgeWordData
2. If Cambridge fails → fallback to dictionaryapi.dev (existing logic extracted to _fetch_from_dictionary_api)
3. Translate via LiteLLMTranslator.translate_definition()
4. Build and return unified response dict
```

**Response schema (new flat fields + backward compat):**

```json
{
    "word": "resilient",
    "phonetic": "/rɪˈzɪl.i.ənt/",
    "phonetic_us": "/rɪˈzɪl.jənt/",
    "phonetic_source": "cambridge_uk",
    "audio_url": "https://dictionary.cambridge.org/...mp3",
    "definition_en": "able to quickly return to a previous good condition",
    "definition_vi": "kiên cường, có khả năng phục hồi nhanh chóng",
    "short_meaning_vi": "kiên cường",
    "part_of_speech": "adjective",
    "cefr_level": "C1",
    "example_en": "Resilient economies survived the recession.",
    "source": "cambridge",

    "phonetics": [{"text": "/rɪˈzɪl.i.ənt/", "audio": "...mp3"}],
    "meanings": [{"part_of_speech": "adjective", "definitions": [{"en": "...", "example": "..."}]}]
}
```

Backward compat fields (`phonetics`, `meanings`) ensure existing FE code doesn't break during transition.

**Existing `get_cambridge_british_audio(word)` function:** Kept but not called by new flow. Other endpoints (audio fetch APIs) may still use it.

### 4. API Endpoint — `views.py`

- `get_word_details_api` (line 896): No change needed — it just proxies `get_word_details()`.
- `translate_to_vietnamese` (line 1273): Kept (not deleted), but no longer called by `/add` flow.
- `save_flashcards` (line 921): Add `cefr_level` to the `defaults` dict passed to `update_or_create`.

### 5. Frontend — `add_flashcard.html`

**`updateCardUI(card, data)` changes:**

- Use flat fields with fallback: `data.phonetic || data.phonetics?.find(...)?.text`
- Use `data.definition_vi` directly instead of calling `translateToVietnamese()`
- Remove the `translateToVietnamese()` call from `updateCardUI`
- Definition suggestion dropdown still populated from `data.meanings` if available

**CEFR Badge:**

- HTML: pill-shaped `<div class="cefr-badge">` in flashcard header, right side
- Color-coded by level: A1=#58CC02, A2=#89E219, B1=#FFC800, B2=#FF9600, C1=#FF4B4B, C2=#8B0000
- Tooltip on hover showing level description (e.g., "C1 - Advanced")
- CSS `fadeIn` animation (0.3s ease-in) when populated
- Hidden when no CEFR data available

**Part of speech display:** Small italic text next to phonetic in `.auto-info` area.

**Save flow:** Append `cefr_level` from badge `dataset.level` to FormData.

### 6. Error Handling

Cascade strategy — each layer fails independently:

```
Cambridge fail → log warning → fallback to dictionaryapi.dev → if also fail → return error
LLM fail → log warning → fallback to GoogleTranslator → if also fail → definition_vi = ""
```

### 7. Caching

| Data | Cache Key | Timeout |
|---|---|---|
| Cambridge word data | `cambridge_word:{word}` | 24 hours |
| LLM translation | `llm_translation:{word}:{md5(def)[:8]}` | 7 days |
| FE in-memory | `wordApiCache` (JS object) | Per session |

### 8. Logging

- Use `logging.getLogger(__name__)` consistently
- Migrate existing `print()` calls to `logger`
- `info`: successful operations with word + source
- `warning`: fallback triggered with original error
- `error`: both primary and fallback failed

## Not In Scope

- Migrating other services to the new Cambridge data (study flow, review flow)
- Removing `dictionaryapi.dev` dependency entirely (kept as fallback)
- Deleting `translate_to_vietnamese` endpoint (may be used elsewhere in future)
- Restructuring into `services/` subdirectory (keeping flat module structure)
