"""
Django signals to handle cache invalidation when models are modified.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Flashcard, FavoriteFlashcard, IncorrectWordReview, StudySession
from .cache_utils import invalidate_user_study_cache, StatisticsCache


@receiver([post_save, post_delete], sender=Flashcard)
def invalidate_flashcard_cache(sender, instance, **kwargs):
    """Invalidate user's study cache when flashcards are modified."""
    invalidate_user_study_cache(instance.user_id)


@receiver([post_save, post_delete], sender=FavoriteFlashcard)
def invalidate_favorite_cache(sender, instance, **kwargs):
    """Invalidate user's favorite cache when favorites are modified."""
    from django.core.cache import cache
    cache_key = f"user_{instance.user_id}_favorites"
    cache.delete(cache_key)


@receiver([post_save, post_delete], sender=IncorrectWordReview)
def invalidate_incorrect_words_cache(sender, instance, **kwargs):
    """Invalidate user's incorrect words cache when modified."""
    from django.core.cache import cache
    cache_key = f"user_{instance.user_id}_incorrect_words"
    cache.delete(cache_key)


@receiver(post_save, sender=StudySession)
def invalidate_stats_cache_on_session_end(sender, instance, created, **kwargs):
    """Clear statistics cache when a study session is ended (session_end becomes set)."""
    if not created and instance.session_end is not None:
        StatisticsCache.invalidate_user_stats(instance.user_id)