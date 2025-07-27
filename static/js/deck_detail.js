// static/js/deck_detail.js

document.addEventListener("DOMContentLoaded", function () {
  const carouselContainer = document.querySelector("#carousel-container");
  if (!carouselContainer) {
    return;
  }

  const carouselSlides = carouselContainer.querySelector("#carousel-slides");
  const slides = Array.from(carouselSlides.children);
  const prevBtn = carouselContainer.querySelector("#prevBtn");
  const nextBtn = carouselContainer.querySelector("#nextBtn");
  const paginationDotsContainer = document.querySelector("#pagination-dots");

  let currentSlideIndex = 0;

  function showSlide(index) {
    // Ensure the index loops around
    if (index < 0) {
      currentSlideIndex = slides.length - 1;
    } else if (index >= slides.length) {
      currentSlideIndex = 0;
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

  // Event listener for audio icons and edit functionality
  carouselSlides.addEventListener("click", function (event) {
    const audioIcon = event.target.closest(".audio-icon-tailwind");
    if (audioIcon) {
      const audioUrl = audioIcon.dataset.audioUrl;
      if (audioUrl) {
        try {
          new Audio(audioUrl)
            .play()
            .catch((e) => console.error("Audio playback error:", e));
        } catch (e) {
          console.error("Error creating Audio object:", e);
        }
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

  // Edit functionality functions
  function enterEditMode(cardContainer) {
    const viewMode = cardContainer.querySelector(".card-view-mode");
    const editMode = cardContainer.querySelector(".card-edit-mode");

    if (viewMode && editMode) {
      viewMode.classList.add("hidden");
      editMode.classList.remove("hidden");

      // Store original data for cancel functionality
      storeOriginalData(cardContainer);

      // Enable edit mode state
      enableEditModeState();
    }
  }

  function exitEditMode(cardContainer) {
    const viewMode = cardContainer.querySelector(".card-view-mode");
    const editMode = cardContainer.querySelector(".card-edit-mode");

    if (viewMode && editMode) {
      viewMode.classList.remove("hidden");
      editMode.classList.add("hidden");

      // Disable edit mode state
      disableEditModeState();
    }
  }

  function storeOriginalData(cardContainer) {
    const editMode = cardContainer.querySelector(".card-edit-mode");
    const originalData = {
      word: editMode.querySelector(".edit-word").value,
      phonetic: editMode.querySelector(".edit-phonetic").value,
      partOfSpeech: editMode.querySelector(".edit-part-of-speech").value,
      audioUrl: editMode.querySelector(".edit-audio-url").value,
      definitions: [],
    };

    // Store definition data
    const englishDefs = editMode.querySelectorAll(".edit-english-def");
    const vietnameseDefs = editMode.querySelectorAll(".edit-vietnamese-def");

    for (let i = 0; i < englishDefs.length; i++) {
      originalData.definitions.push({
        english: englishDefs[i].value,
        vietnamese: vietnameseDefs[i] ? vietnameseDefs[i].value : "",
      });
    }

    cardContainer.dataset.originalData = JSON.stringify(originalData);
  }

  function restoreOriginalData(cardContainer) {
    const originalData = JSON.parse(cardContainer.dataset.originalData || "{}");
    const editMode = cardContainer.querySelector(".card-edit-mode");

    if (originalData && editMode) {
      editMode.querySelector(".edit-word").value = originalData.word || "";
      editMode.querySelector(".edit-phonetic").value =
        originalData.phonetic || "";
      editMode.querySelector(".edit-part-of-speech").value =
        originalData.partOfSpeech || "";
      editMode.querySelector(".edit-audio-url").value =
        originalData.audioUrl || "";

      // Restore definitions
      const englishDefs = editMode.querySelectorAll(".edit-english-def");
      const vietnameseDefs = editMode.querySelectorAll(".edit-vietnamese-def");

      originalData.definitions.forEach((def, index) => {
        if (englishDefs[index]) englishDefs[index].value = def.english;
        if (vietnameseDefs[index]) vietnameseDefs[index].value = def.vietnamese;
      });
    }
  }

  function cancelEdit(cardContainer) {
    const confirmCancel =
      window.manual_texts?.confirm_cancel_edit ||
      "Are you sure you want to cancel? Unsaved changes will be lost.";

    if (confirm(confirmCancel)) {
      restoreOriginalData(cardContainer);
      exitEditMode(cardContainer);
    }
  }

  function saveCardChanges(cardContainer) {
    const cardId = cardContainer.dataset.cardId;
    const editMode = cardContainer.querySelector(".card-edit-mode");

    // Collect form data
    const formData = {
      card_id: cardId,
      word: editMode.querySelector(".edit-word").value.trim(),
      phonetic: editMode.querySelector(".edit-phonetic").value.trim(),
      part_of_speech: editMode
        .querySelector(".edit-part-of-speech")
        .value.trim(),
      audio_url: editMode.querySelector(".edit-audio-url").value.trim(),
      definitions: [],
    };

    // Collect definitions
    const englishDefs = editMode.querySelectorAll(".edit-english-def");
    const vietnameseDefs = editMode.querySelectorAll(".edit-vietnamese-def");

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
    const saveBtn = editMode.querySelector(".save-card-btn");
    const originalText = saveBtn.textContent;
    saveBtn.textContent = window.manual_texts?.saving || "Saving...";
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
          updateCardDisplay(cardContainer, data.card);
          exitEditMode(cardContainer);
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
        saveBtn.textContent = originalText;
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

  // Audio status functionality
  function initializeAudioStatusFeatures() {
    updateAudioStats();
    setupAudioFilter();
    setupAudioUrlFieldHandlers();
  }

  function updateAudioStats() {
    const allCards = document.querySelectorAll("[data-card-id]");
    let withAudioCount = 0;
    let withoutAudioCount = 0;

    allCards.forEach((card) => {
      // Check if card has audio button (indicates audio is available)
      const hasAudioButton = card.querySelector(".audio-icon-tailwind");
      if (hasAudioButton) {
        withAudioCount++;
      } else {
        withoutAudioCount++;
      }
    });

    // Update stats display
    const withAudioElement = document.getElementById("cards-with-audio-count");
    const withoutAudioElement = document.getElementById(
      "cards-without-audio-count"
    );

    if (withAudioElement) withAudioElement.textContent = withAudioCount;
    if (withoutAudioElement)
      withoutAudioElement.textContent = withoutAudioCount;
  }

  function setupAudioFilter() {
    const filterSelect = document.getElementById("audio-filter");
    if (!filterSelect) return;

    filterSelect.addEventListener("change", function () {
      const filterValue = this.value;
      const allCards = document.querySelectorAll("[data-card-id]");

      allCards.forEach((card) => {
        // Check if card has audio button (indicates audio is available)
        const hasAudioButton = card.querySelector(".audio-icon-tailwind");
        let shouldShow = true;

        switch (filterValue) {
          case "with-audio":
            shouldShow = !!hasAudioButton;
            break;
          case "without-audio":
            shouldShow = !hasAudioButton;
            break;
          case "all":
          default:
            shouldShow = true;
            break;
        }

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
});
