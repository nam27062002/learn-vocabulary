# tests/test_example_sentence.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, Deck

User = get_user_model()

class ExampleSentenceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.com', password='pass')
        self.deck = Deck.objects.create(user=self.user, name='Test')

    def test_flashcard_has_example_sentence_field(self):
        card = Flashcard.objects.create(user=self.user, deck=self.deck, word='resilient')
        card.example_sentence = 'She is a resilient person.'
        card.example_source = 'cambridge'
        card.save()
        card.refresh_from_db()
        self.assertEqual(card.example_sentence, 'She is a resilient person.')
        self.assertEqual(card.example_source, 'cambridge')

    def test_example_fields_nullable(self):
        card = Flashcard.objects.create(user=self.user, deck=self.deck, word='brave')
        self.assertIsNone(card.example_sentence)
        self.assertIsNone(card.example_source)
