"""Tests for the api_audio_proxy view (Cambridge audio fallback chain)."""
from unittest.mock import patch

from django.test import TestCase, RequestFactory

from vocabulary import views


class FakeResponse:
    def __init__(self, status_code=200, content=b'', headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}

    def raise_for_status(self):
        import requests
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f'{self.status_code}')
        return None


class ApiAudioProxyTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.cambridge_url = (
            'https://dictionary.cambridge.org/media/english/'
            'us_pron/s/sum/summa/summarize.mp3'
        )
        self.user = self._login()

    def _request(self, url):
        request = self.factory.get('/api/audio-proxy/', {'url': url})
        request.user = self.user
        return request

    def _login(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(email='proxytester@example.com').first()
        if user is None:
            user = User.objects.create_user(email='proxytester@example.com', password='x')
        return user

    def test_rejects_non_cambridge_host(self):
        request = self.factory.get('/api/audio-proxy/', {'url': 'http://evil.com/audio.mp3'})
        request.user = self.user
        response = views.api_audio_proxy(request)
        self.assertEqual(response.status_code, 400)

    def test_serves_cambridge_audio(self):
        self._login()
        with patch.object(views.requests, 'get', return_value=FakeResponse(
            200, b'cambridge-bytes', {'Content-Type': 'audio/mpeg'})):
            response = views.api_audio_proxy(self._request(self.cambridge_url))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'cambridge-bytes')
        self.assertEqual(response['Content-Type'], 'audio/mpeg')

    def test_falls_back_to_google_tts_when_cambridge_blocked(self):
        self._login()
        with patch.object(views.requests, 'get') as mock_get:
            def side_effect(url, **kwargs):
                if 'dictionary.cambridge.org' in url:
                    return FakeResponse(403, b'blocked')
                if 'translate_tts' in url:
                    self.assertEqual(kwargs['params']['q'], 'summarize')
                    return FakeResponse(200, b'tts-bytes', {'Content-Type': 'audio/mpeg'})
                raise AssertionError(f'Unexpected URL: {url}')

            mock_get.side_effect = side_effect
            response = views.api_audio_proxy(self._request(self.cambridge_url))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'tts-bytes')
        self.assertEqual(response['Content-Type'], 'audio/mpeg')

    def test_fallback_fails_returns_502(self):
        self._login()
        with patch.object(views.requests, 'get') as mock_get:
            def side_effect(url, **kwargs):
                if 'dictionary.cambridge.org' in url:
                    return FakeResponse(403, b'blocked')
                return FakeResponse(500, b'error')

            mock_get.side_effect = side_effect
            response = views.api_audio_proxy(self._request(self.cambridge_url))
        self.assertEqual(response.status_code, 502)
