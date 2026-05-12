import json
import base64
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, Definition, Deck

User = get_user_model()


class SaveGeneratedImageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='imgtest@test.com', password='pass')
        self.client.force_login(self.user)
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')
        self.card = Flashcard.objects.create(user=self.user, deck=self.deck, word='resilient')
        Definition.objects.create(
            flashcard=self.card,
            english_definition='able to recover quickly from difficulties',
            vietnamese_definition='kiên cường',
        )

    def test_save_generated_image_success(self):
        """Endpoint saves b64 image to card.image and returns success."""
        fake_b64 = base64.b64encode(b'fake-png-data').decode()
        fake_result = {
            'image_b64': fake_b64,
            'provider': 'litellm',
            'model': 'gpt-image-1',
            'source': 'generated',
            'provider_label': 'LiteLLM',
            'model_label': 'gpt-image-1',
            'engine_label': 'LiteLLM / gpt-image-1',
        }
        with patch('vocabulary.image_service.generate_word_image_result', return_value=fake_result):
            response = self.client.post(
                '/api/ai/save-generated-image/',
                data=json.dumps({'flashcard_id': self.card.id}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['word'], 'resilient')
        self.assertEqual(data['model'], 'gpt-image-1')
        self.card.refresh_from_db()
        self.assertTrue(bool(self.card.image))

    def test_returns_404_for_card_of_other_user(self):
        """Endpoint returns 404 when card belongs to a different user."""
        other = User.objects.create_user(email='other@test.com', password='pass')
        other_card = Flashcard.objects.create(user=other, word='agile')
        response = self.client.post(
            '/api/ai/save-generated-image/',
            data=json.dumps({'flashcard_id': other_card.id}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_returns_error_when_generation_fails(self):
        """Endpoint returns success=False when image_service returns None."""
        with patch('vocabulary.image_service.generate_word_image_result', return_value=None):
            response = self.client.post(
                '/api/ai/save-generated-image/',
                data=json.dumps({'flashcard_id': self.card.id}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    def test_requires_post_method(self):
        """Endpoint rejects GET requests."""
        response = self.client.get('/api/ai/save-generated-image/')
        self.assertEqual(response.status_code, 405)

    def test_unauthenticated_user_is_redirected(self):
        """Endpoint redirects unauthenticated users."""
        self.client.logout()
        response = self.client.post(
            '/api/ai/save-generated-image/',
            data=json.dumps({'flashcard_id': self.card.id}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)
