"""
Audio fetching service for Cambridge Dictionary
"""
import requests
from lxml import html
import time
import logging
from urllib.parse import urljoin
from django.conf import settings

logger = logging.getLogger(__name__)

class CambridgeAudioFetcher:
    """Service to fetch audio URLs from Cambridge Dictionary"""
    
    BASE_URL = "https://dictionary.cambridge.org"
    DICTIONARY_URL = "https://dictionary.cambridge.org/dictionary/english/{word}"
    AUDIO_XPATH = '//*[@id="audio1"]/source[1]'
    
    # Rate limiting settings
    REQUEST_DELAY = 1.0  # Delay between requests in seconds
    MAX_RETRIES = 3
    TIMEOUT = 10
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to Cambridge Dictionary"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.REQUEST_DELAY:
            sleep_time = self.REQUEST_DELAY - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_audio_url(self, word):
        """
        Fetch audio URL for a given word from Cambridge Dictionary
        
        Args:
            word (str): The word to fetch audio for
            
        Returns:
            str or None: The audio URL if found, None otherwise
        """
        if not word or not word.strip():
            return None
        
        word = word.strip().lower()
        url = self.DICTIONARY_URL.format(word=word)
        
        logger.info(f"Fetching audio for word: {word}")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Rate limiting
                self._rate_limit()
                
                # Make request
                response = self.session.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
                
                # Parse HTML
                tree = html.fromstring(response.content)
                
                # Find audio element using XPath
                audio_elements = tree.xpath(self.AUDIO_XPATH)
                
                if audio_elements:
                    audio_element = audio_elements[0]
                    src = audio_element.get('src')
                    
                    if src:
                        # Construct full URL
                        if src.startswith('/'):
                            audio_url = urljoin(self.BASE_URL, src)
                        else:
                            audio_url = src
                        
                        logger.info(f"Found audio URL for '{word}': {audio_url}")
                        return audio_url
                    else:
                        logger.warning(f"Audio element found for '{word}' but no src attribute")
                else:
                    logger.info(f"No audio found for word: {word}")
                
                return None
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for word '{word}' (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch audio for word '{word}' after {self.MAX_RETRIES} attempts")
            
            except Exception as e:
                logger.error(f"Unexpected error fetching audio for word '{word}': {e}")
                break
        
        return None
    
    def fetch_audio_for_multiple_words(self, words):
        """
        Fetch audio URLs for multiple words
        
        Args:
            words (list): List of words to fetch audio for
            
        Returns:
            dict: Dictionary mapping words to their audio URLs (or None if not found)
        """
        results = {}
        
        for word in words:
            audio_url = self.fetch_audio_url(word)
            results[word] = audio_url
            
            # Additional delay between words to be extra respectful
            if len(words) > 1:
                time.sleep(0.5)
        
        return results


# Global instance
cambridge_audio_fetcher = CambridgeAudioFetcher()


def fetch_audio_for_word(word):
    """
    Convenience function to fetch audio for a single word
    
    Args:
        word (str): The word to fetch audio for
        
    Returns:
        str or None: The audio URL if found, None otherwise
    """
    return cambridge_audio_fetcher.fetch_audio_url(word)


def fetch_audio_for_words(words):
    """
    Convenience function to fetch audio for multiple words
    
    Args:
        words (list): List of words to fetch audio for
        
    Returns:
        dict: Dictionary mapping words to their audio URLs
    """
    return cambridge_audio_fetcher.fetch_audio_for_multiple_words(words)
