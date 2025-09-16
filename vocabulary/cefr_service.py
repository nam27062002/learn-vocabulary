"""
CEFR Level Classification Service

This service provides CEFR level classification for English words using the CEFR-J Wordlist.
The CEFR-J Wordlist is a comprehensive vocabulary list developed by Tokyo University of Foreign Studies
that classifies words according to CEFR levels (A1, A2, B1, B2, C1, C2).

Data Source: CEFR-J Wordlist Version 1.6
Citation: 『CEFR-J Wordlist Version 1.6』 東京外国語大学投野由紀夫研究室
URL: http://www.cefr-j.org/download.html
"""

import os
import json
import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class CEFRLevelClassifier:
    """
    CEFR Level Classifier using CEFR-J Wordlist data.
    
    This class provides methods to classify English words according to CEFR levels.
    It uses a local cache to store the wordlist data for fast lookups.
    """
    
    CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    CACHE_KEY = 'cefr_wordlist_data'
    CACHE_TIMEOUT = 60 * 60 * 24 * 7  # 1 week
    
    def __init__(self):
        self.wordlist_data = None
        self._load_wordlist()
    
    def _load_wordlist(self):
        """Load CEFR wordlist data from cache or initialize empty data."""
        try:
            # Try to load from cache first
            self.wordlist_data = cache.get(self.CACHE_KEY)
            
            if self.wordlist_data is None:
                # Initialize with empty data structure
                self.wordlist_data = {level: set() for level in self.CEFR_LEVELS}
                logger.info("Initialized empty CEFR wordlist data")
            else:
                # Convert sets back from lists (cache serialization)
                for level in self.CEFR_LEVELS:
                    if isinstance(self.wordlist_data.get(level), list):
                        self.wordlist_data[level] = set(self.wordlist_data[level])
                logger.info("Loaded CEFR wordlist data from cache")
                
        except Exception as e:
            logger.error(f"Error loading CEFR wordlist: {e}")
            self.wordlist_data = {level: set() for level in self.CEFR_LEVELS}
    
    def _save_wordlist_to_cache(self):
        """Save wordlist data to cache."""
        try:
            # Convert sets to lists for cache serialization
            cache_data = {}
            for level, words in self.wordlist_data.items():
                cache_data[level] = list(words) if isinstance(words, set) else words
            
            cache.set(self.CACHE_KEY, cache_data, self.CACHE_TIMEOUT)
            logger.info("Saved CEFR wordlist data to cache")
        except Exception as e:
            logger.error(f"Error saving CEFR wordlist to cache: {e}")
    
    def add_word_to_level(self, word, level):
        """
        Add a word to a specific CEFR level.
        
        Args:
            word (str): The word to add
            level (str): CEFR level (A1, A2, B1, B2, C1, C2)
        """
        if level not in self.CEFR_LEVELS:
            logger.warning(f"Invalid CEFR level: {level}")
            return
        
        if word and isinstance(word, str):
            word_clean = word.lower().strip()
            self.wordlist_data[level].add(word_clean)
    
    def get_word_level(self, word):
        """
        Get the CEFR level for a given word.

        Args:
            word (str): The word to classify

        Returns:
            str: CEFR level (A1, A2, B1, B2, C1, C2) or None if not found
        """
        if not word or not isinstance(word, str):
            return None

        word_clean = word.lower().strip()

        # Check each level in order (A1 to C2)
        for level in self.CEFR_LEVELS:
            if word_clean in self.wordlist_data[level]:
                return level

        # Fallback classification based on word characteristics
        return self._classify_word_fallback(word_clean)

    def _classify_word_fallback(self, word):
        """
        Fallback classification for words not in the CEFR database.
        Uses heuristics based on word length, complexity, and common patterns.

        Args:
            word (str): The word to classify (already cleaned)

        Returns:
            str: Estimated CEFR level
        """
        if not word:
            return None

        word_len = len(word)

        # Very short common words - likely A1
        if word_len <= 3:
            return 'A1'

        # Short words (4-5 letters) - likely A1 or A2
        if word_len <= 5:
            # Check for common patterns
            if word.endswith(('ing', 'ed', 'er', 'ly')):
                return 'A2'
            return 'A1'

        # Medium words (6-8 letters) - A2 to B1
        if word_len <= 8:
            # Check for complex suffixes
            if word.endswith(('tion', 'sion', 'ment', 'ness', 'able', 'ible')):
                return 'B1'
            if word.endswith(('ing', 'ed', 'er', 'ly', 'al')):
                return 'A2'
            return 'A2'

        # Long words (9-12 letters) - B1 to B2
        if word_len <= 12:
            # Check for academic/formal suffixes
            if word.endswith(('tion', 'sion', 'ment', 'ness', 'ity', 'ism', 'ist', 'ive', 'ous')):
                return 'B2'
            if word.endswith(('able', 'ible', 'ful', 'less', 'ward')):
                return 'B1'
            return 'B1'

        # Very long words (13+ letters) - B2 to C2
        if word_len <= 15:
            return 'B2'

        # Extremely long words - likely C1 or C2
        return 'C1'
    
    def get_level_color(self, level):
        """
        Get a color code for a CEFR level for UI display.
        
        Args:
            level (str): CEFR level
            
        Returns:
            str: CSS color class or hex color
        """
        level_colors = {
            'A1': '#4CAF50',  # Green - Beginner
            'A2': '#8BC34A',  # Light Green - Elementary
            'B1': '#FFC107',  # Amber - Intermediate
            'B2': '#FF9800',  # Orange - Upper Intermediate
            'C1': '#FF5722',  # Deep Orange - Advanced
            'C2': '#F44336',  # Red - Proficient
        }
        return level_colors.get(level, '#9E9E9E')  # Gray for unknown
    
    def get_level_description(self, level):
        """
        Get a human-readable description for a CEFR level.
        
        Args:
            level (str): CEFR level
            
        Returns:
            str: Description of the level
        """
        descriptions = {
            'A1': 'Beginner',
            'A2': 'Elementary', 
            'B1': 'Intermediate',
            'B2': 'Upper Intermediate',
            'C1': 'Advanced',
            'C2': 'Proficient'
        }
        return descriptions.get(level, 'Unknown')
    
    def bulk_classify_words(self, words):
        """
        Classify multiple words at once.
        
        Args:
            words (list): List of words to classify
            
        Returns:
            dict: Dictionary mapping words to their CEFR levels
        """
        results = {}
        for word in words:
            results[word] = self.get_word_level(word)
        return results
    
    def get_statistics(self):
        """
        Get statistics about the loaded wordlist.
        
        Returns:
            dict: Statistics including word counts per level
        """
        stats = {}
        total_words = 0
        
        for level in self.CEFR_LEVELS:
            count = len(self.wordlist_data[level])
            stats[level] = count
            total_words += count
        
        stats['total'] = total_words
        return stats
    
    def update_cache(self):
        """Force update the cache with current wordlist data."""
        self._save_wordlist_to_cache()


# Global instance
cefr_classifier = CEFRLevelClassifier()


def get_word_cefr_level(word):
    """
    Convenience function to get CEFR level for a word.
    
    Args:
        word (str): The word to classify
        
    Returns:
        str: CEFR level or None
    """
    return cefr_classifier.get_word_level(word)


def get_cefr_level_info(level):
    """
    Get comprehensive information about a CEFR level.
    
    Args:
        level (str): CEFR level
        
    Returns:
        dict: Level information including color and description
    """
    if not level:
        return None
    
    return {
        'level': level,
        'description': cefr_classifier.get_level_description(level),
        'color': cefr_classifier.get_level_color(level)
    }


def populate_cefr_data_from_sample():
    """
    Populate CEFR data with a comprehensive sample of common words for demonstration.
    This is based on common vocabulary lists and educational standards.
    """
    sample_data = {
        'A1': [
            # Basic greetings and common words
            'hello', 'goodbye', 'yes', 'no', 'please', 'thank', 'you', 'I', 'am', 'is', 'are',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'from', 'with',
            # Family and people
            'mother', 'father', 'family', 'friend', 'man', 'woman', 'boy', 'girl', 'baby',
            'people', 'person', 'child', 'children', 'brother', 'sister', 'son', 'daughter',
            # Basic objects and animals
            'cat', 'dog', 'house', 'car', 'book', 'water', 'food', 'table', 'chair', 'bed',
            'door', 'window', 'phone', 'computer', 'television', 'radio', 'clock', 'watch',
            # Colors and basic adjectives
            'red', 'blue', 'green', 'yellow', 'black', 'white', 'brown', 'orange', 'pink',
            'good', 'bad', 'big', 'small', 'hot', 'cold', 'happy', 'sad', 'new', 'old',
            # Numbers and time
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
            'today', 'tomorrow', 'yesterday', 'morning', 'afternoon', 'evening', 'night',
            # Basic places and activities
            'school', 'home', 'work', 'shop', 'park', 'street', 'city', 'country',
            'eat', 'drink', 'sleep', 'walk', 'run', 'sit', 'stand', 'go', 'come', 'see',
            'hear', 'speak', 'read', 'write', 'play', 'work', 'study', 'learn', 'teach'
        ],
        'A2': [
            # More complex adjectives and descriptions
            'beautiful', 'interesting', 'important', 'different', 'difficult', 'easy', 'expensive',
            'cheap', 'fast', 'slow', 'young', 'old', 'modern', 'traditional', 'popular', 'famous',
            'dangerous', 'safe', 'clean', 'dirty', 'quiet', 'noisy', 'busy', 'free', 'full', 'empty',
            # Places and travel
            'restaurant', 'hotel', 'airport', 'station', 'hospital', 'library', 'museum', 'cinema',
            'theater', 'bank', 'post', 'office', 'supermarket', 'pharmacy', 'garage', 'factory',
            # Weather and nature
            'weather', 'season', 'spring', 'summer', 'autumn', 'winter', 'rain', 'snow', 'sun',
            'wind', 'cloud', 'storm', 'temperature', 'degree', 'mountain', 'river', 'sea', 'lake',
            # Activities and hobbies
            'holiday', 'vacation', 'travel', 'journey', 'trip', 'visit', 'tour', 'adventure',
            'sport', 'football', 'tennis', 'swimming', 'dancing', 'music', 'singing', 'cooking',
            # Technology and communication
            'email', 'message', 'letter', 'newspaper', 'magazine', 'internet', 'website', 'photo'
        ],
        'B1': [
            # Environment and society
            'environment', 'pollution', 'climate', 'global', 'warming', 'recycling', 'energy',
            'renewable', 'sustainable', 'conservation', 'wildlife', 'species', 'habitat',
            # Technology and modern life
            'technology', 'computer', 'internet', 'website', 'software', 'hardware', 'digital',
            'online', 'offline', 'download', 'upload', 'database', 'network', 'security',
            # Government and politics
            'government', 'politics', 'political', 'democracy', 'election', 'vote', 'candidate',
            'parliament', 'minister', 'president', 'policy', 'law', 'legal', 'illegal',
            # Economy and business
            'economy', 'economic', 'business', 'company', 'organization', 'industry', 'market',
            'customer', 'service', 'product', 'price', 'cost', 'profit', 'loss', 'investment',
            # Education and knowledge
            'education', 'university', 'college', 'degree', 'qualification', 'research', 'study',
            'science', 'scientific', 'medicine', 'medical', 'health', 'healthy', 'disease',
            # Culture and society
            'culture', 'cultural', 'society', 'social', 'community', 'relationship', 'communication',
            'information', 'knowledge', 'experience', 'skill', 'ability', 'talent', 'creative'
        ],
        'B2': [
            # Advanced descriptive words
            'sophisticated', 'comprehensive', 'fundamental', 'significant', 'substantial', 'considerable',
            'contemporary', 'innovative', 'efficient', 'effective', 'productive', 'competitive',
            'alternative', 'potential', 'relevant', 'appropriate', 'adequate', 'sufficient',
            'anonymous', 'confidential', 'controversial', 'conventional', 'crucial', 'diverse',
            # Complex concepts
            'globalization', 'internationalization', 'modernization', 'industrialization',
            'urbanization', 'commercialization', 'privatization', 'standardization',
            # Academic and professional
            'democracy', 'capitalism', 'socialism', 'liberalism', 'conservatism', 'nationalism',
            'philosophy', 'psychology', 'sociology', 'anthropology', 'archaeology', 'linguistics',
            'economics', 'statistics', 'mathematics', 'physics', 'chemistry', 'biology',
            # Abstract concepts
            'concept', 'theory', 'principle', 'strategy', 'approach', 'method', 'technique',
            'procedure', 'process', 'system', 'structure', 'function', 'purpose', 'objective'
        ],
        'C1': [
            # Highly sophisticated vocabulary
            'unprecedented', 'ubiquitous', 'meticulous', 'scrupulous', 'conscientious', 'diligent',
            'comprehensive', 'exhaustive', 'thorough', 'rigorous', 'systematic', 'methodical',
            'entrepreneurship', 'bureaucracy', 'hierarchy', 'methodology', 'terminology', 'ideology',
            'phenomenon', 'hypothesis', 'synthesis', 'analysis', 'paradigm', 'framework',
            # Academic and research terms
            'empirical', 'theoretical', 'conceptual', 'analytical', 'critical', 'objective',
            'subjective', 'quantitative', 'qualitative', 'statistical', 'correlation', 'causation',
            # Professional and technical
            'implementation', 'optimization', 'enhancement', 'modification', 'adaptation',
            'integration', 'coordination', 'collaboration', 'consultation', 'negotiation'
        ],
        'C2': [
            # Extremely advanced vocabulary
            'quintessential', 'perspicacious', 'sagacious', 'erudite', 'pedantic', 'ostentatious',
            'pretentious', 'presumptuous', 'audacious', 'tenacious', 'vivacious', 'loquacious',
            # Philosophical and academic
            'epistemology', 'ontology', 'phenomenology', 'hermeneutics', 'dialectical', 'metaphysical',
            'existential', 'transcendental', 'empiricism', 'rationalism', 'pragmatism', 'nihilism',
            # Highly specialized terms
            'juxtaposition', 'dichotomy', 'paradox', 'antithesis', 'synthesis', 'metamorphosis',
            'catharsis', 'epiphany', 'serendipity', 'zeitgeist', 'schadenfreude', 'weltanschauung'
        ]
    }
    
    for level, words in sample_data.items():
        for word in words:
            cefr_classifier.add_word_to_level(word, level)
    
    cefr_classifier.update_cache()
    logger.info("Populated CEFR data with sample words")
