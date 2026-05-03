import base64
import requests
import urllib3
from django.conf import settings
from django.core.cache import cache

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def generate_word_image(word: str, definition: str = '') -> str | None:
    """
    Generate an illustrative image for a vocabulary word using the image generation API.
    Returns base64-encoded PNG data, or None on failure.
    Results are cached for 7 days.
    """
    cache_key = f'ai_word_image:{word.lower()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    context = f"'{word}'"
    if definition:
        context += f" which means '{definition}'"

    prompt = (
        f"A simple, clean, colorful illustration representing the English word {context}. "
        f"Flat design style, educational, suitable as a vocabulary flashcard image. "
        f"No text or letters in the image."
    )

    try:
        response = requests.post(
            settings.LLM_IMAGE_URL,
            json={
                'model': settings.LLM_IMAGE_MODEL,
                'prompt': prompt,
                'n': 1,
                'size': '1024x1024',
            },
            headers={'Authorization': f'Bearer {settings.LLM_API_KEY}'},
            timeout=settings.LLM_IMAGE_TIMEOUT,
            verify=False,
        )
        response.raise_for_status()
        data = response.json()

        image_data = data['data'][0]
        if 'b64_json' in image_data:
            b64 = image_data['b64_json']
        elif 'url' in image_data:
            img_response = requests.get(image_data['url'], timeout=30, verify=False)
            img_response.raise_for_status()
            b64 = base64.b64encode(img_response.content).decode('utf-8')
        else:
            return None

        cache.set(cache_key, b64, timeout=settings.CACHE_TIMEOUTS.get('generated_image', 60 * 60 * 24 * 7))
        return b64

    except Exception as e:
        print(f"[WARNING] Image generation failed for '{word}': {e}")
        return None
