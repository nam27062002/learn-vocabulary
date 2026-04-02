"""Tests for study system bug fixes."""
import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from vocabulary.models import Flashcard, StudySession, StudySessionAnswer, Deck
from vocabulary.statistics_utils import record_answer, create_study_session, end_study_session
from vocabulary.cache_utils import StatisticsCache, CacheKeys, generate_cache_key

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

    def test_difficulty_before_captures_pre_update_score(self):
        """difficulty_before must store the difficulty BEFORE _update_card_difficulty runs."""
        # Card starts at 'Good' difficulty
        self.card.difficulty_score = 0.67
        self.card.save()

        # Simulate the api_submit_answer flow: update card first, then record
        old_score = self.card.difficulty_score  # 0.67 — captured before update
        self.card.difficulty_score = 0.0        # simulates _update_card_difficulty setting to "Again"
        self.card.save()

        answer = record_answer(
            session=self.session,
            flashcard=self.card,
            is_correct=False,
            response_time_seconds=3.5,
            question_type='multiple_choice',
            difficulty_after=0.0,
            difficulty_before_override=old_score,  # explicitly pass pre-update value
        )

        self.assertEqual(answer.difficulty_before, 0.67,
                         "difficulty_before should be 0.67 (before the update), not 0.0")
        self.assertEqual(answer.difficulty_after, 0.0,
                         "difficulty_after should be 0.0 (after the update)")
        self.assertNotEqual(answer.difficulty_before, answer.difficulty_after,
                            "difficulty_before and difficulty_after should differ when difficulty changed")

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


class StatisticsCacheInvalidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='cache@example.com',
            password='testpass123'
        )
        self.user_id = self.user.id

    def test_invalidate_user_stats_clears_cached_entries(self):
        """invalidate_user_stats must delete all statistics cache entries for a user."""
        today_str = timezone.now().date().isoformat()

        for period in ['7', '30', '90']:
            key = generate_cache_key(
                CacheKeys.USER_STATISTICS,
                user_id=self.user_id,
                period=period,
                date=today_str,
            )
            cache.set(key, {'some': 'data'}, 3600)

        for period in ['7', '30', '90']:
            key = generate_cache_key(
                CacheKeys.USER_STATISTICS,
                user_id=self.user_id,
                period=period,
                date=today_str,
            )
            self.assertIsNotNone(cache.get(key), f"Pre-condition: cache for period={period} should exist")

        StatisticsCache.invalidate_user_stats(self.user_id)

        for period in ['7', '30', '90']:
            key = generate_cache_key(
                CacheKeys.USER_STATISTICS,
                user_id=self.user_id,
                period=period,
                date=today_str,
            )
            self.assertIsNone(cache.get(key), f"Cache for period={period} should be cleared after invalidation")


class StaleSessionPreservationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='stale@example.com',
            password='testpass123'
        )
        self.deck = Deck.objects.create(user=self.user, name='Stale Deck')
        self.client = Client()
        self.client.login(email='stale@example.com', password='testpass123')

    def test_visiting_study_page_does_not_delete_incomplete_sessions(self):
        """Incomplete sessions must be ended gracefully, not deleted."""
        session = StudySession.objects.create(
            user=self.user,
            study_mode='deck',
            session_end=None,
        )
        session_id = session.id

        response = self.client.get('/study/')
        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            StudySession.objects.filter(id=session_id).exists(),
            "Stale session was deleted — it should have been ended instead"
        )

    def test_stale_session_is_marked_as_ended(self):
        """After visiting study page, incomplete sessions should have session_end set."""
        session = StudySession.objects.create(
            user=self.user,
            study_mode='deck',
            session_end=None,
        )
        session_id = session.id

        self.client.get('/study/')

        session.refresh_from_db()
        self.assertIsNotNone(
            session.session_end,
            "Stale session should have session_end set after study_page visit"
        )


class StudySessionSignalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='signal@example.com',
            password='testpass123'
        )
        self.user_id = self.user.id

    def test_ending_session_invalidates_stats_cache(self):
        """Saving a StudySession with session_end set must clear the stats cache."""
        today_str = timezone.now().date().isoformat()
        key = generate_cache_key(
            CacheKeys.USER_STATISTICS,
            user_id=self.user_id,
            period='30',
            date=today_str,
        )
        cache.set(key, {'stale': 'data'}, 3600)
        self.assertIsNotNone(cache.get(key), "Pre-condition: cache should exist before session ends")

        session = StudySession.objects.create(
            user=self.user,
            study_mode='deck',
            session_end=None,
        )
        session.session_end = timezone.now()
        session.save()

        self.assertIsNone(
            cache.get(key),
            "Stats cache should be cleared after study session ends"
        )

    def test_creating_session_without_end_does_not_clear_cache(self):
        """Creating a new (incomplete) session must NOT clear stats cache."""
        today_str = timezone.now().date().isoformat()
        key = generate_cache_key(
            CacheKeys.USER_STATISTICS,
            user_id=self.user_id,
            period='30',
            date=today_str,
        )
        cache.set(key, {'valid': 'data'}, 3600)

        StudySession.objects.create(
            user=self.user,
            study_mode='deck',
            session_end=None,
        )

        self.assertIsNotNone(
            cache.get(key),
            "Stats cache should NOT be cleared when a new incomplete session is created"
        )


class AnswerSubmissionAtomicTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='atomic@example.com',
            password='testpass123'
        )
        self.deck = Deck.objects.create(user=self.user, name='Atomic Deck')
        self.card = Flashcard.objects.create(
            user=self.user,
            word='resilient',
            deck=self.deck,
            difficulty_score=None,
        )
        self.client = Client()
        self.client.login(email='atomic@example.com', password='testpass123')

        session = create_study_session(self.user, study_mode='deck', deck_ids=[self.deck.id])
        django_session = self.client.session
        django_session['current_study_session_id'] = session.id
        django_session.save()
        self.study_session = session

    def test_answer_not_recorded_when_difficulty_update_fails(self):
        """If _update_card_difficulty raises inside atomic block, StudySessionAnswer must NOT be committed."""
        initial_answer_count = StudySessionAnswer.objects.filter(
            session=self.study_session
        ).count()

        with patch('vocabulary.views._update_card_difficulty', side_effect=Exception("DB error")):
            self.client.post(
                '/api/study/submit-answer/',
                data=json.dumps({
                    'card_id': self.card.id,
                    'correct': True,
                    'response_time': 2.5,
                    'question_type': 'multiple_choice',
                }),
                content_type='application/json',
            )

        final_answer_count = StudySessionAnswer.objects.filter(
            session=self.study_session
        ).count()
        self.assertEqual(
            initial_answer_count,
            final_answer_count,
            "StudySessionAnswer should be rolled back when difficulty update fails"
        )
