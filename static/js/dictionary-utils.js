/**
 * Dictionary Utilities - Intelligent fallback mechanism for dictionary links
 *
 * This module provides utilities for handling dictionary links with intelligent fallback support.
 * Primary: Cambridge Dictionary (https://dictionary.cambridge.org/dictionary/english/{word})
 * Fallback: Oxford Learner's Dictionary (https://www.oxfordlearnersdictionaries.com/definition/english/{word})
 *
 * If Cambridge Dictionary is slow (>3 seconds) or unresponsive, automatically switches to Oxford.
 */

class DictionaryUtils {
  static CAMBRIDGE_BASE_URL = "https://dictionary.cambridge.org";
  static CAMBRIDGE_WORD_URL =
    "https://dictionary.cambridge.org/dictionary/english/";
  static OXFORD_WORD_URL =
    "https://www.oxfordlearnersdictionaries.com/definition/english/";
  static TIMEOUT_MS = 3000; // 3 seconds timeout for faster fallback
  static RETRY_DELAY_MS = 500; // 0.5 second delay before fallback

  /**
   * Opens a dictionary link with intelligent fallback mechanism
   * @param {string} word - The word to look up
   * @param {Object} options - Configuration options
   * @param {boolean} options.newTab - Whether to open in new tab (default: true)
   * @param {Function} options.onFallback - Callback when fallback is used
   * @param {Function} options.onError - Callback when both attempts fail
   */
  static async openDictionaryLink(word, options = {}) {
    const { newTab = true, onFallback = null, onError = null } = options;

    if (!word || typeof word !== "string") {
      console.error("DictionaryUtils: Invalid word provided");
      if (onError) onError(new Error("Invalid word provided"));
      return;
    }

    const encodedWord = encodeURIComponent(word.trim().toLowerCase());
    const cambridgeUrl = `${this.CAMBRIDGE_WORD_URL}${encodedWord}`;
    const oxfordUrl = `${this.OXFORD_WORD_URL}${encodedWord}`;

    console.log(`🔍 DictionaryUtils: Looking up word "${word}"`);
    console.log(`📖 Primary URL (Cambridge): ${cambridgeUrl}`);
    console.log(`📚 Fallback URL (Oxford): ${oxfordUrl}`);

    try {
      // First attempt: Try Cambridge Dictionary with response time check
      console.log("⏱️ Testing Cambridge Dictionary response time...");
      const cambridgeAccessible = await this.checkSiteAccessibility(
        cambridgeUrl
      );

      if (cambridgeAccessible) {
        console.log("✅ Cambridge Dictionary is accessible and responsive");
        this.openUrl(cambridgeUrl, newTab);
        return;
      }

      // Cambridge failed or too slow, use Oxford fallback
      console.log(
        "⚠️ Cambridge Dictionary is slow/unresponsive, switching to Oxford..."
      );
      await this.delay(this.RETRY_DELAY_MS);

      if (onFallback) {
        onFallback(word, oxfordUrl);
      }

      console.log("📚 Opening Oxford Learner's Dictionary as fallback");
      this.openUrl(oxfordUrl, newTab);
    } catch (error) {
      console.error("❌ DictionaryUtils: Error in openDictionaryLink:", error);

      // Last resort: try Oxford anyway
      console.log("🆘 Last resort: attempting Oxford Dictionary...");
      try {
        this.openUrl(oxfordUrl, newTab);
        if (onFallback) {
          onFallback(word, oxfordUrl);
        }
      } catch (finalError) {
        console.error("❌ All dictionary attempts failed:", finalError);
        if (onError) {
          onError(finalError);
        } else {
          // Absolute last resort: open Cambridge anyway
          this.openUrl(cambridgeUrl, newTab);
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
        method: "HEAD",
        mode: "no-cors",
        cache: "no-cache",
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
      window.open(url, "_blank", "noopener,noreferrer");
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
      className = "word-link",
      text = word,
      onFallback = null,
      onError = null,
    } = options;

    const link = document.createElement("a");
    link.textContent = text;
    link.className = className;
    link.href = "#";
    link.setAttribute("data-word", word);

    // Prevent default link behavior and use our fallback mechanism
    link.addEventListener("click", (event) => {
      event.preventDefault();
      this.openDictionaryLink(word, {
        newTab: true,
        onFallback,
        onError,
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
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Creates a dictionary link with fallback for existing anchor elements
   * @param {HTMLElement} linkElement - Existing anchor element
   * @param {string} word - The word to look up
   * @param {Object} options - Configuration options
   */
  static enhanceExistingLink(linkElement, word, options = {}) {
    if (!linkElement || linkElement.tagName !== "A") {
      console.error("DictionaryUtils: Invalid link element provided");
      return;
    }

    const { onFallback = null, onError = null } = options;

    // Store original href as fallback
    const originalHref = linkElement.href;

    // Override click behavior
    linkElement.addEventListener("click", (event) => {
      event.preventDefault();
      this.openDictionaryLink(word, {
        newTab: true,
        onFallback: (word, fallbackUrl) => {
          console.log(
            `DictionaryUtils: Using fallback for ${word}: ${fallbackUrl}`
          );
          if (onFallback) onFallback(word, fallbackUrl);
        },
        onError: (error) => {
          console.error(
            "DictionaryUtils: Both attempts failed, using original href"
          );
          // As absolute last resort, use original href
          window.open(originalHref, "_blank", "noopener,noreferrer");
          if (onError) onError(error);
        },
      });
    });
  }
}

// Export for use in other modules
window.DictionaryUtils = DictionaryUtils;
