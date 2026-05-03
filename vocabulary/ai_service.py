import re
import json
import requests
import urllib3
from django.conf import settings
from django.core.cache import cache

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_word_examples(word: str) -> list[str]:
    """
    Return 5 example sentences for `word` via the configured LLM proxy.
    Results are cached for 24 hours to avoid redundant LLM calls.
    """
    cache_key = f'ai_word_examples:{word.lower()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    prompt = (
        f'Give me exactly 5 natural English example sentences that use the word "{word}". '
        f'Each sentence should clearly show the meaning of "{word}" in context. '
        f'Return only a JSON array of 5 strings, no explanation. '
        f'Example format: ["Sentence 1.", "Sentence 2.", "Sentence 3.", "Sentence 4.", "Sentence 5."]'
    )

    response = requests.post(
        settings.LLM_URL,
        json={
            'model': settings.LLM_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 600,
        },
        headers={'Authorization': f'Bearer {settings.LLM_API_KEY}'},
        timeout=settings.LLM_TIMEOUT,
        verify=False,
    )
    response.raise_for_status()
    content = response.json()['choices'][0]['message']['content'].strip()

    # LLM may wrap the array in prose — extract the first JSON array found.
    match = re.search(r'\[.*?\]', content, re.DOTALL)
    if match:
        sentences = json.loads(match.group())
        sentences = [s for s in sentences if isinstance(s, str)][:5]
    else:
        # Fallback: treat each non-empty line as a sentence, strip leading numbering.
        sentences = [
            re.sub(r'^[\d.\-) ]+', '', line).strip()
            for line in content.splitlines()
            if line.strip()
        ][:5]

    cache.set(cache_key, sentences, timeout=60 * 60 * 24)
    return sentences


def get_vstep_suggestions(existing_words: list[str]) -> list[str]:
    """
    Return 20 VSTEP exam vocabulary words via the LLM proxy,
    excluding words the user already knows.
    Results are cached for 1 hour keyed by the sorted word set.
    """
    existing_lower = {w.lower() for w in existing_words}

    cache_key = f'vstep_suggestions:{hash(tuple(sorted(existing_lower)))}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    exclusion_text = ', '.join(existing_words[:500]) if existing_words else 'none'

    prompt = (
        'You are a VSTEP exam preparation expert. '
        'Give me exactly 40 English vocabulary words that are most commonly tested '
        'in VSTEP exams (levels B1 to C1).\n\n'
        'Rules:\n'
        '- Prioritize words by frequency of appearance in VSTEP exams (most common first)\n'
        '- Focus on academic and general English words used across Reading, Listening, Writing sections\n'
        '- Do NOT include any of these words the user already knows: '
        f'{exclusion_text}\n'
        '- Return ONLY a JSON array of 40 strings, no explanation\n'
        '- Example: ["phenomenon", "substantial", "prevalent"]'
    )

    response = requests.post(
        settings.LLM_URL,
        json={
            'model': settings.LLM_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 800,
        },
        headers={'Authorization': f'Bearer {settings.LLM_API_KEY}'},
        timeout=settings.LLM_TIMEOUT,
        verify=False,
    )
    response.raise_for_status()
    content = response.json()['choices'][0]['message']['content'].strip()

    match = re.search(r'\[.*?\]', content, re.DOTALL)
    if match:
        words = json.loads(match.group())
        words = [w for w in words if isinstance(w, str)]
    else:
        words = [
            re.sub(r'^[\d.\-) ]+', '', line).strip()
            for line in content.splitlines()
            if line.strip()
        ]

    result = [w for w in words if w.lower() not in existing_lower][:20]
    cache.set(cache_key, result, timeout=60 * 60)
    return result
