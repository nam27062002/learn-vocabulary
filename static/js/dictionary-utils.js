/**
 * Dictionary Utilities - Fallback mechanism for Cambridge Dictionary links
 * 
 * This module provides utilities for handling dictionary links with fallback support.
 * If the main Cambridge Dictionary site fails to load, it automatically redirects
 * to the specific word definition page.
 */

class DictionaryUtils {
    static CAMBRIDGE_BASE_URL = 'https://dictionary.cambridge.org';
    static CAMBRIDGE_WORD_URL = 'https://dictionary.cambridge.org/dictionary/english/';
    static TIMEOUT_MS = 5000; // 5 seconds timeout
    static RETRY_DELAY_MS = 1000; // 1 second delay before fallback

    /**
     * Opens a dictionary link with fallback mechanism
     * @param {string} word - The word to look up
     * @param {Object} options - Configuration options
     * @param {boolean} options.newTab - Whether to open in new tab (default: true)
     * @param {Function} options.onFallback - Callback when fallback is used
     * @param {Function} options.onError - Callback when both attempts fail
     */
    static async openDictionaryLink(word, options = {}) {
        const {
            newTab = true,
            onFallback = null,
            onError = null
        } = options;

        if (!word || typeof word !== 'string') {
            console.error('DictionaryUtils: Invalid word provided');
            if (onError) onError(new Error('Invalid word provided'));
            return;
        }

        const encodedWord = encodeURIComponent(word.trim());
        const primaryUrl = this.CAMBRIDGE_BASE_URL;
        const fallbackUrl = `${this.CAMBRIDGE_WORD_URL}${encodedWord}`;

        console.log(`DictionaryUtils: Attempting to open dictionary for word: ${word}`);

        try {
            // First attempt: Try to open the main Cambridge Dictionary site
            const isMainSiteAccessible = await this.checkSiteAccessibility(primaryUrl);
            
            if (isMainSiteAccessible) {
                console.log('DictionaryUtils: Main Cambridge Dictionary site is accessible');
                this.openUrl(primaryUrl, newTab);
                return;
            }

            // If main site is not accessible, wait a moment and try fallback
            console.log('DictionaryUtils: Main site not accessible, using fallback...');
            await this.delay(this.RETRY_DELAY_MS);

            if (onFallback) {
                onFallback(word, fallbackUrl);
            }

            this.openUrl(fallbackUrl, newTab);
            console.log(`DictionaryUtils: Opened fallback URL: ${fallbackUrl}`);

        } catch (error) {
            console.error('DictionaryUtils: Error in openDictionaryLink:', error);
            
            // As a last resort, try to open the fallback URL anyway
            try {
                this.openUrl(fallbackUrl, newTab);
                console.log(`DictionaryUtils: Opened fallback URL as last resort: ${fallbackUrl}`);
            } catch (fallbackError) {
                console.error('DictionaryUtils: Failed to open fallback URL:', fallbackError);
                if (onError) {
                    onError(fallbackError);
                }
            }
        }
    }

    /**
     * Checks if a website is accessible
     * @param {string} url - The URL to check
     * @returns {Promise<boolean>} - True if accessible, false otherwise
     */
    static async checkSiteAccessibility(url) {
        return new Promise((resolve) => {
            const timeoutId = setTimeout(() => {
                resolve(false);
            }, this.TIMEOUT_MS);

            // Use fetch with no-cors mode to avoid CORS issues
            // We're just checking if the site responds, not reading the content
            fetch(url, {
                method: 'HEAD',
                mode: 'no-cors',
                cache: 'no-cache'
            })
            .then(() => {
                clearTimeout(timeoutId);
                resolve(true);
            })
            .catch(() => {
                clearTimeout(timeoutId);
                resolve(false);
            });
        });
    }

    /**
     * Opens a URL in the current window or new tab
     * @param {string} url - The URL to open
     * @param {boolean} newTab - Whether to open in new tab
     */
    static openUrl(url, newTab = true) {
        if (newTab) {
            window.open(url, '_blank', 'noopener,noreferrer');
        } else {
            window.location.href = url;
        }
    }

    /**
     * Creates a clickable dictionary link element
     * @param {string} word - The word to create link for
     * @param {Object} options - Configuration options
     * @param {string} options.className - CSS class for the link
     * @param {string} options.text - Text to display (defaults to word)
     * @param {Function} options.onFallback - Callback when fallback is used
     * @param {Function} options.onError - Callback when both attempts fail
     * @returns {HTMLElement} - The created link element
     */
    static createDictionaryLink(word, options = {}) {
        const {
            className = 'word-link',
            text = word,
            onFallback = null,
            onError = null
        } = options;

        const link = document.createElement('a');
        link.textContent = text;
        link.className = className;
        link.href = '#';
        link.setAttribute('data-word', word);
        
        // Prevent default link behavior and use our fallback mechanism
        link.addEventListener('click', (event) => {
            event.preventDefault();
            this.openDictionaryLink(word, {
                newTab: true,
                onFallback,
                onError
            });
        });

        return link;
    }

    /**
     * Utility function to add delay
     * @param {number} ms - Milliseconds to delay
     * @returns {Promise} - Promise that resolves after delay
     */
    static delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Creates a dictionary link with fallback for existing anchor elements
     * @param {HTMLElement} linkElement - Existing anchor element
     * @param {string} word - The word to look up
     * @param {Object} options - Configuration options
     */
    static enhanceExistingLink(linkElement, word, options = {}) {
        if (!linkElement || linkElement.tagName !== 'A') {
            console.error('DictionaryUtils: Invalid link element provided');
            return;
        }

        const {
            onFallback = null,
            onError = null
        } = options;

        // Store original href as fallback
        const originalHref = linkElement.href;
        
        // Override click behavior
        linkElement.addEventListener('click', (event) => {
            event.preventDefault();
            this.openDictionaryLink(word, {
                newTab: true,
                onFallback: (word, fallbackUrl) => {
                    console.log(`DictionaryUtils: Using fallback for ${word}: ${fallbackUrl}`);
                    if (onFallback) onFallback(word, fallbackUrl);
                },
                onError: (error) => {
                    console.error('DictionaryUtils: Both attempts failed, using original href');
                    // As absolute last resort, use original href
                    window.open(originalHref, '_blank', 'noopener,noreferrer');
                    if (onError) onError(error);
                }
            });
        });
    }
}

// Export for use in other modules
window.DictionaryUtils = DictionaryUtils;
