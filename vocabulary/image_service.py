import base64
import requests
import urllib3
from django.conf import settings
from django.core.cache import cache

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _build_result(
    image_b64: str,
    provider: str,
    model: str,
    source: str,
    fallback_from: str | None = None,
) -> dict:
    provider_label = provider.replace('_', ' ').title()
    model_label = model or 'unknown-model'
    return {
        'image_b64': image_b64,
        'provider': provider,
        'model': model,
        'source': source,
        'provider_label': provider_label,
        'model_label': model_label,
        'engine_label': f'{provider_label} / {model_label}',
        'fallback_from': fallback_from,
        'fallback_used': bool(fallback_from),
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


def _extract_b64_image(data: dict, verify: bool) -> str | None:
    image_items = data.get('data') or []
    if not image_items:
        return None

    image_data = image_items[0]
    if 'b64_json' in image_data:
        return image_data['b64_json']

    if 'url' in image_data:
        img_response = requests.get(image_data['url'], timeout=30, verify=verify)
        img_response.raise_for_status()
        return base64.b64encode(img_response.content).decode('utf-8')

    return None


def _generate_with_openai_compatible_api(
    *,
    provider: str,
    url: str,
    model: str,
    api_key: str,
    prompt: str,
    timeout: int,
    verify: bool,
) -> dict | None:
    if not url or not model or not api_key:
        return None

    response = requests.post(
        url,
        json={
            'model': model,
            'prompt': prompt,
            'n': 1,
            'size': '1024x1024',
            'response_format': 'b64_json',
        },
        headers={'Authorization': f'Bearer {api_key}'},
        timeout=timeout,
        verify=verify,
    )
    response.raise_for_status()
    b64 = _extract_b64_image(response.json(), verify=verify)
    if not b64:
        return None

    return _build_result(b64, provider, model, 'generated')


def _generate_with_gemini(prompt: str) -> dict | None:
    return _generate_with_openai_compatible_api(
        provider='gemini',
        url=getattr(settings, 'GEMINI_IMAGE_URL', ''),
        model=getattr(settings, 'GEMINI_IMAGE_MODEL', ''),
        api_key=getattr(settings, 'GEMINI_API_KEY', ''),
        prompt=prompt,
        timeout=getattr(settings, 'GEMINI_IMAGE_TIMEOUT', getattr(settings, 'LLM_IMAGE_TIMEOUT', 60)),
        verify=True,
    )


def _generate_with_fallback_provider(prompt: str, fallback_from: str | None = None) -> dict | None:
    result = _generate_with_openai_compatible_api(
        provider='fallback_provider',
        url=settings.LLM_IMAGE_URL,
        model=settings.LLM_IMAGE_MODEL,
        api_key=settings.LLM_API_KEY,
        prompt=prompt,
        timeout=settings.LLM_IMAGE_TIMEOUT,
        verify=False,
    )

    if not result:
        return None

    if not fallback_from:
        return result

    return {
        **result,
        'fallback_from': fallback_from,
        'fallback_used': True,
    }


def generate_word_image_result(word: str, definition: str = '') -> dict | None:
    """
    Generate an illustrative image for a vocabulary word using Gemini first,
    then fall back to the existing image generation provider.
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
                'fallback_used': bool(cached.get('fallback_from')),
            }

        if isinstance(cached, str):
            return _build_result(cached, 'cache', 'cached-image', 'cache')

    prompt = _build_prompt(word, definition)

    try:
        result = None

        gemini_failed = False

        try:
            result = _generate_with_gemini(prompt)
        except Exception as exc:
            gemini_failed = True
            print(f"[WARNING] Gemini image generation failed for '{word}': {exc}")

        if not result:
            result = _generate_with_fallback_provider(
                prompt,
                fallback_from='gemini' if gemini_failed or getattr(settings, 'GEMINI_API_KEY', '') else None,
            )

        if not result:
            return None

        cache.set(cache_key, result, timeout=settings.CACHE_TIMEOUTS.get('generated_image', 60 * 60 * 24 * 7))
        return result

    except Exception as e:
        print(f"[WARNING] Image generation failed for '{word}': {e}")
        return None


def generate_word_image(word: str, definition: str = '') -> str | None:
    result = generate_word_image_result(word, definition)
    if not result:
        return None

    return result['image_b64']
