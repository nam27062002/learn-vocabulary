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
