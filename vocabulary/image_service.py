import json
import logging
import time
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


def _build_result(image_b64: str, provider: str, model: str, source: str) -> dict:
    provider_label = 'Stable Diffusion' if provider == 'sd_webui' else provider.replace('_', ' ').title()
    model_label = model or 'unknown-model'
    return {
        'image_b64': image_b64,
        'provider': provider,
        'model': model,
        'source': source,
        'provider_label': provider_label,
        'model_label': model_label,
        'engine_label': f'{provider_label} / {model_label}',
    }


def _build_prompt(word: str, definition: str = '') -> str:
    context = f"'{word}'"
    if definition:
        context += f" which means '{definition}'"

    return (
        f"A simple, clean, colorful illustration representing the English word {context}. "
        f"Flat design style, educational, suitable as a vocabulary flashcard image. "
        f"No text or letters in the image."
    )


def _generate_with_sd_webui(prompt: str) -> dict | None:
    url = settings.SD_WEBUI_URL
    if not url:
        return None

    response = requests.post(
        f'{url.rstrip("/")}/sdapi/v1/txt2img',
        json={
            'prompt': prompt,
            'negative_prompt': 'text, letters, watermark, signature',
            'steps': 25,
            'width': 1024,
            'height': 1024,
        },
        timeout=settings.LLM_IMAGE_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()

    images = data.get('images') or []
    if not images:
        return None

    model = 'stable-diffusion'
    try:
        info = json.loads(data.get('info', '{}'))
        model = info.get('sd_model_name') or model
    except (ValueError, TypeError):
        pass

    return _build_result(images[0], 'sd_webui', model, 'generated')


def generate_word_image_result(word: str, definition: str = '') -> dict | None:
    """
    Generate an illustrative image for a vocabulary word using a local
    Stable Diffusion WebUI (AUTOMATIC1111) instance.
    Returns image data plus provider metadata, or None on failure.
    Results are cached for 7 days.
    """
    cache_key = f'ai_word_image:{word.lower()}'
    cached = cache.get(cache_key)
    if cached is not None:
        if isinstance(cached, dict) and cached.get('image_b64'):
            return {
                **cached,
                'source': 'cache',
            }

        if isinstance(cached, str):
            return _build_result(cached, 'cache', 'cached-image', 'cache')

    prompt = _build_prompt(word, definition)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = _generate_with_sd_webui(prompt)

            if not result:
                logger.warning(f"No image returned for '{word}' (attempt {attempt}/{MAX_RETRIES})")
            else:
                cache.set(cache_key, result, timeout=settings.CACHE_TIMEOUTS.get('generated_image', 60 * 60 * 24 * 7))
                return result

        except Exception as e:
            logger.warning(f"Image generation failed for '{word}' (attempt {attempt}/{MAX_RETRIES}): {e}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF_SECONDS)

    logger.error(f"Image generation failed for '{word}' after {MAX_RETRIES} attempts")
    return None


def generate_word_image(word: str, definition: str = '') -> str | None:
    result = generate_word_image_result(word, definition)
    if not result:
        return None

    return result['image_b64']
