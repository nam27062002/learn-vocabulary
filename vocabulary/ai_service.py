import re
import json
import requests
from django.conf import settings
from django.core.cache import cache


def get_word_examples(word: str) -> list[str]:
    """
    Return 5 example sentences for `word` using the local LM Studio instance.
    Results are cached for 24 hours to avoid redundant LLM calls.
    Raises requests.exceptions.ConnectionError if LM Studio is unreachable.
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
        settings.LM_STUDIO_URL,
        json={
            'model': settings.LM_STUDIO_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 600,
        },
        timeout=settings.LM_STUDIO_TIMEOUT,
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
