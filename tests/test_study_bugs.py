"""Tests for study system bug fixes."""
import json
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
