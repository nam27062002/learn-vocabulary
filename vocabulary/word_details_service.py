import logging

import requests

from .audio_service import EnhancedCambridgeAudioFetcher, CambridgeWordData
from .llm_translator import LiteLLMTranslator, TranslationResult

logger = logging.getLogger(__name__)

_cambridge_fetcher = EnhancedCambridgeAudioFetcher()
_translator = LiteLLMTranslator()


def _generate_example_llm(word: str, definition_en: str) -> str:
    """Generate an example sentence for the word via LLM. Returns empty string on failure."""
    try:
        import requests as _requests
        from django.conf import settings as _settings
        response = _requests.post(
            _settings.LLM_URL,
            json={
                "model": _settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an English teacher. Respond with exactly one natural example sentence and nothing else. No quotation marks."},
                    {"role": "user", "content": f"Write one natural English example sentence for the word '{word}' meaning: {definition_en}"},
                ],
                "temperature": 0.7,
                "max_tokens": 80,
            },
            headers={"Authorization": f"Bearer {_settings.LLM_API_KEY}"},
            timeout=_settings.LLM_TIMEOUT,
            verify=False,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"LLM example generation failed for '{word}': {e}")
        return ""


def _enrich_example(word: str, result: dict) -> None:
    """Add example_sentence and example_source to result dict in-place."""
    cambridge_example = result.get("example_en", "")
    if cambridge_example:
        result["example_sentence"] = cambridge_example
        result["example_source"] = "cambridge"
    else:
        generated = _generate_example_llm(word, result.get("definition_en", ""))
        result["example_sentence"] = generated
        result["example_source"] = "llm" if generated else ""


def get_word_details(word: str) -> dict:
    """Fetch word details using Cambridge Dictionary first, with dictionaryapi.dev fallback."""
    if not word or not word.strip():
        return {"error": "No word provided"}

    word = word.strip()

    cambridge_data = _fetch_from_cambridge(word)
    if cambridge_data:
        translation = _translate(cambridge_data)
        result = _build_cambridge_response(cambridge_data, translation)
        _enrich_example(word, result)
        return result

    fallback_data = _fetch_from_dictionary_api(word)
    if fallback_data:
        translation = _translate_fallback(word, fallback_data)
        result = _build_fallback_response(fallback_data, translation)
        _enrich_example(word, result)
        return result

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
