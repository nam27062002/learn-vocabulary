"""Tests for study system bug fixes."""
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from vocabulary.models import Flashcard, StudySession, StudySessionAnswer, Deck
from vocabulary.statistics_utils import record_answer, create_study_session

User = get_user_model()


class DifficultyAfterBugTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')
        self.card = Flashcard.objects.create(
            user=self.user,
            word='ephemeral',
            deck=self.deck,
            difficulty_score=None
        )
        self.session = create_study_session(self.user, study_mode='deck', deck_ids=[self.deck.id])

    def test_difficulty_after_reflects_post_update_score(self):
        """difficulty_after must store the difficulty AFTER the update, not before."""
        # Card starts at 0.67 (Good); simulate _update_card_difficulty() changing it to 0.0 (Again)
        self.card.difficulty_score = 0.67
        self.card.save()

        answer = record_answer(
            session=self.session,
            flashcard=self.card,
            is_correct=False,
            response_time_seconds=3.5,
            question_type='multiple_choice',
            difficulty_after=0.0,  # post-update value passed explicitly by views.py
        )

        # difficulty_before reflects the card score at call time (0.67)
        self.assertEqual(answer.difficulty_before, 0.67)
        # difficulty_after must reflect the explicitly-passed post-update value, not difficulty_before
        self.assertEqual(answer.difficulty_after, 0.0)

    def test_difficulty_after_defaults_to_current_score_when_not_provided(self):
        """Callers that don't pass difficulty_after should still work (backward compat)."""
        self.card.difficulty_score = 0.67
        self.card.save()

        answer = record_answer(
            session=self.session,
            flashcard=self.card,
            is_correct=True,
            response_time_seconds=2.0,
            question_type='multiple_choice',
        )

        self.assertEqual(answer.difficulty_after, 0.67)
