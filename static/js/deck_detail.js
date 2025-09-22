// static/js/deck_detail.js

document.addEventListener("DOMContentLoaded", function () {
  const carouselContainer = document.querySelector("#carousel-container");
  if (!carouselContainer) {
    return;
  }

  const carouselSlides = carouselContainer.querySelector("#carousel-slides");
  const slides = Array.from(carouselSlides.children);
  const prevBtn = document.querySelector("#prevBtn");
  const nextBtn = document.querySelector("#nextBtn");
  const paginationDotsContainer = document.querySelector("#pagination-dots");

  let currentSlideIndex = 0;

  function showSlide(index) {
    // Ensure the index loops around
    if (index < 0) {
      currentSlideIndex = slides.length - 1;
    } else if (index >= slides.length) {
      currentSlideIndex = 0;
    } else {
      currentSlideIndex = index;
    }

    const currentSlide = slides[currentSlideIndex];

    // The scrollLeft will be the offset of the current slide
    const targetScrollLeft = currentSlide.offsetLeft;

    carouselSlides.scrollTo({
      left: targetScrollLeft,
      behavior: "smooth",
    });

    // Apply shadow/peek effect dynamically via inline styles
    slides.forEach((slide, i) => {
      if (i === currentSlideIndex) {
        slide.style.opacity = "1";
        slide.style.transform = "scale(1)";
        slide.style.zIndex = "2";
      } else {
        slide.style.opacity = "0.7";
        slide.style.transform = "scale(0.9)";
        slide.style.zIndex = "1";
      }
    });

    updatePagination();
  }

  function nextSlide() {
    currentSlideIndex++;
    showSlide(currentSlideIndex);
  }

  function prevSlide() {
    currentSlideIndex--;
    showSlide(currentSlideIndex);
  }

  function updatePagination() {
    if (paginationDotsContainer) {
      paginationDotsContainer.innerHTML = "";
      slides.forEach((_, index) => {
        const dot = document.createElement("span");
        dot.classList.add("pagination-dot");
        if (index === currentSlideIndex) {
          dot.classList.add("active");
        }
        dot.addEventListener("click", () => {
          // Disable pagination during edit mode
          if (document.body.getAttribute("data-edit-mode") === "true") {
            return;
          }

          // Disable pagination during deck name editing
          const deckNameEdit = document.getElementById("deck-name-edit");
          if (deckNameEdit && !deckNameEdit.classList.contains("hidden")) {
            return;
          }

          showSlide(index);
        });
        paginationDotsContainer.appendChild(dot);
      });
    }
  }

  // Event listeners for navigation buttons
  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      // Disable navigation during edit mode
      if (document.body.getAttribute("data-edit-mode") === "true") {
        return;
      }

      // Disable navigation during deck name editing
      const deckNameEdit = document.getElementById("deck-name-edit");
      if (deckNameEdit && !deckNameEdit.classList.contains("hidden")) {
        return;
      }

      prevSlide();
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      // Disable navigation during edit mode
      if (document.body.getAttribute("data-edit-mode") === "true") {
        return;
      }

      // Disable navigation during deck name editing
      const deckNameEdit = document.getElementById("deck-name-edit");
      if (deckNameEdit && !deckNameEdit.classList.contains("hidden")) {
        return;
      }

      nextSlide();
    });
  }

  // Enhanced audio playback function
  function playAudioWithDebug(audioUrl, audioIcon) {
    console.log(`[AUDIO DEBUG] Attempting to play audio: ${audioUrl}`);

    if (!audioUrl) {
      console.error("[AUDIO DEBUG] No audio URL provided");
      return;
    }

    try {
      const audio = new Audio(audioUrl);

      // Add comprehensive event listeners for debugging
      audio.addEventListener('loadstart', () => {
        console.log(`[AUDIO DEBUG] Loading started for: ${audioUrl}`);
      });

      audio.addEventListener('canplay', () => {
        console.log(`[AUDIO DEBUG] Audio can start playing: ${audioUrl}`);
      });

      audio.addEventListener('play', () => {
        console.log(`[AUDIO DEBUG] Audio playback started: ${audioUrl}`);
        // Visual feedback - briefly change icon color
        if (audioIcon) {
          audioIcon.style.color = '#10b981'; // Green
          setTimeout(() => {
            audioIcon.style.color = ''; // Reset to default
          }, 1000);
        }
      });

      audio.addEventListener('ended', () => {
        console.log(`[AUDIO DEBUG] Audio playback ended: ${audioUrl}`);
      });

      audio.addEventListener('error', (e) => {
        console.error(`[AUDIO DEBUG] Audio error for ${audioUrl}:`, e);
        console.error(`[AUDIO DEBUG] Error details:`, {
          code: e.target?.error?.code,
          message: e.target?.error?.message,
          networkState: e.target?.networkState,
          readyState: e.target?.readyState
        });

        // Visual feedback for error
        if (audioIcon) {
          audioIcon.style.color = '#ef4444'; // Red
          setTimeout(() => {
            audioIcon.style.color = ''; // Reset to default
          }, 2000);
        }
      });

      // Attempt to play with promise handling
      const playPromise = audio.play();

      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            console.log(`[AUDIO DEBUG] Audio play() promise resolved for: ${audioUrl}`);
          })
          .catch((e) => {
            console.error(`[AUDIO DEBUG] Audio playback promise rejected for ${audioUrl}:`, e);

            // Handle specific autoplay policy errors
            if (e.name === 'NotAllowedError') {
              console.warn(`[AUDIO DEBUG] Autoplay blocked by browser policy. User interaction required.`);
            } else if (e.name === 'NotSupportedError') {
              console.error(`[AUDIO DEBUG] Audio format not supported.`);
            } else if (e.name === 'AbortError') {
              console.warn(`[AUDIO DEBUG] Audio playback aborted.`);
            }
          });
      }

    } catch (e) {
      console.error(`[AUDIO DEBUG] Error creating Audio object for ${audioUrl}:`, e);
    }
  }

  // Enhanced event listener for audio icons with better event handling
  carouselSlides.addEventListener("click", function (event) {
    // Check for audio icon click first (highest priority)
    const audioIcon = event.target.closest(".audio-icon-tailwind");
    if (audioIcon) {
      console.log(`[AUDIO DEBUG] Audio icon clicked`);

      // Prevent event bubbling to avoid conflicts
      event.preventDefault();
      event.stopPropagation();

      const audioUrl = audioIcon.dataset.audioUrl;
      console.log(`[AUDIO DEBUG] Audio URL from dataset:`, audioUrl);

      if (audioUrl) {
        playAudioWithDebug(audioUrl, audioIcon);
      } else {
        console.error(`[AUDIO DEBUG] No audio URL found in dataset`);
      }
      return;
    }

    // Handle edit button clicks
    const editBtn = event.target.closest(".edit-card-btn");
    if (editBtn) {
      const cardContainer = editBtn.closest("[data-card-id]");
      enterEditMode(cardContainer);
      return;
    }

    // Handle save button clicks
    const saveBtn = event.target.closest(".save-card-btn");
    if (saveBtn) {
      const cardContainer = saveBtn.closest("[data-card-id]");
      saveCardChanges(cardContainer);
      return;
    }

    // Handle cancel button clicks
    const cancelBtn = event.target.closest(".cancel-edit-btn");
    if (cancelBtn) {
      const cardContainer = cancelBtn.closest("[data-card-id]");
      cancelEdit(cardContainer);
      return;
    }

    // Handle enhanced audio button clicks
    const enhancedAudioBtn = event.target.closest(".enhanced-audio-btn");
    if (enhancedAudioBtn) {
      const cardId = enhancedAudioBtn.dataset.cardId;
      const word = enhancedAudioBtn.dataset.word;

      if (cardId && word && window.EnhancedAudioManager) {
        window.EnhancedAudioManager.showAudioSelectionModal(cardId, word);
      }
      return;
    }
  });

  // Initial setup
  showSlide(currentSlideIndex);

  // Initialize audio status functionality
  initializeAudioStatusFeatures();

  // Initialize deck name editing functionality
  initializeDeckNameEditing();

  // Initialize audio fetching functionality
  initializeAudioFetching();

  // Initialize dictionary links with fallback mechanism
  initializeDictionaryLinks();

  // Make updateCardDisplay globally available for enhanced audio manager
  window.updateCardDisplay = updateCardDisplay;

  // Make enhanced audio card display function globally available
  window.updateCardDisplayForAudio = updateCardDisplayForAudio;

  // Make updateAudioStats globally available for enhanced audio manager
  window.updateAudioStats = updateAudioStats;

  // Make showMessage globally available for enhanced audio manager
  window.showMessage = showMessage;

  // Keyboard navigation
  document.addEventListener("keydown", function (event) {
    // Handle ESC key to exit edit mode
    if (event.key === "Escape") {
      const editModeCard = document.querySelector(
        ".card-edit-mode:not(.hidden)"
      );
      if (editModeCard) {
        const cardContainer = editModeCard.closest("[data-card-id]");
        if (cardContainer) {
          cancelEdit(cardContainer);
        }
      }
      return;
    }

    // Disable arrow key navigation during edit mode
    if (document.body.getAttribute("data-edit-mode") === "true") {
      return;
    }

    // Disable arrow key navigation during deck name editing
    const deckNameEdit = document.getElementById("deck-name-edit");
    if (deckNameEdit && !deckNameEdit.classList.contains("hidden")) {
      return;
    }

    if (event.key === "ArrowLeft") {
      prevSlide();
    } else if (event.key === "ArrowRight") {
      nextSlide();
    }
  });

  // Swipe/Drag functionality
  let startX;
  let isDragging = false;
  let initialScrollLeft;

  carouselSlides.addEventListener("mousedown", (e) => {
    // Disable drag during edit mode
    if (document.body.getAttribute("data-edit-mode") === "true") {
      return;
    }

    // Disable drag during deck name editing
    const deckNameEdit = document.getElementById("deck-name-edit");
    if (deckNameEdit && !deckNameEdit.classList.contains("hidden")) {
      return;
    }

    isDragging = true;
    startX = e.pageX;
    initialScrollLeft = carouselSlides.scrollLeft;
    carouselSlides.style.cursor = "grabbing";
  });

  carouselSlides.addEventListener("mouseleave", () => {
    if (isDragging) {
      isDragging = false;
      carouselSlides.style.cursor = "grab";
    }
  });

  carouselSlides.addEventListener("mouseup", () => {
    isDragging = false;
    carouselSlides.style.cursor = "grab";
    // When mouseup, let scroll-snap handle the snapping.
    // No need to call showSlide here explicitly for snapping.
  });

  carouselSlides.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    // Disable drag during edit mode
    if (document.body.getAttribute("data-edit-mode") === "true") {
      return;
    }

    // Disable drag during deck name editing
    const deckNameEdit = document.getElementById("deck-name-edit");
    if (deckNameEdit && !deckNameEdit.classList.contains("hidden")) {
      return;
    }

    e.preventDefault();
    const x = e.pageX;
    const walk = (x - startX) * 1.5;
    carouselSlides.scrollLeft = initialScrollLeft - walk;
  });

  carouselSlides.addEventListener("touchend", (e) => {
    // Prevent touch interactions during edit mode
    if (document.body.getAttribute("data-edit-mode") === "true") {
      e.preventDefault();
      return;
    }

    // Prevent touch interactions during deck name editing
    const deckNameEdit = document.getElementById("deck-name-edit");
    if (deckNameEdit && !deckNameEdit.classList.contains("hidden")) {
      e.preventDefault();
      return;
    }

    const endX = e.changedTouches[0].pageX;
    const threshold = 50;
    if (startX - endX > threshold) {
      // Let scroll-snap handle the transition for next/prev
      nextSlide();
    } else if (endX - startX > threshold) {
      // Let scroll-snap handle the transition for next/prev
      prevSlide();
    }
  });

  carouselSlides.addEventListener("touchstart", (e) => {
    startX = e.touches[0].pageX;
    initialScrollLeft = carouselSlides.scrollLeft;
  });

  carouselSlides.addEventListener("touchmove", (e) => {
    // Prevent touch interactions during edit mode
    if (document.body.getAttribute("data-edit-mode") === "true") {
      e.preventDefault();
      return;
    }

    // Prevent touch interactions during deck name editing
    const deckNameEdit = document.getElementById("deck-name-edit");
    if (deckNameEdit && !deckNameEdit.classList.contains("hidden")) {
      e.preventDefault();
      return;
    }

    const x = e.touches[0].pageX;
    const walk = (x - startX) * 1.5;
    carouselSlides.scrollLeft = initialScrollLeft - walk;
  });

  carouselSlides.addEventListener("touchstart", (e) => {
    // Prevent touch interactions during edit mode
    if (document.body.getAttribute("data-edit-mode") === "true") {
      e.preventDefault();
      return;
    }

    // Prevent touch interactions during deck name editing
    const deckNameEdit = document.getElementById("deck-name-edit");
    if (deckNameEdit && !deckNameEdit.classList.contains("hidden")) {
      e.preventDefault();
      return;
    }

    startX = e.touches[0].pageX;
    initialScrollLeft = carouselSlides.scrollLeft;
  });

  // Edit functionality functions - Updated for Modal
  let currentEditingCard = null;

  function enterEditMode(cardContainer) {
    currentEditingCard = cardContainer;
    showEditCardModal(cardContainer);
  }

  function showEditCardModal(cardContainer) {
    const modal = document.getElementById('editCardModal');
    const cardId = cardContainer.dataset.cardId;

    // Get card data
    const viewMode = cardContainer.querySelector('.card-view-mode');
    const word = viewMode.querySelector('.dictionary-word-link').textContent;
    const phoneticElement = viewMode.querySelector('.text-lg.text-gray-400.font-serif.italic span');
    const phonetic = phoneticElement ? phoneticElement.textContent : '';
    const partOfSpeechElement = viewMode.querySelector('.text-lg.text-gray-400.italic');
    const partOfSpeech = partOfSpeechElement ? partOfSpeechElement.textContent.replace(/[()]/g, '').trim() : '';
    const audioIcon = viewMode.querySelector('.audio-icon-tailwind');
    const audioUrl = audioIcon ? audioIcon.dataset.audioUrl : '';

    // Fill modal fields
    document.getElementById('modal-edit-word').value = word;
    document.getElementById('modal-edit-phonetic').value = phonetic;

    // Set part of speech in select dropdown
    const partOfSpeechSelect = document.getElementById('modal-edit-part-of-speech');
    partOfSpeechSelect.value = partOfSpeech.toLowerCase();

    document.getElementById('modal-edit-audio-url').value = audioUrl;

    // Load definitions
    loadDefinitionsToModal(viewMode);

    // Show modal
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
  }

  function hideEditCardModal() {
    const modal = document.getElementById('editCardModal');
    modal.style.display = 'none';
    document.body.style.overflow = '';
    currentEditingCard = null;
  }

  function loadDefinitionsToModal(viewMode) {
    const container = document.getElementById('modal-definitions-container');
    container.innerHTML = '';

    // Get all definition pairs - better selector to find actual definition text
    const definitionElements = viewMode.querySelectorAll('.text-base.text-gray-300.leading-relaxed.mb-2');
    const definitions = [];

    for (let i = 0; i < definitionElements.length; i += 2) {
      const englishEl = definitionElements[i];
      const vietnameseEl = definitionElements[i + 1];

      if (englishEl && vietnameseEl) {
        // Remove the "EN:" and "VI:" labels completely
        let englishText = englishEl.textContent.replace(/^EN:\s*/i, '').trim();
        let vietnameseText = vietnameseEl.textContent.replace(/^VI:\s*/i, '').trim();

        // Also handle cases where the span might contain the prefix
        const englishSpan = englishEl.querySelector('span.font-semibold');
        if (englishSpan) {
          englishText = englishEl.textContent.replace(englishSpan.textContent, '').trim();
        }

        const vietnameseSpan = vietnameseEl.querySelector('span.font-semibold');
        if (vietnameseSpan) {
          vietnameseText = vietnameseEl.textContent.replace(vietnameseSpan.textContent, '').trim();
        }

        if (englishText && vietnameseText) {
          definitions.push({ english: englishText, vietnamese: vietnameseText });
        }
      }
    }

    // Add existing definitions or create one empty pair
    if (definitions.length === 0) {
      addDefinitionPair(container, '', '');
    } else {
      definitions.forEach(def => {
        addDefinitionPair(container, def.english, def.vietnamese);
      });
    }
  }

  function addDefinitionPair(container, englishText = '', vietnameseText = '') {
    const pairDiv = document.createElement('div');
    pairDiv.className = 'modal-definition-pair';

    pairDiv.innerHTML = `
      <div class="definition-pair-header">
        <span class="definition-pair-number">#${container.children.length + 1}</span>
        <button type="button" class="remove-definition" onclick="removeDefinitionPair(this)">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="definition-inputs">
        <div class="definition-input-group">
          <div class="input-label">
            <i class="fas fa-flag text-blue-400"></i>
            <span>English</span>
          </div>
          <textarea
            class="modal-edit-english-def definition-textarea"
            rows="2"
            placeholder="The encountering of risks; a bold undertaking..."
          >${englishText}</textarea>
        </div>

        <div class="definition-input-group">
          <div class="input-label">
            <i class="fas fa-flag text-red-400"></i>
            <span>Vietnamese</span>
          </div>
          <textarea
            class="modal-edit-vietnamese-def definition-textarea"
            rows="2"
            placeholder="cuộc phiêu lưu"
          >${vietnameseText}</textarea>
        </div>
      </div>
    `;

    container.appendChild(pairDiv);

    // Update numbers for all pairs
    updateDefinitionNumbers(container);
  }

  function exitEditMode(cardContainer) {
    // This function is now handled by hideEditCardModal
    hideEditCardModal();
  }

  // Old inline editing functions removed - now using modal

  function saveEditCardModal() {
    if (!currentEditingCard) return;

    const cardId = currentEditingCard.dataset.cardId;

    // Collect form data from modal
    const formData = {
      card_id: cardId,
      word: document.getElementById('modal-edit-word').value.trim(),
      phonetic: document.getElementById('modal-edit-phonetic').value.trim(),
      part_of_speech: document.getElementById('modal-edit-part-of-speech').value.trim(),
      audio_url: document.getElementById('modal-edit-audio-url').value.trim(),
      definitions: [],
    };

    // Collect definitions from modal
    const englishDefs = document.querySelectorAll(".modal-edit-english-def");
    const vietnameseDefs = document.querySelectorAll(".modal-edit-vietnamese-def");

    for (let i = 0; i < englishDefs.length; i++) {
      const englishDef = englishDefs[i].value.trim();
      const vietnameseDef = vietnameseDefs[i]
        ? vietnameseDefs[i].value.trim()
        : "";

      if (englishDef && vietnameseDef) {
        formData.definitions.push({
          english_definition: englishDef,
          vietnamese_definition: vietnameseDef,
        });
      }
    }

    // Validate required fields
    if (!formData.word) {
      showMessage(
        window.manual_texts?.word_required || "Word is required",
        "error"
      );
      return;
    }

    if (formData.definitions.length === 0) {
      showMessage(
        window.manual_texts?.definition_required ||
          "At least one definition is required",
        "error"
      );
      return;
    }

    // Show loading state
    const saveBtn = document.querySelector(".btn-save");
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    saveBtn.disabled = true;

    // Prepare request details (API endpoints don't use language prefixes)
    const requestUrl = `/api/update-flashcard/`;
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    const requestHeaders = {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken ? csrfToken.content : "",
    };
    const requestBody = JSON.stringify(formData);

    // Send update request
    fetch(requestUrl, {
      method: "POST",
      headers: requestHeaders,
      body: requestBody,
    })
      .then((response) => {
        // Check if response is ok first
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Check if response has content before parsing JSON
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
          throw new Error("Server did not return JSON response");
        }

        return response.json();
      })
      .then((data) => {
        if (data.success) {
          updateCardDisplay(currentEditingCard, data.card);
          hideEditCardModal();
          showMessage(
            window.manual_texts?.card_updated_successfully ||
              "Card updated successfully!",
            "success"
          );
        } else {
          showMessage(
            data.error ||
              window.manual_texts?.error_updating_card ||
              "Error updating card",
            "error"
          );
        }
      })
      .catch((error) => {
        console.error("Error updating card:", error);
        let errorMessage =
          window.manual_texts?.error_updating_card || "Error updating card";

        // Provide more specific error messages
        if (error.message.includes("HTTP 405")) {
          errorMessage =
            window.manual_texts?.method_not_allowed ||
            "Method not allowed. Please refresh the page and try again.";
        } else if (error.message.includes("HTTP 403")) {
          errorMessage =
            window.manual_texts?.permission_denied ||
            "Permission denied. Please refresh the page and try again.";
        } else if (error.message.includes("HTTP 404")) {
          errorMessage =
            window.manual_texts?.card_not_found ||
            "Card not found. Please refresh the page and try again.";
        } else if (error.message.includes("JSON")) {
          errorMessage =
            window.manual_texts?.server_response_error ||
            "Server response error. Please try again.";
        }

        showMessage(errorMessage, "error");
      })
      .finally(() => {
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
      });
  }

  function updateCardDisplay(cardContainer, cardData) {
    const viewMode = cardContainer.querySelector(".card-view-mode");

    // Update word
    const wordLink = viewMode.querySelector("a");
    if (wordLink) {
      wordLink.textContent = cardData.word;
      wordLink.href = `https://dictionary.cambridge.org/dictionary/english/${cardData.word}`;
      wordLink.setAttribute("data-word", cardData.word);

      // Enhance the updated link with fallback mechanism if DictionaryUtils is available
      if (typeof window.DictionaryUtils !== "undefined") {
        DictionaryUtils.enhanceExistingLink(wordLink, cardData.word, {
          onFallback: (word, fallbackUrl) => {
            console.log(
              `Deck Detail: Using fallback dictionary URL for updated word ${word}: ${fallbackUrl}`
            );
          },
          onError: (error) => {
            console.error(
              `Deck Detail: Dictionary fallback failed for updated word ${cardData.word}:`,
              error
            );
          },
        });
      }
    }

    // Update part of speech
    const posElement = viewMode.querySelector(
      ".text-lg.text-gray-400.mb-2.italic"
    );
    if (posElement) {
      if (cardData.part_of_speech) {
        posElement.textContent = `(${cardData.part_of_speech})`;
        posElement.style.display = "block";
      } else {
        posElement.style.display = "none";
      }
    }

    // Update phonetic and audio
    const phoneticContainer = viewMode.querySelector(
      ".text-lg.text-gray-400.font-serif.italic.mb-4"
    );
    if (phoneticContainer) {
      const phoneticSpan = phoneticContainer.querySelector("span");
      const audioBtn = phoneticContainer.querySelector(".audio-icon-tailwind");

      if (cardData.phonetic) {
        phoneticSpan.textContent = cardData.phonetic;
        phoneticContainer.style.display = "flex";

        if (cardData.audio_url && audioBtn) {
          audioBtn.dataset.audioUrl = cardData.audio_url;
          audioBtn.style.display = "block";
        } else if (audioBtn) {
          audioBtn.style.display = "none";
        }
      } else {
        phoneticContainer.style.display = "none";
      }
    }

    // Update definitions
    const definitionContainers = viewMode.querySelectorAll(
      ".text-base.text-gray-300.leading-relaxed.mb-2"
    );

    // Remove existing definitions
    definitionContainers.forEach((container) => container.remove());

    // Add new definitions
    if (cardData.definitions && cardData.definitions.length > 0) {
      cardData.definitions.forEach((def) => {
        const englishDiv = document.createElement("div");
        englishDiv.className = "text-base text-gray-300 leading-relaxed mb-2";
        englishDiv.innerHTML = `<span class="font-semibold text-primary-color">EN:</span> ${def.english_definition}`;

        const vietnameseDiv = document.createElement("div");
        vietnameseDiv.className =
          "text-base text-gray-300 leading-relaxed mb-2";
        vietnameseDiv.innerHTML = `<span class="font-semibold text-primary-color">VI:</span> ${def.vietnamese_definition}`;

        viewMode.appendChild(englishDiv);
        viewMode.appendChild(vietnameseDiv);
      });
    } else {
      // Show a message if no definitions
      const noDefDiv = document.createElement("div");
      noDefDiv.className =
        "text-base text-gray-400 leading-relaxed mb-2 italic";
      noDefDiv.textContent =
        window.manual_texts?.no_definitions_available ||
        "No definitions available";
      viewMode.appendChild(noDefDiv);
    }

    // Update audio status after updating display
    updateAudioStatusAfterSave(cardContainer, cardData);
  }

  function showMessage(message, type) {
    // Create message element
    const messageDiv = document.createElement("div");
    messageDiv.className = `fixed top-4 right-4 px-6 py-3 rounded-md text-white font-medium z-50 transition-all duration-300 ${
      type === "success" ? "bg-green-600" : "bg-red-600"
    }`;
    messageDiv.textContent = message;

    document.body.appendChild(messageDiv);

    // Auto remove after 3 seconds
    setTimeout(() => {
      messageDiv.style.opacity = "0";
      setTimeout(() => {
        if (messageDiv.parentNode) {
          messageDiv.parentNode.removeChild(messageDiv);
        }
      }, 300);
    }, 3000);
  }

  // Edit mode state management functions
  function enableEditModeState() {
    document.body.setAttribute("data-edit-mode", "true");

    // Disable scroll-snap behavior
    carouselSlides.style.scrollSnapType = "none";

    // Add visual feedback
    carouselSlides.style.cursor = "default";

    // Prevent accidental scrolling
    carouselSlides.style.overflowX = "hidden";
  }

  function disableEditModeState() {
    document.body.removeAttribute("data-edit-mode");

    // Re-enable scroll-snap behavior
    carouselSlides.style.scrollSnapType = "x mandatory";

    // Restore cursor
    carouselSlides.style.cursor = "grab";

    // Re-enable scrolling
    carouselSlides.style.overflowX = "auto";
  }

  // Browser audio support testing
  function testBrowserAudioSupport() {
    console.log(`[AUDIO DEBUG] ========== TESTING BROWSER AUDIO SUPPORT ==========`);

    try {
      const testAudio = new Audio();
      console.log(`[AUDIO DEBUG] Audio constructor supported: ✅`);

      // Test audio formats
      const formats = [
        { ext: 'MP3', mime: 'audio/mpeg' },
        { ext: 'WAV', mime: 'audio/wav' },
        { ext: 'OGG', mime: 'audio/ogg' }
      ];

      formats.forEach(format => {
        const canPlay = testAudio.canPlayType(format.mime);
        if (canPlay === 'probably') {
          console.log(`[AUDIO DEBUG] ${format.ext} format: Probably supported ✅`);
        } else if (canPlay === 'maybe') {
          console.log(`[AUDIO DEBUG] ${format.ext} format: Maybe supported ⚠️`);
        } else {
          console.log(`[AUDIO DEBUG] ${format.ext} format: Not supported ❌`);
        }
      });

      // Test autoplay policy
      testAudio.muted = true;
      const autoplayPromise = testAudio.play();
      if (autoplayPromise !== undefined) {
        autoplayPromise
          .then(() => {
            console.log(`[AUDIO DEBUG] Autoplay allowed (muted) ✅`);
            testAudio.pause();
          })
          .catch(() => {
            console.log(`[AUDIO DEBUG] Autoplay blocked even when muted ⚠️`);
          });
      }

    } catch (e) {
      console.error(`[AUDIO DEBUG] Audio constructor not supported ❌:`, e);
    }
  }

  // Audio icon debugging function
  function debugAudioIcons() {
    console.log(`[AUDIO DEBUG] ========== DEBUGGING AUDIO ICONS ==========`);

    const audioIcons = document.querySelectorAll('.audio-icon-tailwind');
    console.log(`[AUDIO DEBUG] Found ${audioIcons.length} audio icons`);

    audioIcons.forEach((icon, index) => {
      const audioUrl = icon.dataset.audioUrl;
      const hasUrl = !!audioUrl;
      console.log(`[AUDIO DEBUG] Icon ${index + 1}:`, {
        hasAudioUrl: hasUrl,
        audioUrl: audioUrl,
        element: icon
      });

      // Test if the icon is clickable
      const rect = icon.getBoundingClientRect();
      const isVisible = rect.width > 0 && rect.height > 0;
      console.log(`[AUDIO DEBUG] Icon ${index + 1} visibility:`, {
        visible: isVisible,
        width: rect.width,
        height: rect.height,
        top: rect.top,
        left: rect.left
      });
    });

    // Test if carousel slides container exists
    const carousel = document.querySelector('#carousel-slides');
    if (carousel) {
      console.log(`[AUDIO DEBUG] Carousel slides container found`);
    } else {
      console.error(`[AUDIO DEBUG] Carousel slides container NOT found`);
    }
  }

  // Add direct event listeners to audio icons for better reliability
  function initializeAudioIconListeners() {
    console.log(`[AUDIO DEBUG] ========== INITIALIZING DIRECT AUDIO ICON LISTENERS ==========`);

    const audioIcons = document.querySelectorAll('.audio-icon-tailwind');
    console.log(`[AUDIO DEBUG] Found ${audioIcons.length} audio icons for direct listeners`);

    audioIcons.forEach((icon, index) => {
      // Remove any existing listeners to avoid duplicates
      icon.removeEventListener('click', handleAudioIconClick);

      // Add new listener
      icon.addEventListener('click', handleAudioIconClick);

      console.log(`[AUDIO DEBUG] Direct listener added to icon ${index + 1}`);
    });
  }

  // Dedicated audio icon click handler
  function handleAudioIconClick(event) {
    console.log(`[AUDIO DEBUG] Direct audio icon click handler triggered`);

    // Prevent any event bubbling or default behavior
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    const audioIcon = event.currentTarget;
    const audioUrl = audioIcon.dataset.audioUrl;

    console.log(`[AUDIO DEBUG] Direct handler - Audio URL:`, audioUrl);

    if (audioUrl) {
      playAudioWithDebug(audioUrl, audioIcon);
    } else {
      console.error(`[AUDIO DEBUG] Direct handler - No audio URL found`);
    }
  }

  // Audio status functionality
  function initializeAudioStatusFeatures() {
    console.log(`[DEBUG] ========== INITIALIZING AUDIO STATUS FEATURES ==========`);

    // Test browser audio support first
    testBrowserAudioSupport();

    // Debug audio icons
    debugAudioIcons();

    // Initialize direct audio icon listeners
    initializeAudioIconListeners();
    console.log(`[DEBUG] DOM ready state: ${document.readyState}`);
    console.log(`[DEBUG] Current time: ${new Date().toISOString()}`);

    // Check initial DOM state
    const initialCards = document.querySelectorAll("[data-card-id]");
    console.log(`[DEBUG] Initial DOM scan: Found ${initialCards.length} elements with [data-card-id]`);

    updateAudioStats();
    setupAudioFilter();
    setupAudioUrlFieldHandlers();

    console.log(`[DEBUG] ========== AUDIO STATUS FEATURES INITIALIZED ==========`);
  }

  function updateAudioStats() {
    console.log(`[DEBUG] ========== AUDIO STATS DEBUG START ==========`);
    console.log(`[DEBUG] Called from:`, new Error().stack.split('\n')[2].trim());
    console.log(`[DEBUG] Timestamp: ${new Date().toISOString()}`);

    // Get all elements with data-card-id attribute
    const allElements = document.querySelectorAll("[data-card-id]");
    console.log(`[DEBUG] DOM Query Result: Found ${allElements.length} elements with [data-card-id]`);

    // Filter to only get card containers (not favorite buttons or other elements)
    const allCards = Array.from(allElements).filter(element => {
      const hasViewMode = element.querySelector(".card-view-mode");
      const isCardContainer = element.classList.contains("flex-shrink-0");
      console.log(`[DEBUG] Element analysis: tagName=${element.tagName}, hasViewMode=${!!hasViewMode}, isCardContainer=${isCardContainer}, classes="${element.className}"`);
      return hasViewMode && isCardContainer;
    });

    console.log(`[DEBUG] Filtered to ${allCards.length} actual card containers`);

    // Check for duplicate card IDs
    const cardIds = [];
    const duplicateIds = [];
    const cardDetails = [];

    allCards.forEach((card, index) => {
      const cardId = card.getAttribute("data-card-id");
      const isVisible = card.style.display !== "none";
      const hasViewMode = !!card.querySelector(".card-view-mode");
      const hasEditMode = !!card.querySelector(".card-edit-mode");
      const cardClasses = card.className;
      const cardPosition = card.getBoundingClientRect();

      // Track card IDs for duplicate detection
      if (cardIds.includes(cardId)) {
        duplicateIds.push(cardId);
      } else {
        cardIds.push(cardId);
      }

      // Collect detailed info about each card element
      cardDetails.push({
        index: index + 1,
        cardId: cardId,
        isVisible: isVisible,
        hasViewMode: hasViewMode,
        hasEditMode: hasEditMode,
        classes: cardClasses,
        position: `x:${Math.round(cardPosition.x)}, y:${Math.round(cardPosition.y)}, w:${Math.round(cardPosition.width)}, h:${Math.round(cardPosition.height)}`,
        element: card
      });

      console.log(`[DEBUG] Element ${index + 1}:`);
      console.log(`  - Card ID: ${cardId}`);
      console.log(`  - Visible: ${isVisible} (display: ${card.style.display || 'default'})`);
      console.log(`  - Has View Mode: ${hasViewMode}`);
      console.log(`  - Has Edit Mode: ${hasEditMode}`);
      console.log(`  - Classes: ${cardClasses}`);
      console.log(`  - Position: ${cardPosition.x}, ${cardPosition.y} (${cardPosition.width}x${cardPosition.height})`);
    });

    // Report duplicate detection results
    console.log(`[DEBUG] Unique Card IDs: [${cardIds.join(', ')}]`);
    if (duplicateIds.length > 0) {
      console.error(`[ERROR] DUPLICATE CARD IDs DETECTED: [${duplicateIds.join(', ')}]`);
      console.error(`[ERROR] This explains why counts are wrong!`);
    } else {
      console.log(`[DEBUG] ✅ No duplicate card IDs found`);
    }

    // Count audio statistics
    let withAudioCount = 0;
    let withoutAudioCount = 0;
    let processedCards = 0;

    allCards.forEach((card, index) => {
      const cardId = card.getAttribute("data-card-id");
      const viewMode = card.querySelector(".card-view-mode");

      if (!viewMode) {
        console.warn(`[WARN] Card ${index + 1} (ID: ${cardId}) has no view mode - skipping`);
        return;
      }

      const hasAudioAttr = viewMode.getAttribute("data-has-audio");
      const hasAudio = hasAudioAttr === "true";

      console.log(`[DEBUG] Processing Card ${index + 1} (ID: ${cardId}):`);
      console.log(`  - data-has-audio attribute: "${hasAudioAttr}"`);
      console.log(`  - Parsed hasAudio: ${hasAudio}`);

      if (hasAudio) {
        withAudioCount++;
        console.log(`  - ✅ Counted as WITH audio (total with audio: ${withAudioCount})`);
      } else {
        withoutAudioCount++;
        console.log(`  - ❌ Counted as WITHOUT audio (total without audio: ${withoutAudioCount})`);
      }

      processedCards++;
    });

    console.log(`[DEBUG] Processing Summary:`);
    console.log(`  - Total elements found: ${allCards.length}`);
    console.log(`  - Cards processed: ${processedCards}`);
    console.log(`  - Cards with audio: ${withAudioCount}`);
    console.log(`  - Cards without audio: ${withoutAudioCount}`);
    console.log(`  - Sum: ${withAudioCount + withoutAudioCount}`);

    // Update stats display
    const withAudioElement = document.getElementById("cards-with-audio-count");
    const withoutAudioElement = document.getElementById("cards-without-audio-count");

    if (withAudioElement) {
      withAudioElement.textContent = withAudioCount;
      console.log(`[DEBUG] Updated display: cards-with-audio-count = ${withAudioCount}`);
    }
    if (withoutAudioElement) {
      withoutAudioElement.textContent = withoutAudioCount;
      console.log(`[DEBUG] Updated display: cards-without-audio-count = ${withoutAudioCount}`);
    }

    // Final validation
    const totalCalculated = withAudioCount + withoutAudioCount;
    const uniqueCardCount = cardIds.length;

    console.log(`[DEBUG] Final Validation:`);
    console.log(`  - DOM elements found: ${allCards.length}`);
    console.log(`  - Unique card IDs: ${uniqueCardCount}`);
    console.log(`  - Total calculated: ${totalCalculated}`);

    if (totalCalculated !== uniqueCardCount) {
      console.error(`[ERROR] MISMATCH: Calculated total (${totalCalculated}) != Unique cards (${uniqueCardCount})`);
      console.error(`[ERROR] This suggests duplicate DOM elements or counting logic error`);
    } else if (allCards.length !== uniqueCardCount) {
      console.error(`[ERROR] DUPLICATE ELEMENTS: Found ${allCards.length} DOM elements but only ${uniqueCardCount} unique card IDs`);
    } else {
      console.log(`[DEBUG] ✅ All counts match correctly!`);
    }

    console.log(`[DEBUG] ========== AUDIO STATS DEBUG END ==========`);
  }

  function setupAudioFilter() {
    const filterSelect = document.getElementById("audio-filter");
    if (!filterSelect) return;

    filterSelect.addEventListener("change", function () {
      const filterValue = this.value;
      const allElements = document.querySelectorAll("[data-card-id]");

      // Filter to only get card containers (not favorite buttons)
      const allCards = Array.from(allElements).filter(element => {
        const hasViewMode = element.querySelector(".card-view-mode");
        const isCardContainer = element.classList.contains("flex-shrink-0");
        return hasViewMode && isCardContainer;
      });

      console.log(`[DEBUG] Audio filter changed to: ${filterValue}, found ${allCards.length} card containers`);

      allCards.forEach((card, index) => {
        // Use the data-has-audio attribute for consistent detection
        const viewMode = card.querySelector(".card-view-mode");
        const hasAudio = viewMode && viewMode.getAttribute("data-has-audio") === "true";
        let shouldShow = true;

        switch (filterValue) {
          case "with-audio":
            shouldShow = hasAudio;
            break;
          case "without-audio":
            shouldShow = !hasAudio;
            break;
          case "all":
          default:
            shouldShow = true;
            break;
        }

        console.log(`[DEBUG] Card ${index + 1}: hasAudio=${hasAudio}, shouldShow=${shouldShow} (filter: ${filterValue})`);

        if (shouldShow) {
          card.style.display = "";
        } else {
          card.style.display = "none";
        }
      });

      // Update carousel after filtering
      updateCarouselAfterFilter();
    });
  }

  function updateCarouselAfterFilter() {
    // Reset to first visible slide
    const visibleCards = document.querySelectorAll(
      '[data-card-id]:not([style*="display: none"])'
    );
    if (visibleCards.length > 0) {
      // Update slides array and current index
      slides.length = 0;
      visibleCards.forEach((card) => slides.push(card));
      currentSlideIndex = 0;
      showSlide(0);
    }
  }

  function setupAudioUrlFieldHandlers() {
    // Simplified audio URL field handling - no special styling needed
    // The audio button visibility will be updated when the card is saved
  }

  // Update audio button visibility after successful card save
  function updateAudioStatusAfterSave(cardContainer, cardData) {
    const viewMode = cardContainer.querySelector(".card-view-mode");
    const hasAudio = cardData.audio_url && cardData.audio_url.trim().length > 0;

    // Update data attribute
    viewMode.setAttribute("data-has-audio", hasAudio ? "true" : "false");

    // Update audio button visibility in phonetic section
    updateAudioButtonVisibility(viewMode, cardData);

    // Update stats
    updateAudioStats();
  }

  function updateAudioButtonVisibility(viewMode, cardData) {
    const hasAudio = cardData.audio_url && cardData.audio_url.trim().length > 0;
    const phoneticContainer = viewMode.querySelector(
      ".text-lg.text-gray-400.font-serif.italic.mb-4"
    );

    if (hasAudio) {
      // If we have audio, ensure the audio button exists
      if (cardData.phonetic) {
        // Update existing phonetic container with audio button
        if (phoneticContainer) {
          const existingAudioBtn = phoneticContainer.querySelector(
            ".audio-icon-tailwind"
          );
          if (!existingAudioBtn) {
            // Add audio button to existing phonetic container
            const audioBtn = document.createElement("button");
            audioBtn.className =
              "audio-icon-tailwind text-gray-500 hover:text-primary-color transition-colors duration-200";
            audioBtn.setAttribute("data-audio-url", cardData.audio_url);
            audioBtn.title = window.manual_texts?.listen || "Listen";
            audioBtn.innerHTML = '<i class="fas fa-volume-up text-xl"></i>';
            phoneticContainer.appendChild(audioBtn);
          } else {
            // Update existing audio button
            existingAudioBtn.setAttribute("data-audio-url", cardData.audio_url);
          }
        }
      } else {
        // No phonetic but has audio - create audio-only container
        if (phoneticContainer) {
          phoneticContainer.remove();
        }
        const audioContainer = document.createElement("div");
        audioContainer.className =
          "text-lg text-gray-400 font-serif italic mb-4 flex items-center space-x-2";
        audioContainer.innerHTML = `
                    <span class="text-gray-500 text-sm">${
                      window.manual_texts?.listen || "Listen"
                    }:</span>
                    <button class="audio-icon-tailwind text-gray-500 hover:text-primary-color transition-colors duration-200" data-audio-url="${
                      cardData.audio_url
                    }" title="${window.manual_texts?.listen || "Listen"}">
                        <i class="fas fa-volume-up text-xl"></i>
                    </button>
                `;

        // Insert after the word title
        const wordTitle = viewMode.querySelector(".text-3xl.font-bold.mb-2");
        const partOfSpeech = viewMode.querySelector(
          ".text-lg.text-gray-400.mb-2.italic"
        );
        const insertAfter = partOfSpeech || wordTitle;
        insertAfter.parentNode.insertBefore(
          audioContainer,
          insertAfter.nextSibling
        );
      }
    } else {
      // No audio - remove audio button
      const existingAudioBtn = viewMode.querySelector(".audio-icon-tailwind");
      if (existingAudioBtn) {
        existingAudioBtn.remove();
      }

      // If phonetic container only has audio button, remove the whole container
      if (phoneticContainer && !cardData.phonetic) {
        phoneticContainer.remove();
      }
    }
  }

  // Deck name editing functionality
  function initializeDeckNameEditing() {
    const editBtn = document.getElementById("edit-deck-name-btn");
    const saveBtn = document.getElementById("save-deck-name-btn");
    const cancelBtn = document.getElementById("cancel-deck-edit-btn");
    const deckNameView = document.getElementById("deck-name-view");
    const deckNameEdit = document.getElementById("deck-name-edit");
    const deckNameInput = document.getElementById("deck-name-input");

    if (
      !editBtn ||
      !saveBtn ||
      !cancelBtn ||
      !deckNameView ||
      !deckNameEdit ||
      !deckNameInput
    ) {
      return; // Elements not found
    }

    let originalName = deckNameInput.value;

    // Enter edit mode
    editBtn.addEventListener("click", function () {
      originalName = deckNameInput.value;
      deckNameView.classList.add("hidden");
      deckNameEdit.classList.remove("hidden");
      deckNameInput.focus();
      deckNameInput.select();
    });

    // Cancel edit
    cancelBtn.addEventListener("click", function () {
      deckNameInput.value = originalName;
      exitDeckNameEditMode();
    });

    // Save deck name
    saveBtn.addEventListener("click", function () {
      saveDeckName();
    });

    // Handle Enter key to save
    deckNameInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        saveDeckName();
      } else if (event.key === "Escape") {
        event.preventDefault();
        deckNameInput.value = originalName;
        exitDeckNameEditMode();
      }
    });

    function exitDeckNameEditMode() {
      deckNameView.classList.remove("hidden");
      deckNameEdit.classList.add("hidden");
    }

    function saveDeckName() {
      const newName = deckNameInput.value.trim();

      if (!newName) {
        showMessage(
          window.manual_texts?.deck_name_required || "Deck name is required",
          "error"
        );
        deckNameInput.focus();
        return;
      }

      if (newName === originalName) {
        exitDeckNameEditMode();
        return;
      }

      // Show loading state
      saveBtn.textContent = window.manual_texts?.saving || "Saving...";
      saveBtn.disabled = true;
      cancelBtn.disabled = true;

      // Get deck ID from URL
      const pathParts = window.location.pathname.split("/");
      const deckId = pathParts[pathParts.length - 2]; // Assuming URL is /decks/{id}/

      // Send update request (API endpoints don't use language prefixes)
      fetch(`/api/update-deck-name/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
            .content,
        },
        body: JSON.stringify({
          deck_id: deckId,
          name: newName,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            // Update the display
            const deckNameTitle = deckNameView.querySelector("h1");
            deckNameTitle.textContent = data.deck.name;
            originalName = data.deck.name;
            deckNameInput.value = data.deck.name;

            exitDeckNameEditMode();
            showMessage(
              window.manual_texts?.deck_name_updated ||
                "Deck name updated successfully!",
              "success"
            );
          } else {
            showMessage(
              data.error ||
                window.manual_texts?.error_updating_deck ||
                "Error updating deck name",
              "error"
            );
          }
        })
        .catch((error) => {
          console.error("Error updating deck name:", error);
          showMessage(
            window.manual_texts?.error_updating_deck ||
              "Error updating deck name",
            "error"
          );
        })
        .finally(() => {
          saveBtn.textContent =
            window.manual_texts?.save_deck_name || "Save Name";
          saveBtn.disabled = false;
          cancelBtn.disabled = false;
        });
    }
  }

  // Audio fetching functionality
  function initializeAudioFetching() {
    const fetchBtn = document.getElementById("fetch-missing-audio-btn");
    if (!fetchBtn) return;

    fetchBtn.addEventListener("click", function () {
      fetchMissingAudioForDeck();
    });
  }

  function fetchMissingAudioForDeck() {
    const fetchBtn = document.getElementById("fetch-missing-audio-btn");
    const pathParts = window.location.pathname.split("/");
    const deckId = pathParts[pathParts.length - 2]; // Get deck ID from URL
    const languagePrefix = pathParts[1]; // Get language code (en/vi)

    // Show loading state
    fetchBtn.disabled = true;
    fetchBtn.classList.add("loading");
    const originalText = fetchBtn.innerHTML;
    fetchBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${
      window.manual_texts?.fetching_audio || "Fetching audio..."
    }`;

    // Create progress indicator
    const progressDiv = createProgressIndicator();
    document.body.appendChild(progressDiv);

    // Make API request
    fetch(`/api/fetch-missing-audio/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
          .content,
      },
      body: JSON.stringify({
        deck_id: deckId,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          updateProgressIndicator(progressDiv, data);

          if (data.updated_count > 0) {
            // Refresh the page to show updated audio buttons
            setTimeout(() => {
              window.location.reload();
            }, 2000);

            showMessage(
              `${
                window.manual_texts?.audio_fetched_successfully ||
                "Audio fetched successfully!"
              } ${data.updated_count} ${
                window.manual_texts?.cards_updated || "cards updated"
              }`,
              "success"
            );
          } else {
            showMessage(
              window.manual_texts?.no_audio_found ||
                "No audio found for some words",
              "info"
            );
          }
        } else {
          showMessage(
            data.error ||
              window.manual_texts?.audio_fetch_error ||
              "Error fetching audio",
            "error"
          );
        }
      })
      .catch((error) => {
        console.error("Error fetching audio:", error);
        showMessage(
          window.manual_texts?.audio_fetch_error || "Error fetching audio",
          "error"
        );
      })
      .finally(() => {
        // Restore button state
        fetchBtn.disabled = false;
        fetchBtn.classList.remove("loading");
        fetchBtn.innerHTML = originalText;

        // Remove progress indicator after delay
        setTimeout(() => {
          if (progressDiv.parentNode) {
            progressDiv.parentNode.removeChild(progressDiv);
          }
        }, 3000);
      });
  }

  function createProgressIndicator() {
    const progressDiv = document.createElement("div");
    progressDiv.className = "audio-fetch-progress";
    progressDiv.innerHTML = `
            <button class="close-btn" onclick="this.parentNode.remove()">
                <i class="fas fa-times"></i>
            </button>
            <div class="progress-header">
                <i class="fas fa-download"></i>
                <span>${
                  window.manual_texts?.fetching_audio || "Fetching audio..."
                }</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
            <div class="progress-text">
                <span class="current-word">Starting...</span>
            </div>
        `;
    return progressDiv;
  }

  function updateProgressIndicator(progressDiv, data) {
    const progressFill = progressDiv.querySelector(".progress-fill");
    const progressText = progressDiv.querySelector(".progress-text");
    const header = progressDiv.querySelector(".progress-header span");

    if (data.total_processed > 0) {
      const percentage = (data.updated_count / data.total_processed) * 100;
      progressFill.style.width = `${percentage}%`;
    }

    header.textContent =
      window.manual_texts?.audio_fetch_complete || "Audio fetch complete";
    progressText.innerHTML = `
            <div>${window.manual_texts?.found_label || "Found:"} ${
      data.updated_count
    } / ${data.total_processed}</div>
            <div class="text-xs mt-1">
                ${data.words_processed
                  .filter((w) => w.found)
                  .map((w) => w.word)
                  .join(", ")}
            </div>
        `;
  }

  function fetchAudioForSingleCard(cardId) {
    return fetch(`/api/fetch-audio-for-card/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
          .content,
      },
      body: JSON.stringify({
        card_id: cardId,
      }),
    }).then((response) => response.json());
  }

  // Initialize dictionary links with fallback mechanism
  function initializeDictionaryLinks() {
    console.log("Initializing dictionary links with fallback mechanism...");

    // Check if DictionaryUtils is available
    if (typeof window.DictionaryUtils === "undefined") {
      console.warn(
        "DictionaryUtils not available, dictionary links will use default behavior"
      );
      return;
    }

    // Find all dictionary word links and enhance them
    const dictionaryLinks = document.querySelectorAll(".dictionary-word-link");

    dictionaryLinks.forEach((link) => {
      const word = link.getAttribute("data-word") || link.textContent.trim();

      if (word) {
        DictionaryUtils.enhanceExistingLink(link, word, {
          onFallback: (word, fallbackUrl) => {
            console.log(
              `Deck Detail: Using fallback dictionary URL for ${word}: ${fallbackUrl}`
            );
          },
          onError: (error) => {
            console.error(
              `Deck Detail: Dictionary fallback failed for ${word}:`,
              error
            );
          },
        });

        console.log(`Enhanced dictionary link for word: ${word}`);
      }
    });

    console.log(`Enhanced ${dictionaryLinks.length} dictionary links`);
  }

  // Initialize favorites functionality
  function initializeFavorites() {
    console.log("🔍 Initializing favorites functionality...");

    // Load favorite status for all cards
    loadFavoriteStatus();

    // Add event listeners to favorite buttons
    const favoriteButtons = document.querySelectorAll('.favorite-btn');
    favoriteButtons.forEach(button => {
      button.addEventListener('click', handleFavoriteToggle);
    });

    console.log(`✅ Added favorite listeners to ${favoriteButtons.length} buttons`);
  }

  // Load favorite status for all visible cards
  function loadFavoriteStatus() {
    const favoriteButtons = document.querySelectorAll('.favorite-btn');
    const cardIds = Array.from(favoriteButtons).map(btn => btn.getAttribute('data-card-id'));

    if (cardIds.length === 0) {
      console.log("No favorite buttons found");
      return;
    }

    const params = new URLSearchParams();
    cardIds.forEach(id => params.append('card_ids[]', id));

    fetch(`/api/favorites/check/?${params.toString()}`, {
      method: 'GET',
      headers: {
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Update favorite button states
        Object.entries(data.favorites).forEach(([cardId, isFavorited]) => {
          const button = document.querySelector(`[data-card-id="${cardId}"]`);
          if (button) {
            updateFavoriteButton(button, isFavorited);
          }
        });
        console.log("✅ Favorite status loaded for all cards");
      } else {
        console.error("Failed to load favorite status:", data.error);
      }
    })
    .catch(error => {
      console.error("Error loading favorite status:", error);
    });
  }

  // Handle favorite button click
  function handleFavoriteToggle(event) {
    event.preventDefault();
    event.stopPropagation();

    const button = event.currentTarget;
    const cardId = button.getAttribute('data-card-id');

    if (!cardId) {
      console.error("No card ID found for favorite button");
      return;
    }

    // Show loading state
    const originalIcon = button.querySelector('.favorite-icon').textContent;
    button.querySelector('.favorite-icon').textContent = '⏳';
    button.disabled = true;

    fetch('/api/favorites/toggle/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
      },
      body: JSON.stringify({
        card_id: cardId
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        updateFavoriteButton(button, data.is_favorited);
        console.log(`✅ Favorite toggled for card ${cardId}: ${data.is_favorited ? 'added' : 'removed'}`);

        // Show feedback message
        showFavoriteMessage(data.is_favorited);
      } else {
        console.error("Failed to toggle favorite:", data.error);
        // Restore original state
        button.querySelector('.favorite-icon').textContent = originalIcon;
        alert('Error toggling favorite: ' + data.error);
      }
    })
    .catch(error => {
      console.error("Error toggling favorite:", error);
      // Restore original state
      button.querySelector('.favorite-icon').textContent = originalIcon;
      alert('Error toggling favorite');
    })
    .finally(() => {
      button.disabled = false;
    });
  }

  // Update favorite button appearance
  function updateFavoriteButton(button, isFavorited) {
    const icon = button.querySelector('.favorite-icon');
    if (isFavorited) {
      icon.textContent = '❤️';
      button.classList.add('favorited');
      button.title = 'Remove from favorites';
    } else {
      icon.textContent = '🤍';
      button.classList.remove('favorited');
      button.title = 'Add to favorites';
    }
  }

  // Show favorite feedback message
  function showFavoriteMessage(isFavorited) {
    const message = isFavorited ?
      '❤️ Added to favorites!' :
      '💔 Removed from favorites';

    // Create temporary message element
    const messageEl = document.createElement('div');
    messageEl.textContent = message;
    messageEl.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${isFavorited ? '#10b981' : '#ef4444'};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      font-weight: 600;
      z-index: 1000;
      animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(messageEl);

    // Remove after 3 seconds
    setTimeout(() => {
      messageEl.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => {
        if (messageEl.parentNode) {
          messageEl.parentNode.removeChild(messageEl);
        }
      }, 300);
    }, 3000);
  }

  // Initialize favorites when page loads
  initializeFavorites();

  // Initialize blacklist functionality
  function initializeBlacklist() {
    console.log("🔍 Initializing blacklist functionality...");

    // Load blacklist status for all cards
    loadBlacklistStatus();

    // Add event listeners to blacklist buttons
    const blacklistButtons = document.querySelectorAll('.blacklist-btn');
    blacklistButtons.forEach(button => {
      button.addEventListener('click', handleBlacklistToggle);
    });

    console.log(`✅ Added blacklist listeners to ${blacklistButtons.length} buttons`);
  }

  // Load blacklist status for all visible cards
  function loadBlacklistStatus() {
    const blacklistButtons = document.querySelectorAll('.blacklist-btn');
    const cardIds = Array.from(blacklistButtons).map(btn => btn.getAttribute('data-card-id'));

    if (cardIds.length === 0) {
      console.log("No blacklist buttons found");
      return;
    }

    const params = new URLSearchParams();
    cardIds.forEach(id => params.append('card_ids[]', id));

    fetch(`/api/blacklist/check/?${params.toString()}`, {
      method: 'GET',
      headers: {
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Update blacklist button states
        Object.entries(data.blacklists).forEach(([cardId, isBlacklisted]) => {
          const button = document.querySelector(`.blacklist-btn[data-card-id="${cardId}"]`);
          if (button) {
            updateBlacklistButton(button, isBlacklisted);
          }
        });
        console.log("✅ Blacklist status loaded for all cards");
      } else {
        console.error("Failed to load blacklist status:", data.error);
      }
    })
    .catch(error => {
      console.error("Error loading blacklist status:", error);
    });
  }

  // Handle blacklist button click
  function handleBlacklistToggle(event) {
    event.preventDefault();
    event.stopPropagation();

    const button = event.currentTarget;
    const cardId = button.getAttribute('data-card-id');

    if (!cardId) {
      console.error("No card ID found for blacklist button");
      return;
    }

    // Show loading state
    const originalIcon = button.querySelector('.blacklist-icon').textContent;
    button.querySelector('.blacklist-icon').textContent = '⏳';
    button.disabled = true;

    fetch('/api/blacklist/toggle/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
      },
      body: JSON.stringify({
        card_id: cardId
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        updateBlacklistButton(button, data.is_blacklisted);
        console.log(`✅ Blacklist toggled for card ${cardId}: ${data.is_blacklisted ? 'added' : 'removed'}`);

        // Show feedback message
        showBlacklistMessage(data.is_blacklisted);
      } else {
        console.error("Failed to toggle blacklist:", data.error);
        // Restore original state
        button.querySelector('.blacklist-icon').textContent = originalIcon;
        alert('Error toggling blacklist: ' + data.error);
      }
    })
    .catch(error => {
      console.error("Error toggling blacklist:", error);
      // Restore original state
      button.querySelector('.blacklist-icon').textContent = originalIcon;
      alert('Error toggling blacklist');
    })
    .finally(() => {
      button.disabled = false;
    });
  }

  // Update blacklist button appearance
  function updateBlacklistButton(button, isBlacklisted) {
    const icon = button.querySelector('.blacklist-icon');
    if (isBlacklisted) {
      icon.textContent = '🚫';
      button.classList.add('blacklisted');
      button.title = 'Remove from blacklist';
    } else {
      icon.textContent = '🔘';
      button.classList.remove('blacklisted');
      button.title = 'Add to blacklist';
    }
  }

  // Show blacklist feedback message
  function showBlacklistMessage(isBlacklisted) {
    const message = isBlacklisted ?
      '⛔ Added to blacklist!' :
      '✅ Removed from blacklist';

    // Create temporary message element
    const messageEl = document.createElement('div');
    messageEl.textContent = message;
    messageEl.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${isBlacklisted ? '#ef4444' : '#10b981'};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      font-weight: 600;
      z-index: 1000;
      animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(messageEl);

    // Remove after 3 seconds
    setTimeout(() => {
      messageEl.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => {
        if (messageEl.parentNode) {
          messageEl.parentNode.removeChild(messageEl);
        }
      }, 300);
    }, 3000);
  }

  // Initialize blacklist when page loads
  initializeBlacklist();

  // Initialize delete card functionality
  initializeDeleteCard();

  // Initialize card hover functionality
  initializeCardHoverEffects();

  /**
   * Update card display after audio selection
   * Called by Enhanced Audio Manager after successful audio update
   */
  function updateCardDisplayForAudio(cardId, updatedData) {
    console.log(`updateCardDisplayForAudio called with cardId: ${cardId}, updatedData:`, updatedData);

    // Validate input parameters
    if (!cardId) {
      console.error('updateCardDisplayForAudio: cardId is null or undefined');
      return;
    }

    if (!updatedData) {
      console.error('updateCardDisplayForAudio: updatedData is null or undefined');
      return;
    }

    const cardContainer = document.querySelector(`[data-card-id="${cardId}"]`);
    if (!cardContainer) {
      console.error(`Card container not found for cardId: ${cardId}`);
      // Try to find the card container with a more flexible selector
      const allCards = document.querySelectorAll('[data-card-id]');
      console.log('Available card IDs:', Array.from(allCards).map(card => card.dataset.cardId));
      return;
    }

    const viewMode = cardContainer.querySelector('.card-view-mode');
    if (!viewMode) {
      console.error(`View mode not found for cardId: ${cardId}`);
      return;
    }

    // Update audio URL if provided
    if (updatedData.audio_url) {
      console.log(`Updating audio URL to: ${updatedData.audio_url}`);

      // Update data attribute
      viewMode.setAttribute('data-has-audio', 'true');

      // Find existing audio container - try multiple selectors
      let audioContainer = viewMode.querySelector('.text-lg.text-gray-400.font-serif.italic.mb-4.flex.items-center.space-x-2');

      // If not found, look for phonetic container that might exist
      if (!audioContainer) {
        audioContainer = viewMode.querySelector('.text-lg.text-gray-400.font-serif.italic.mb-4');
      }

      // Also try to find any container that has audio buttons
      if (!audioContainer) {
        const existingAudioBtn = viewMode.querySelector('.audio-icon-tailwind');
        if (existingAudioBtn) {
          audioContainer = existingAudioBtn.closest('div');
        }
      }

      if (!audioContainer) {
        console.log('Creating new audio container');
        // Create new audio container if it doesn't exist
        audioContainer = document.createElement('div');
        audioContainer.className = 'text-lg text-gray-400 font-serif italic mb-4 flex items-center space-x-2';

        // Insert after the word title or part of speech
        const wordTitle = viewMode.querySelector('.text-3xl.font-bold.mb-2');
        const partOfSpeech = viewMode.querySelector('.text-lg.text-gray-400.mb-2.italic');

        if (partOfSpeech) {
          partOfSpeech.insertAdjacentElement('afterend', audioContainer);
        } else if (wordTitle) {
          wordTitle.insertAdjacentElement('afterend', audioContainer);
        } else {
          console.error('Could not find insertion point for audio container');
          return;
        }
      } else {
        console.log('Found existing audio container, updating it');
        // Ensure the container has the correct classes for flex layout
        audioContainer.className = 'text-lg text-gray-400 font-serif italic mb-4 flex items-center space-x-2';
      }

      // Preserve existing phonetic text if it exists
      const existingPhoneticSpan = audioContainer.querySelector('span:first-child');
      let phoneticText = '';

      if (existingPhoneticSpan && !existingPhoneticSpan.classList.contains('text-gray-500')) {
        phoneticText = existingPhoneticSpan.textContent;
      }

      // Get word for enhanced audio button
      const wordElement = cardContainer.querySelector('.dictionary-word-link');
      const word = wordElement ? wordElement.textContent : '';

      // Update audio container content (no enhanced audio button here since it's in the top button group)
      const newContent = `
        ${phoneticText ? `<span>${phoneticText}</span>` : `<span class="text-gray-500 text-sm">${window.manual_texts?.listen || 'Listen'}:</span>`}
        <button
          class="audio-icon-tailwind text-gray-500 hover:text-primary-color transition-colors duration-200"
          data-audio-url="${updatedData.audio_url}"
          title="${window.manual_texts?.listen || 'Listen'}"
        >
          <i class="fas fa-volume-up text-xl"></i>
        </button>
      `;

      audioContainer.innerHTML = newContent;

      console.log('Audio container updated successfully');
      console.log('New audio URL set:', updatedData.audio_url);
      console.log('Audio container HTML:', audioContainer.outerHTML.substring(0, 200) + '...');

      // Rebind audio button event handlers for the new audio button
      const newAudioBtn = audioContainer.querySelector('.audio-icon-tailwind');
      if (newAudioBtn && newAudioBtn.dataset.audioUrl) {
        console.log('Rebinding audio button event handler');
        // The audio button click handler should already be bound via event delegation
        // But we can verify it has the correct data
        console.log('New audio button data-audio-url:', newAudioBtn.dataset.audioUrl);
      }
    }

    // Update audio statistics
    if (typeof updateAudioStats === 'function') {
      updateAudioStats();
      console.log('Audio statistics updated');
    } else {
      console.warn('updateAudioStats function not available');
    }

    console.log(`Successfully updated card display for card ${cardId}`);
  }

  // Delete Card Functionality
  let cardToDelete = null;

  function initializeDeleteCard() {
    console.log("🗑️ Initializing delete card functionality...");

    // Add event listeners to delete buttons
    const deleteButtons = document.querySelectorAll('.delete-card-btn');
    deleteButtons.forEach(button => {
      button.addEventListener('click', handleDeleteCardClick);
    });

    console.log(`✅ Added delete listeners to ${deleteButtons.length} buttons`);
  }

  function handleDeleteCardClick(event) {
    event.preventDefault();
    event.stopPropagation();

    const button = event.currentTarget;
    const cardId = button.getAttribute('data-card-id');

    if (!cardId) {
      console.error("No card ID found for delete button");
      return;
    }

    // Find the card data
    const cardElement = button.closest('[data-card-id]');
    if (!cardElement) {
      console.error("Could not find card element");
      return;
    }

    // Extract card information for preview
    const wordElement = cardElement.querySelector('.word-text');
    const partOfSpeechElement = cardElement.querySelector('.part-of-speech');

    const word = wordElement ? wordElement.textContent.trim() : 'Unknown';
    const partOfSpeech = partOfSpeechElement ? partOfSpeechElement.textContent.trim() : '';

    // Store card to delete
    cardToDelete = {
      id: cardId,
      word: word,
      partOfSpeech: partOfSpeech,
      element: cardElement
    };

    // Show confirmation modal
    showDeleteCardModal(word, partOfSpeech);
  }

  function showDeleteCardModal(word, partOfSpeech) {
    const modal = document.getElementById('deleteCardModal');
    const wordElement = document.getElementById('deleteCardWord');
    const partOfSpeechElement = document.getElementById('deleteCardPartOfSpeech');

    if (wordElement) {
      wordElement.textContent = word;
    }

    if (partOfSpeechElement) {
      partOfSpeechElement.textContent = partOfSpeech ? `(${partOfSpeech})` : '';
    }

    if (modal) {
      modal.style.display = 'block';
      document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }
  }

  function hideDeleteCardModal() {
    const modal = document.getElementById('deleteCardModal');
    if (modal) {
      modal.style.display = 'none';
      document.body.style.overflow = ''; // Restore scrolling
    }
    cardToDelete = null;
  }

  async function confirmDeleteCard() {
    if (!cardToDelete) {
      console.error("No card to delete");
      return;
    }

    const deleteBtn = document.querySelector('.btn-delete');
    const originalText = deleteBtn.innerHTML;

    try {
      // Show loading state
      deleteBtn.disabled = true;
      deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

      // Get CSRF token
      const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

      const response = await fetch('/api/delete-flashcard/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          id: cardToDelete.id
        })
      });

      const data = await response.json();

      if (data.success) {
        console.log(`✅ Card ${cardToDelete.id} deleted successfully`);

        // Hide modal
        hideDeleteCardModal();

        // Remove card from UI with animation
        if (cardToDelete.element) {
          cardToDelete.element.style.transition = 'all 0.3s ease';
          cardToDelete.element.style.transform = 'scale(0.8)';
          cardToDelete.element.style.opacity = '0';

          setTimeout(() => {
            cardToDelete.element.remove();

            // Check if this was the last card
            const remainingCards = document.querySelectorAll('[data-card-id]');
            if (remainingCards.length === 0) {
              // Reload page to show empty state
              window.location.reload();
            } else {
              // Update pagination if needed
              updatePaginationAfterDelete();
            }
          }, 300);
        }

        // Show success message
        showDeleteMessage(true, `Card "${cardToDelete.word}" deleted successfully`);

      } else {
        console.error("Failed to delete card:", data.error);
        showDeleteMessage(false, data.error || 'Failed to delete card');
      }
    } catch (error) {
      console.error("Error deleting card:", error);
      showDeleteMessage(false, 'Network error occurred');
    } finally {
      // Restore button state
      deleteBtn.disabled = false;
      deleteBtn.innerHTML = originalText;
    }
  }

  function updatePaginationAfterDelete() {
    // Update carousel navigation if needed
    const slides = document.querySelectorAll('#carousel-slides > div');
    const totalSlides = slides.length;

    if (totalSlides > 0) {
      // Reset to first slide if current slide was deleted
      const carousel = document.getElementById('carousel-slides');
      if (carousel) {
        carousel.scrollTo({ left: 0, behavior: 'smooth' });
      }

      // Update pagination dots
      updatePaginationDots(totalSlides);
    }
  }

  function updatePaginationDots(totalSlides) {
    const paginationContainer = document.getElementById('pagination-dots');
    if (paginationContainer && totalSlides > 1) {
      paginationContainer.innerHTML = '';

      for (let i = 0; i < totalSlides; i++) {
        const dot = document.createElement('span');
        dot.className = `pagination-dot ${i === 0 ? 'active' : ''}`;
        dot.onclick = () => scrollToSlide(i);
        paginationContainer.appendChild(dot);
      }
    }
  }

  function showDeleteMessage(success, message) {
    const messageEl = document.createElement('div');
    messageEl.textContent = message;
    messageEl.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${success ? '#10b981' : '#ef4444'};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      font-weight: 600;
      z-index: 10001;
      animation: slideIn 0.3s ease;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;

    document.body.appendChild(messageEl);

    // Remove after 3 seconds
    setTimeout(() => {
      messageEl.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => {
        if (messageEl.parentNode) {
          messageEl.parentNode.removeChild(messageEl);
        }
      }, 300);
    }, 3000);
  }

  // Card Hover Effects for Auto-hide Buttons
  function initializeCardHoverEffects() {
    console.log("👆 Initializing card hover effects...");

    const cardElements = document.querySelectorAll('.card-view-mode');

    cardElements.forEach(card => {
      const actionButtons = card.querySelector('.card-action-buttons');

      if (!actionButtons) return;

      // Enhanced hover functionality
      card.addEventListener('mouseenter', () => {
        actionButtons.style.opacity = '1';
      });

      card.addEventListener('mouseleave', () => {
        // Only hide if not on mobile
        if (window.innerWidth > 480) {
          actionButtons.style.opacity = '0';
        }
      });

      // Ensure buttons stay visible when hovering over them
      actionButtons.addEventListener('mouseenter', () => {
        actionButtons.style.opacity = '1';
      });
    });

    // Handle window resize to adjust mobile behavior
    window.addEventListener('resize', () => {
      if (window.innerWidth <= 480) {
        // Show all buttons on mobile
        document.querySelectorAll('.card-action-buttons').forEach(buttons => {
          buttons.style.opacity = '1';
        });
      }
    });

    console.log(`✅ Card hover effects initialized for ${cardElements.length} cards`);
  }

  // Fix tooltip issues by removing unwanted title attributes
  function fixTooltipIssues() {
    console.log(`[AUDIO DEBUG] ========== FIXING TOOLTIP ISSUES ==========`);

    // Remove title attributes from elements that shouldn't have tooltips
    const cardElements = document.querySelectorAll('.card-view-mode');

    cardElements.forEach((card, cardIndex) => {
      // Remove title from the card itself if it exists
      if (card.hasAttribute('title')) {
        const removedTitle = card.getAttribute('title');
        card.removeAttribute('title');
        console.log(`[AUDIO DEBUG] Removed card title: "${removedTitle}" from card ${cardIndex + 1}`);
      }

      // Remove cursor pointer from card
      card.style.cursor = 'default';

      // Ensure only action buttons and audio icons have tooltips
      const nonButtonElements = card.querySelectorAll('*:not(.card-action-btn):not(.audio-icon-tailwind)[title]');
      nonButtonElements.forEach(element => {
        const titleValue = element.getAttribute('title');
        if (titleValue) {
          // Remove any title that mentions "favorite" or similar
          if (titleValue.toLowerCase().includes('favorite') ||
              titleValue.toLowerCase().includes('add to') ||
              titleValue.toLowerCase().includes('toggle')) {
            element.removeAttribute('title');
            console.log(`[AUDIO DEBUG] Removed unwanted title: "${titleValue}"`);
          }
        }
      });

      // Ensure audio icons are properly configured
      const audioIcons = card.querySelectorAll('.audio-icon-tailwind');
      audioIcons.forEach((icon, iconIndex) => {
        icon.style.cursor = 'pointer';
        icon.style.pointerEvents = 'auto';
        icon.style.zIndex = '15';
        console.log(`[AUDIO DEBUG] Configured audio icon ${iconIndex + 1} in card ${cardIndex + 1}`);
      });
    });

    console.log(`[AUDIO DEBUG] Tooltip issues fixed for ${cardElements.length} cards`);
  }

  // Initialize tooltip fixes
  fixTooltipIssues();

  // Add definition pair functionality
  document.getElementById('add-definition-btn').addEventListener('click', function() {
    const container = document.getElementById('modal-definitions-container');
    addDefinitionPair(container);
  });

  // Update definition pair numbers
  function updateDefinitionNumbers(container) {
    const pairs = container.querySelectorAll('.modal-definition-pair');
    pairs.forEach((pair, index) => {
      const numberSpan = pair.querySelector('.definition-pair-number');
      if (numberSpan) {
        numberSpan.textContent = `#${index + 1}`;
      }
    });
  }

  // Global remove definition function
  window.removeDefinitionPair = function(button) {
    const pair = button.closest('.modal-definition-pair');
    const container = document.getElementById('modal-definitions-container');

    // Don't allow removing the last definition pair
    if (container.children.length > 1) {
      pair.remove();
      updateDefinitionNumbers(container);
    } else {
      showMessage('At least one definition is required', 'error');
    }
  };

  // ESC key to close edit modal
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      const editModal = document.getElementById('editCardModal');
      if (editModal.style.display === 'block') {
        hideEditCardModal();
        return;
      }
    }
  });

  // Make functions globally available for modal buttons
  window.showDeleteCardModal = showDeleteCardModal;
  window.hideDeleteCardModal = hideDeleteCardModal;
  window.confirmDeleteCard = confirmDeleteCard;
  window.hideEditCardModal = hideEditCardModal;
  window.saveEditCardModal = saveEditCardModal;

});
