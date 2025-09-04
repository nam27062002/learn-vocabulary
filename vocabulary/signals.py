"""
Django signals to handle cache invalidation when models are modified.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Flashcard, FavoriteFlashcard, IncorrectWordReview
from .cache_utils import invalidate_user_study_cache


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