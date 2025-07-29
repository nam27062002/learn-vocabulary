"""
Audio fetching service for Cambridge Dictionary
"""
import requests
from lxml import html
import time
import logging
from urllib.parse import urljoin
from django.conf import settings
from dataclasses import dataclass
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

@dataclass
class AudioOption:
    """Data structure for audio pronunciation options"""
    url: str
    label: str  # e.g., "US pronunciation", "UK pronunciation"
    selector_source: str  # e.g., "audio1", "audio2"
    is_valid: bool
    error_message: Optional[str] = None

# Configuration for multiple audio source selectors
AUDIO_SELECTORS = [
    {
        'id': 'audio1',
        'xpath': '//*[@id="audio1"]/source[1]',
        'label_xpath': '//*[@id="audio1"]/../span[@class="region"]',
        'default_label': 'Primary pronunciation'
    },
    {
        'id': 'audio2',
        'xpath': '//*[@id="audio2"]/source[1]',
        'label_xpath': '//*[@id="audio2"]/../span[@class="region"]',
        'default_label': 'Alternative pronunciation'
    }
]

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


class EnhancedCambridgeAudioFetcher(CambridgeAudioFetcher):
    """Enhanced audio fetcher that supports multiple audio sources and pronunciation options"""

    def __init__(self):
        super().__init__()
        self.audio_selectors = AUDIO_SELECTORS

    def fetch_multiple_audio_sources(self, word: str) -> List[AudioOption]:
        """
        Fetch multiple audio sources for a given word from Cambridge Dictionary

        Args:
            word (str): The word to fetch audio for

        Returns:
            List[AudioOption]: List of available audio options
        """
        if not word or not word.strip():
            return []

        word = word.strip().lower()
        url = self.DICTIONARY_URL.format(word=word)

        logger.info(f"Fetching multiple audio sources for word: {word}")

        for attempt in range(self.MAX_RETRIES):
            try:
                # Rate limiting
                self._rate_limit()

                # Make request
                response = self.session.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()

                # Parse HTML
                tree = html.fromstring(response.content)

                # Extract audio from multiple selectors
                audio_options = self.extract_audio_from_multiple_selectors(tree)

                # Validate audio URLs
                validated_options = self.validate_audio_urls(audio_options)

                logger.info(f"Found {len(validated_options)} audio options for '{word}'")
                return validated_options

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for word '{word}' (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch audio for word '{word}' after {self.MAX_RETRIES} attempts")

            except Exception as e:
                logger.error(f"Unexpected error fetching audio for word '{word}': {e}")
                break

        return []

    def extract_audio_from_multiple_selectors(self, tree) -> List[Dict]:
        """
        Extract audio URLs from multiple XPath selectors

        Args:
            tree: lxml HTML tree

        Returns:
            List[Dict]: List of audio data dictionaries
        """
        audio_data = []

        for selector_config in self.audio_selectors:
            try:
                # Find audio element using XPath
                audio_elements = tree.xpath(selector_config['xpath'])

                if audio_elements:
                    audio_element = audio_elements[0]
                    src = audio_element.get('src')

                    if src:
                        # Construct full URL
                        if src.startswith('/'):
                            audio_url = urljoin(self.BASE_URL, src)
                        else:
                            audio_url = src

                        # Extract pronunciation label
                        label = self.get_pronunciation_labels(tree, selector_config)

                        audio_data.append({
                            'url': audio_url,
                            'label': label,
                            'selector_source': selector_config['id']
                        })

                        logger.debug(f"Found audio from {selector_config['id']}: {audio_url}")
                    else:
                        logger.debug(f"Audio element found for {selector_config['id']} but no src attribute")
                else:
                    logger.debug(f"No audio element found for {selector_config['id']}")

            except Exception as e:
                logger.warning(f"Error extracting audio from {selector_config['id']}: {e}")
                continue

        return audio_data

    def get_pronunciation_labels(self, tree, selector_config: Dict) -> str:
        """
        Extract pronunciation type labels from Cambridge Dictionary

        Args:
            tree: lxml HTML tree
            selector_config: Selector configuration dictionary

        Returns:
            str: Pronunciation label (e.g., "US pronunciation", "UK pronunciation")
        """
        try:
            # Try to extract label from the page
            label_elements = tree.xpath(selector_config['label_xpath'])

            if label_elements:
                label_text = label_elements[0].text_content().strip()
                if label_text:
                    # Format the label nicely
                    if 'us' in label_text.lower():
                        return 'US pronunciation'
                    elif 'uk' in label_text.lower():
                        return 'UK pronunciation'
                    else:
                        return f"{label_text} pronunciation"

            # Fallback to default label based on selector ID
            if selector_config['id'] == 'audio1':
                return 'US pronunciation'
            elif selector_config['id'] == 'audio2':
                return 'UK pronunciation'
            else:
                return selector_config['default_label']

        except Exception as e:
            logger.debug(f"Error extracting pronunciation label: {e}")
            return selector_config['default_label']

    def validate_audio_urls(self, audio_data: List[Dict]) -> List[AudioOption]:
        """
        Validate audio URLs and create AudioOption objects

        Args:
            audio_data: List of audio data dictionaries

        Returns:
            List[AudioOption]: List of validated audio options
        """
        validated_options = []

        for data in audio_data:
            try:
                # Basic URL validation
                url = data['url']
                if not url or not url.startswith(('http://', 'https://')):
                    continue

                # Create AudioOption object
                audio_option = AudioOption(
                    url=url,
                    label=data['label'],
                    selector_source=data['selector_source'],
                    is_valid=True
                )

                validated_options.append(audio_option)

            except Exception as e:
                logger.warning(f"Error validating audio URL {data.get('url', 'unknown')}: {e}")
                # Create invalid option for debugging
                audio_option = AudioOption(
                    url=data.get('url', ''),
                    label=data.get('label', 'Unknown'),
                    selector_source=data.get('selector_source', 'unknown'),
                    is_valid=False,
                    error_message=str(e)
                )
                validated_options.append(audio_option)

        return validated_options


# Global instances
cambridge_audio_fetcher = CambridgeAudioFetcher()
enhanced_cambridge_audio_fetcher = EnhancedCambridgeAudioFetcher()


def get_enhanced_audio_fetcher():
    """
    Factory function to get enhanced audio fetcher instance

    Returns:
        EnhancedCambridgeAudioFetcher: Enhanced audio fetcher instance
    """
    return enhanced_cambridge_audio_fetcher


def fetch_multiple_audio_options(word: str) -> List[AudioOption]:
    """
    Convenience function to fetch multiple audio options for a word

    Args:
        word (str): The word to fetch audio for

    Returns:
        List[AudioOption]: List of available audio options
    """
    return enhanced_cambridge_audio_fetcher.fetch_multiple_audio_sources(word)


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
