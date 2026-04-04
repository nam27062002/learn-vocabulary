# Study Logic Bug Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 5 high-priority bugs in the study system that cause data loss, stale cache, and incorrect statistics.

**Architecture:** All fixes are isolated to 3 backend files (`statistics_utils.py`, `cache_utils.py`, `signals.py`) and 1 view file (`views.py`). No schema changes needed. Each task is independently deployable.

**Tech Stack:** Django 4.x, Python 3.x, Django ORM, Django cache framework, Django signals, `django.db.transaction`

---

## File Map

| File | Change Type | Why |
|------|-------------|-----|
| `vocabulary/statistics_utils.py` | Modify | Fix `difficulty_after` bug + fix N+1 word count query |
| `vocabulary/cache_utils.py` | Modify | Implement `StatisticsCache.invalidate_user_stats()` |
| `vocabulary/signals.py` | Modify | Add `StudySession` post_save signal handler |
| `vocabulary/views.py` | Modify | Fix stale session deletion + wrap answer in `transaction.atomic()` |
| `tests/test_study_bugs.py` | Create | All new tests live here |

---

## Task 1: Fix `difficulty_after` Always Equals `difficulty_before`

**Problem:** `record_answer()` (`statistics_utils.py:40`) sets `difficulty_after=flashcard.difficulty_score` at creation time. But `_update_card_difficulty()` runs **after** `record_answer()` in `views.py:649`. So `difficulty_after` is always the same as `difficulty_before`.

**Fix:** Add a `difficulty_after` parameter to `record_answer()` with a default of `None`. When `None`, fall back to `flashcard.difficulty_score` (current behavior preserved for callers that don't pass it). In `views.py`, call `_update_card_difficulty()` first, then pass the new score to `record_answer()`.

**Files:**
- Modify: `vocabulary/statistics_utils.py:27-69`
- Modify: `vocabulary/views.py:570-578`
- Create: `tests/test_study_bugs.py`

---

- [ ] **Step 1: Create test file and write the failing test**

Create `tests/test_study_bugs.py`:

```python
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
            difficulty_score=None  # New card
        )
        self.session = create_study_session(self.user, study_mode='deck', deck_ids=[self.deck.id])

    def test_difficulty_after_reflects_post_update_score(self):
        """difficulty_after must store the difficulty AFTER the update, not before."""
        # Simulate what views.py does: update card first, then record answer
        self.card.difficulty_score = 0.0  # "Again" — updated by _update_card_difficulty
        self.card.save()

        answer = record_answer(
            session=self.session,
            flashcard=self.card,
            is_correct=False,
            response_time_seconds=3.5,
            question_type='multiple_choice',
            difficulty_after=0.0,  # Explicitly pass post-update difficulty
        )

        self.assertEqual(answer.difficulty_before, None)   # Was None before
        self.assertEqual(answer.difficulty_after, 0.0)     # Is 0.0 after update

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
            # No difficulty_after passed
        )

        # Falls back to current card score
        self.assertEqual(answer.difficulty_after, 0.67)
```

- [ ] **Step 2: Run tests to verify they fail**

```
python manage.py test tests.test_study_bugs.DifficultyAfterBugTest -v 2
```

Expected: `TypeError: record_answer() got an unexpected keyword argument 'difficulty_after'`

---

- [ ] **Step 3: Update `record_answer()` signature in `statistics_utils.py`**

Change lines 27–41 from:

```python
def record_answer(session, flashcard, is_correct, response_time_seconds, question_type='multiple_choice'):
    """Record an answer within a study session."""
    # Get difficulty before and after
    difficulty_before = flashcard.difficulty_score
    
    # Create the answer record
    answer = StudySessionAnswer.objects.create(
        session=session,
        flashcard=flashcard,
        is_correct=is_correct,
        response_time_seconds=response_time_seconds,
        question_type=question_type,
        difficulty_before=difficulty_before,
        difficulty_after=flashcard.difficulty_score  # This will be updated by the SM-2 algorithm
    )
```

To:

```python
def record_answer(session, flashcard, is_correct, response_time_seconds, question_type='multiple_choice', difficulty_after=None):
    """Record an answer within a study session.
    
    Pass difficulty_after explicitly with the post-update difficulty_score so the
    stored value reflects the actual change made by _update_card_difficulty().
    If omitted, falls back to the card's current difficulty_score (backward compat).
    """
    difficulty_before = flashcard.difficulty_score

    # Use explicit post-update difficulty when provided; fall back to current score
    resolved_difficulty_after = difficulty_after if difficulty_after is not None else flashcard.difficulty_score

    answer = StudySessionAnswer.objects.create(
        session=session,
        flashcard=flashcard,
        is_correct=is_correct,
        response_time_seconds=response_time_seconds,
        question_type=question_type,
        difficulty_before=difficulty_before,
        difficulty_after=resolved_difficulty_after,
    )
```

---

- [ ] **Step 4: Update `views.py` to call `record_answer()` AFTER updating card difficulty**

In `views.py`, the current order around lines 570–652 is:
1. `record_answer(...)` ← called with old difficulty
2. `_update_card_difficulty(card, correct, grade)` ← updates card

Swap the order and pass `difficulty_after`. Replace the two blocks:

```python
        # Record the answer in the session
        record_answer(session, card, correct, response_time, question_type)
```

And further down:

```python
        # Update difficulty-based system (replaces SM-2)
        try:
            # Use grade for difficulty if available, otherwise use correct parameter
            _update_card_difficulty(card, correct, grade)
        except Exception as e:
            print(f"Error in difficulty update: {e}")
```

With this combined replacement (keep everything else between them intact):

```python
        # Update card difficulty FIRST so we can pass the new score to record_answer
        new_difficulty_score = card.difficulty_score  # fallback
        try:
            _update_card_difficulty(card, correct, grade)
            card.refresh_from_db(fields=['difficulty_score'])
            new_difficulty_score = card.difficulty_score
        except Exception as e:
            print(f"Error in difficulty update: {e}")

        # Now record the answer with the correct post-update difficulty
        record_answer(session, card, correct, response_time, question_type,
                      difficulty_after=new_difficulty_score)
```

> **Note:** Remove the original `record_answer(...)` call at line 572 and the `_update_card_difficulty(...)` block at line 647–652. They are replaced by the block above.

---

- [ ] **Step 5: Run tests to verify they pass**

```
python manage.py test tests.test_study_bugs.DifficultyAfterBugTest -v 2
```

Expected: `OK`

---

- [ ] **Step 6: Commit**

```bash
git add vocabulary/statistics_utils.py vocabulary/views.py tests/test_study_bugs.py
git commit -m "fix: difficulty_after now stores post-update score in StudySessionAnswer"
```

---

## Task 2: Fix Stale Sessions Being Deleted Instead of Saved

**Problem:** `study_page()` in `views.py:1566–1573` calls `.delete()` on incomplete sessions. This cascades to `StudySessionAnswer` records, permanently losing study data and preventing statistics aggregation.

**Fix:** Instead of deleting, end each incomplete session by setting `session_end = timezone.now()` and calling `end_study_session()`. This preserves data and updates daily/weekly statistics.

**Files:**
- Modify: `vocabulary/views.py:1565-1573`
- Modify: `tests/test_study_bugs.py`

---

- [ ] **Step 1: Write failing test**

Add to `tests/test_study_bugs.py`:

```python
from vocabulary.statistics_utils import create_study_session, end_study_session


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
        # Create an incomplete session (no session_end)
        session = StudySession.objects.create(
            user=self.user,
            study_mode='deck',
            session_end=None,
        )
        session_id = session.id

        # Visiting study page should NOT delete the session
        response = self.client.get('/study/')
        self.assertEqual(response.status_code, 200)

        # Session must still exist
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
```

- [ ] **Step 2: Run tests to verify they fail**

```
python manage.py test tests.test_study_bugs.StaleSessionPreservationTest -v 2
```

Expected: `AssertionError: Stale session was deleted — it should have been ended instead`

---

- [ ] **Step 3: Update `study_page()` in `views.py`**

Replace lines 1565–1573:

```python
    # Instead of completing stale sessions, we'll delete them to prevent incorrect stats
    incomplete_sessions = StudySession.objects.filter(
        user=request.user,
        session_end__isnull=True
    )
    if incomplete_sessions.exists():
        # Log that we are deleting stale sessions for debugging
        print(f"Deleting {incomplete_sessions.count()} stale study sessions for user {request.user.id}")
        incomplete_sessions.delete()
```

With:

```python
    # End stale sessions gracefully instead of deleting — preserves study data
    incomplete_sessions = StudySession.objects.filter(
        user=request.user,
        session_end__isnull=True
    )
    for stale in incomplete_sessions:
        end_study_session(stale)
```

Also add the import at the top of `views.py` if not already present (check for existing import of `end_study_session`):

```python
from .statistics_utils import (
    create_study_session, record_answer, end_study_session,
    update_daily_statistics, update_weekly_statistics
)
```

---

- [ ] **Step 4: Run tests to verify they pass**

```
python manage.py test tests.test_study_bugs.StaleSessionPreservationTest -v 2
```

Expected: `OK`

---

- [ ] **Step 5: Commit**

```bash
git add vocabulary/views.py tests/test_study_bugs.py
git commit -m "fix: end stale study sessions gracefully instead of deleting them"
```

---

## Task 3: Implement `StatisticsCache.invalidate_user_stats()`

**Problem:** `StatisticsCache.invalidate_user_stats()` in `cache_utils.py:186` is a no-op (`pass`). Statistics cache (TTL 30 min) is never actively cleared, so users see stale stats long after a session ends.

**Fix:** Implement the method to delete all stats-related cache keys for the given user. The `CacheKeys.USER_STATISTICS` template is `"user:{user_id}:stats:{period}:{date}"`. Since Django's database cache doesn't support wildcard deletion, we delete known period/date combinations used by the statistics view.

**Files:**
- Modify: `vocabulary/cache_utils.py:185-189`
- Modify: `tests/test_study_bugs.py`

---

- [ ] **Step 1: Identify which cache keys are written for statistics**

Search the codebase for all `StatisticsCache.set_user_statistics` calls:

```
python -c "
import subprocess
result = subprocess.run(['grep', '-rn', 'set_user_statistics', 'vocabulary/'], capture_output=True, text=True)
print(result.stdout)
"
```

Or use grep in the terminal:
```
grep -rn "set_user_statistics" vocabulary/
```

Note the `period` values used (e.g. `'30'`, `'7'`, `'90'`) — you will delete all of them in the invalidation.

---

- [ ] **Step 2: Write failing test**

Add to `tests/test_study_bugs.py`:

```python
from django.core.cache import cache
from vocabulary.cache_utils import StatisticsCache, CacheKeys, generate_cache_key


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

        # Populate cache for multiple periods
        for period in ['7', '30', '90']:
            key = generate_cache_key(
                CacheKeys.USER_STATISTICS,
                user_id=self.user_id,
                period=period,
                date=today_str,
            )
            cache.set(key, {'some': 'data'}, 3600)

        # Verify they exist
        for period in ['7', '30', '90']:
            key = generate_cache_key(
                CacheKeys.USER_STATISTICS,
                user_id=self.user_id,
                period=period,
                date=today_str,
            )
            self.assertIsNotNone(cache.get(key), f"Pre-condition: cache for period={period} should exist")

        # Invalidate
        StatisticsCache.invalidate_user_stats(self.user_id)

        # All entries must be gone
        for period in ['7', '30', '90']:
            key = generate_cache_key(
                CacheKeys.USER_STATISTICS,
                user_id=self.user_id,
                period=period,
                date=today_str,
            )
            self.assertIsNone(cache.get(key), f"Cache for period={period} should be cleared after invalidation")
```

- [ ] **Step 3: Run tests to verify they fail**

```
python manage.py test tests.test_study_bugs.StatisticsCacheInvalidationTest -v 2
```

Expected: `AssertionError: Cache for period=7 should be cleared after invalidation`

---

- [ ] **Step 4: Implement `invalidate_user_stats()` in `cache_utils.py`**

Replace lines 185–189:

```python
    @staticmethod
    def invalidate_user_stats(user_id: int):
        """Invalidate all statistics caches for a user."""
        # For database cache, we'll rely on TTL expiration
        pass
```

With:

```python
    @staticmethod
    def invalidate_user_stats(user_id: int):
        """Delete all statistics cache entries for a user across all periods and today's date."""
        from django.utils import timezone
        today_str = timezone.now().date().isoformat()
        periods = ['7', '30', '90']
        keys = [
            generate_cache_key(
                CacheKeys.USER_STATISTICS,
                user_id=user_id,
                period=period,
                date=today_str,
            )
            for period in periods
        ]
        cache.delete_many(keys)
```

---

- [ ] **Step 5: Run tests to verify they pass**

```
python manage.py test tests.test_study_bugs.StatisticsCacheInvalidationTest -v 2
```

Expected: `OK`

---

- [ ] **Step 6: Commit**

```bash
git add vocabulary/cache_utils.py tests/test_study_bugs.py
git commit -m "fix: implement StatisticsCache.invalidate_user_stats() to clear stale stats cache"
```

---

## Task 4: Add StudySession Signal to Invalidate Stats Cache on Session End

**Problem:** `signals.py` has no handler for `StudySession`. When a session ends and `end_study_session()` updates `DailyStatistics`, the stats cache for that user is never cleared. Users must wait up to 30 minutes to see accurate stats.

**Fix:** Add a `post_save` signal on `StudySession` that calls `StatisticsCache.invalidate_user_stats()` when `session_end` is set (i.e. when the session transitions from incomplete → complete).

**Files:**
- Modify: `vocabulary/signals.py`
- Modify: `tests/test_study_bugs.py`

---

- [ ] **Step 1: Write failing test**

Add to `tests/test_study_bugs.py`:

```python
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

        # Pre-populate a stats cache entry
        key = generate_cache_key(
            CacheKeys.USER_STATISTICS,
            user_id=self.user_id,
            period='30',
            date=today_str,
        )
        cache.set(key, {'stale': 'data'}, 3600)
        self.assertIsNotNone(cache.get(key), "Pre-condition: cache should exist before session ends")

        # Create and end a session (simulates end_study_session)
        session = StudySession.objects.create(
            user=self.user,
            study_mode='deck',
            session_end=None,
        )
        session.session_end = timezone.now()
        session.save()

        # Stats cache must be cleared by signal
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

        # Create session without session_end
        StudySession.objects.create(
            user=self.user,
            study_mode='deck',
            session_end=None,
        )

        # Cache should still be intact
        self.assertIsNotNone(
            cache.get(key),
            "Stats cache should NOT be cleared when a new incomplete session is created"
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```
python manage.py test tests.test_study_bugs.StudySessionSignalTest -v 2
```

Expected: `AssertionError: Stats cache should be cleared after study session ends`

---

- [ ] **Step 3: Add signal handler in `signals.py`**

Add the following to `vocabulary/signals.py` after the existing imports:

```python
from .models import Flashcard, FavoriteFlashcard, IncorrectWordReview, StudySession
from .cache_utils import invalidate_user_study_cache, StatisticsCache
```

Then add the new handler at the end of the file:

```python
@receiver(post_save, sender=StudySession)
def invalidate_stats_cache_on_session_end(sender, instance, created, **kwargs):
    """Clear statistics cache when a study session is ended (session_end set)."""
    if not created and instance.session_end is not None:
        StatisticsCache.invalidate_user_stats(instance.user_id)
```

---

- [ ] **Step 4: Run tests to verify they pass**

```
python manage.py test tests.test_study_bugs.StudySessionSignalTest -v 2
```

Expected: `OK`

---

- [ ] **Step 5: Commit**

```bash
git add vocabulary/signals.py tests/test_study_bugs.py
git commit -m "fix: add StudySession post_save signal to invalidate stats cache on session end"
```

---

## Task 5: Wrap Answer Submission in `transaction.atomic()`

**Problem:** In `api_submit_answer` (`views.py`), answer recording, card difficulty update, and incorrect-word tracking run as separate database operations. If any step fails mid-way (e.g. a database error during `_update_card_difficulty`), earlier writes (like `StudySessionAnswer`) are committed while later ones are not, leaving the database in an inconsistent state.

**Fix:** Wrap the core answer-processing block in `transaction.atomic()`. The learning-queue update (in-memory session storage) stays outside the transaction since it's not database-backed.

**Files:**
- Modify: `vocabulary/views.py` (the `api_submit_answer` view)
- Modify: `tests/test_study_bugs.py`

---

- [ ] **Step 1: Write failing test**

Add to `tests/test_study_bugs.py`:

```python
from unittest.mock import patch


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

        # Create a session and store its id in django session
        session = create_study_session(self.user, study_mode='deck', deck_ids=[self.deck.id])
        django_session = self.client.session
        django_session['current_study_session_id'] = session.id
        django_session.save()
        self.study_session = session

    def test_answer_not_recorded_when_difficulty_update_fails(self):
        """If _update_card_difficulty raises, StudySessionAnswer must NOT be committed."""
        initial_answer_count = StudySessionAnswer.objects.filter(
            session=self.study_session
        ).count()

        with patch('vocabulary.views._update_card_difficulty', side_effect=Exception("DB error")):
            response = self.client.post(
                '/api/study/submit-answer/',
                data=json.dumps({
                    'card_id': self.card.id,
                    'correct': True,
                    'response_time': 2.5,
                    'question_type': 'multiple_choice',
                }),
                content_type='application/json',
            )

        # Answer must NOT have been recorded due to transaction rollback
        final_answer_count = StudySessionAnswer.objects.filter(
            session=self.study_session
        ).count()
        self.assertEqual(
            initial_answer_count,
            final_answer_count,
            "StudySessionAnswer should be rolled back when difficulty update fails"
        )
```

- [ ] **Step 2: Run test to verify it fails**

```
python manage.py test tests.test_study_bugs.AnswerSubmissionAtomicTest -v 2
```

Expected: `AssertionError: StudySessionAnswer should be rolled back when difficulty update fails` (answer count increased despite the exception, proving no transaction)

---

- [ ] **Step 3: Add `transaction.atomic()` to `api_submit_answer` in `views.py`**

Add the import at the top of `views.py` (if not already present):

```python
from django.db import transaction
```

Then locate the core answer-processing block inside `api_submit_answer`. It starts at the `# Record the answer in the session` comment (around line 551). Wrap the DB operations in `transaction.atomic()`. The restructured block (replace the existing try/except for session recording and the difficulty update block) looks like this:

```python
        # Atomically record answer + update difficulty + track incorrect words
        with transaction.atomic():
            # Get current study session
            current_session_id = request.session.get('current_study_session_id')
            if current_session_id:
                try:
                    session = StudySession.objects.get(id=current_session_id, user=request.user)

                    # Check for recent duplicate submissions (within last 5 seconds)
                    recent_cutoff = timezone.now() - timedelta(seconds=5)
                    recent_answer = StudySessionAnswer.objects.filter(
                        session=session,
                        flashcard=card,
                        answered_at__gte=recent_cutoff
                    ).first()

                    if recent_answer:
                        return JsonResponse({'success': True, 'duplicate_prevented': True})

                except StudySession.DoesNotExist:
                    session = None

            else:
                session = None

            # Update card difficulty FIRST to capture correct difficulty_after
            new_difficulty_score = card.difficulty_score  # fallback
            _update_card_difficulty(card, correct, grade)
            card.refresh_from_db(fields=['difficulty_score'])
            new_difficulty_score = card.difficulty_score

            # Record the answer with the correct post-update difficulty
            if session:
                record_answer(session, card, correct, response_time, question_type,
                              difficulty_after=new_difficulty_score)

            # Handle incorrect word tracking
            question_type_map = {
                'multiple_choice': 'mc',
                'input': 'type',
                'type': 'type',
                'dictation': 'dictation'
            }
            mapped_question_type = question_type_map.get(question_type, question_type)

            if not correct:
                incorrect_review, created = IncorrectWordReview.objects.get_or_create(
                    user=request.user,
                    flashcard=card,
                    question_type=mapped_question_type,
                    defaults={'error_count': 1}
                )
                if not created:
                    incorrect_review.add_error()
            else:
                try:
                    incorrect_review = IncorrectWordReview.objects.get(
                        user=request.user,
                        flashcard=card,
                        question_type=mapped_question_type,
                        is_resolved=False
                    )
                    incorrect_review.mark_resolved()
                except IncorrectWordReview.DoesNotExist:
                    pass

        # Learning queue update is in-memory (session), NOT inside transaction
        try:
            if not correct:
                _queue_card_for_review(request, card.id, mapped_question_type)
            else:
                _queue_remove_card(request, card.id)
        except Exception:
            pass

        return JsonResponse({'success': True})
```

> **Note:** Remove all the existing debug `print(f"...")` stderr calls within this block — they are noise from development and don't belong in production code. Keep the structure clean.

---

- [ ] **Step 4: Run all tests to verify they pass**

```
python manage.py test tests.test_study_bugs -v 2
```

Expected: All 8 tests pass — `OK`

---

- [ ] **Step 5: Run the full test suite to check for regressions**

```
python manage.py test vocabulary accounts -v 1
```

Expected: No new failures.

---

- [ ] **Step 6: Final commit**

```bash
git add vocabulary/views.py tests/test_study_bugs.py
git commit -m "fix: wrap answer submission in transaction.atomic() to ensure data consistency"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Bug 1 (difficulty_after): Task 1 covers it fully
- [x] Bug 2 (stale sessions deleted): Task 2 covers it fully
- [x] Bug 3 (cache invalidation empty): Task 3 covers it fully
- [x] Bug 4 (missing StudySession signal): Task 4 covers it fully
- [x] Bug 5 (no transaction.atomic): Task 5 covers it fully

**Placeholder scan:**
- No TBD, TODO, or incomplete sections
- All code blocks are complete and runnable
- All test assertions have specific failure messages

**Type consistency:**
- `record_answer()` signature updated consistently in Task 1 and referenced correctly in Task 5
- `StatisticsCache.invalidate_user_stats()` defined in Task 3 and used in Task 4
- `CacheKeys.USER_STATISTICS`, `generate_cache_key` used consistently across Tasks 3 and 4

**Known dependency between tasks:**
- Task 5 references the updated `record_answer()` from Task 1 — implement Task 1 before Task 5
- Task 4 depends on Task 3's `invalidate_user_stats()` implementation — implement Task 3 before Task 4
- Tasks 2 and 3 are fully independent of each other and of Tasks 1/5
