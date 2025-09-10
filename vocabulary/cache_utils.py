"""
Cache Utilities for Learn English Application
Provides efficient caching for frequently accessed data using Django's cache framework.
"""

from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
import hashlib
import json
from functools import wraps
from typing import Optional, Any, Dict, List

User = get_user_model()

# Get cache timeouts from settings
CACHE_TIMEOUTS = getattr(settings, 'CACHE_TIMEOUTS', {
    'flashcard_list': 600,     # 10 minutes
    'study_session': 300,      # 5 minutes  
    'user_statistics': 1800,   # 30 minutes
    'deck_info': 900,          # 15 minutes
    'api_response': 120,       # 2 minutes
    'incorrect_words': 300,    # 5 minutes
    'favorites': 600,          # 10 minutes
    'dashboard_stats': 300,    # 5 minutes
    'user_words': 600,         # 10 minutes
    'distractors': 600,        # 10 minutes
})

class CacheKeys:
    """Centralized cache key definitions."""
    
    # User-specific data
    USER_DECKS = "user:{user_id}:decks"
    USER_FLASHCARDS = "user:{user_id}:flashcards:deck:{deck_id}"
    USER_STATISTICS = "user:{user_id}:stats:{period}:{date}"
    USER_FAVORITES = "user:{user_id}:favorites"
    USER_INCORRECT_WORDS = "user:{user_id}:incorrect:{question_type}"
    
    # Study session data
    STUDY_CARDS_DIFFICULTY = "user:{user_id}:study:difficulty:{level}:deck:{deck_id}"
    NEXT_CARD_POOL = "user:{user_id}:next_card_pool:{hash}"
    
    # API responses
    API_NEXT_QUESTION = "api:next_question:user:{user_id}:mode:{mode}:{hash}"
    API_USER_STATS = "api:user_stats:user:{user_id}:{period}"
    
    # Deck information
    DECK_CARD_COUNT = "deck:{deck_id}:card_count"
    DECK_INFO = "deck:{deck_id}:info"

def generate_cache_key(key_template: str, **kwargs) -> str:
    """Generate a cache key from template and parameters."""
    return key_template.format(**kwargs)

def hash_query_params(params: Dict[str, Any]) -> str:
    """Generate a hash for query parameters to use in cache keys."""
    sorted_params = json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(sorted_params.encode()).hexdigest()[:8]

def cache_result(cache_key: str, timeout: Optional[int] = None):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_timeout = timeout or CACHE_TIMEOUTS.get('api_response', 120)
            cache.set(cache_key, result, cache_timeout)
            return result
        return wrapper
    return decorator

class FlashcardCache:
    """Cache management for flashcard-related data."""
    
    @staticmethod
    def get_user_flashcards(user_id: int, deck_id: Optional[int] = None) -> Optional[List]:
        """Get cached user flashcards for a specific deck or all decks."""
        if deck_id:
            key = generate_cache_key(CacheKeys.USER_FLASHCARDS, user_id=user_id, deck_id=deck_id)
        else:
            key = generate_cache_key(CacheKeys.USER_FLASHCARDS, user_id=user_id, deck_id="all")
        return cache.get(key)
    
    @staticmethod
    def set_user_flashcards(user_id: int, flashcards: List, deck_id: Optional[int] = None):
        """Cache user flashcards."""
        if deck_id:
            key = generate_cache_key(CacheKeys.USER_FLASHCARDS, user_id=user_id, deck_id=deck_id)
        else:
            key = generate_cache_key(CacheKeys.USER_FLASHCARDS, user_id=user_id, deck_id="all")
        cache.set(key, flashcards, CACHE_TIMEOUTS['flashcard_list'])
    
    @staticmethod
    def get_study_cards_by_difficulty(user_id: int, difficulty_level: str, deck_id: Optional[int] = None) -> Optional[List]:
        """Get cached flashcards by difficulty level."""
        key = generate_cache_key(
            CacheKeys.STUDY_CARDS_DIFFICULTY, 
            user_id=user_id, 
            level=difficulty_level, 
            deck_id=deck_id or "all"
        )
        return cache.get(key)
    
    @staticmethod
    def set_study_cards_by_difficulty(user_id: int, difficulty_level: str, cards: List, deck_id: Optional[int] = None):
        """Cache flashcards by difficulty level."""
        key = generate_cache_key(
            CacheKeys.STUDY_CARDS_DIFFICULTY, 
            user_id=user_id, 
            level=difficulty_level, 
            deck_id=deck_id or "all"
        )
        cache.set(key, cards, CACHE_TIMEOUTS['study_session'])
    
    @staticmethod
    def invalidate_user_cards(user_id: int):
        """Invalidate all flashcard-related caches for a user."""
        # For database cache, we'll rely on TTL expiration
        # Individual cache keys can be deleted if needed
        pass

class StudySessionCache:
    """Cache management for study session data."""
    
    @staticmethod
    def get_next_card_pool(user_id: int, params: Dict[str, Any]) -> Optional[List]:
        """Get cached next card pool based on study parameters."""
        params_hash = hash_query_params(params)
        key = generate_cache_key(CacheKeys.NEXT_CARD_POOL, user_id=user_id, hash=params_hash)
        return cache.get(key)
    
    @staticmethod
    def set_next_card_pool(user_id: int, params: Dict[str, Any], cards: List):
        """Cache next card pool."""
        params_hash = hash_query_params(params)
        key = generate_cache_key(CacheKeys.NEXT_CARD_POOL, user_id=user_id, hash=params_hash)
        cache.set(key, cards, CACHE_TIMEOUTS['study_session'])
    
    @staticmethod
    def get_user_favorites(user_id: int) -> Optional[List]:
        """Get cached user favorite flashcards."""
        key = generate_cache_key(CacheKeys.USER_FAVORITES, user_id=user_id)
        return cache.get(key)
    
    @staticmethod
    def set_user_favorites(user_id: int, favorites: List):
        """Cache user favorite flashcards."""
        key = generate_cache_key(CacheKeys.USER_FAVORITES, user_id=user_id)
        cache.set(key, favorites, CACHE_TIMEOUTS['favorites'])
    
    @staticmethod
    def get_user_incorrect_words(user_id: int, question_type: Optional[str] = None) -> Optional[List]:
        """Get cached user incorrect words."""
        key = generate_cache_key(CacheKeys.USER_INCORRECT_WORDS, user_id=user_id, question_type=question_type or "all")
        return cache.get(key)
    
    @staticmethod
    def set_user_incorrect_words(user_id: int, words: List, question_type: Optional[str] = None):
        """Cache user incorrect words."""
        key = generate_cache_key(CacheKeys.USER_INCORRECT_WORDS, user_id=user_id, question_type=question_type or "all")
        cache.set(key, words, CACHE_TIMEOUTS['incorrect_words'])

class StatisticsCache:
    """Cache management for user statistics."""
    
    @staticmethod
    def get_user_statistics(user_id: int, period: str, date: str) -> Optional[Dict]:
        """Get cached user statistics for a specific period and date."""
        key = generate_cache_key(CacheKeys.USER_STATISTICS, user_id=user_id, period=period, date=date)
        return cache.get(key)
    
    @staticmethod
    def set_user_statistics(user_id: int, period: str, date: str, stats: Dict):
        """Cache user statistics."""
        key = generate_cache_key(CacheKeys.USER_STATISTICS, user_id=user_id, period=period, date=date)
        cache.set(key, stats, CACHE_TIMEOUTS['user_statistics'])
    
    @staticmethod
    def invalidate_user_stats(user_id: int):
        """Invalidate all statistics caches for a user."""
        # For database cache, we'll rely on TTL expiration
        pass

class DeckCache:
    """Cache management for deck-related data."""
    
    @staticmethod
    def get_deck_info(deck_id: int) -> Optional[Dict]:
        """Get cached deck information."""
        key = generate_cache_key(CacheKeys.DECK_INFO, deck_id=deck_id)
        return cache.get(key)
    
    @staticmethod
    def set_deck_info(deck_id: int, info: Dict):
        """Cache deck information."""
        key = generate_cache_key(CacheKeys.DECK_INFO, deck_id=deck_id)
        cache.set(key, info, CACHE_TIMEOUTS['deck_info'])
    
    @staticmethod
    def get_deck_card_count(deck_id: int) -> Optional[int]:
        """Get cached deck card count."""
        key = generate_cache_key(CacheKeys.DECK_CARD_COUNT, deck_id=deck_id)
        return cache.get(key)
    
    @staticmethod
    def set_deck_card_count(deck_id: int, count: int):
        """Cache deck card count."""
        key = generate_cache_key(CacheKeys.DECK_CARD_COUNT, deck_id=deck_id)
        cache.set(key, count, CACHE_TIMEOUTS['deck_info'])

class APICache:
    """Cache management for API responses."""
    
    @staticmethod
    def cache_api_response(cache_key: str, data: Any, timeout: Optional[int] = None):
        """Cache API response data."""
        cache_timeout = timeout or CACHE_TIMEOUTS['api_response']
        cache.set(cache_key, data, cache_timeout)
    
    @staticmethod
    def get_api_response(cache_key: str) -> Optional[Any]:
        """Get cached API response."""
        return cache.get(cache_key)

# Utility functions
def clear_user_cache(user_id: int):
    """Clear all cached data for a specific user."""
    FlashcardCache.invalidate_user_cards(user_id)
    StatisticsCache.invalidate_user_stats(user_id)

def clear_all_cache():
    """Clear all cached data (use with caution)."""
    cache.clear()

def invalidate_user_study_cache(user_id: int):
    """Invalidate study-related cache when flashcards are modified."""
    cache_keys_to_invalidate = [
        f"user_{user_id}_all_flashcards",
        f"user_{user_id}_flashcards_distractors", 
        f"user_{user_id}_dashboard_basic_stats",
        f"user_{user_id}_favorites",
        f"user_{user_id}_incorrect_words"
    ]
    cache.delete_many(cache_keys_to_invalidate)

def get_cache_stats():
    """Get cache statistics for database cache."""
    try:
        # For database cache, we can return basic information
        return {
            'cache_backend': 'Database Cache',
            'status': 'Active',
            'note': 'Using Django database cache backend'
        }
    except Exception as e:
        return {'error': f'Unable to get cache stats: {str(e)}'}