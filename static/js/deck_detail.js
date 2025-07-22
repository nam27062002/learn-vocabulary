// static/js/deck_detail.js

document.addEventListener('DOMContentLoaded', function() {
    const carouselContainer = document.querySelector('#carousel-container');
    if (!carouselContainer) {
        return;
    }

    const carouselSlides = carouselContainer.querySelector('#carousel-slides');
    const slides = Array.from(carouselSlides.children);
    const prevBtn = carouselContainer.querySelector('#prevBtn');
    const nextBtn = carouselContainer.querySelector('#nextBtn');
    const paginationDotsContainer = document.querySelector('#pagination-dots');

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
            behavior: 'smooth'
        });

        // Apply shadow/peek effect dynamically via inline styles
        slides.forEach((slide, i) => {
            if (i === currentSlideIndex) {
                slide.style.opacity = '1';
                slide.style.transform = 'scale(1)';
                slide.style.zIndex = '2';
            } else {
                slide.style.opacity = '0.7';
                slide.style.transform = 'scale(0.9)';
                slide.style.zIndex = '1';
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
            paginationDotsContainer.innerHTML = '';
            slides.forEach((_, index) => {
                const dot = document.createElement('span');
                dot.classList.add('pagination-dot');
                if (index === currentSlideIndex) {
                    dot.classList.add('active');
                }
                dot.addEventListener('click', () => {
                    // Disable pagination during edit mode
                    if (document.body.getAttribute('data-edit-mode') === 'true') {
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
        prevBtn.addEventListener('click', () => {
            // Disable navigation during edit mode
            if (document.body.getAttribute('data-edit-mode') === 'true') {
                return;
            }
            prevSlide();
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            // Disable navigation during edit mode
            if (document.body.getAttribute('data-edit-mode') === 'true') {
                return;
            }
            nextSlide();
        });
    }

    // Event listener for audio icons and edit functionality
    carouselSlides.addEventListener('click', function(event) {
        const audioIcon = event.target.closest('.audio-icon-tailwind');
        if (audioIcon) {
            const audioUrl = audioIcon.dataset.audioUrl;
            if (audioUrl) {
                try {
                    new Audio(audioUrl).play().catch(e => console.error('Audio playback error:', e));
                } catch (e) {
                    console.error('Error creating Audio object:', e);
                }
            }
            return;
        }

        // Handle edit button clicks
        const editBtn = event.target.closest('.edit-card-btn');
        if (editBtn) {
            const cardContainer = editBtn.closest('[data-card-id]');
            enterEditMode(cardContainer);
            return;
        }

        // Handle save button clicks
        const saveBtn = event.target.closest('.save-card-btn');
        if (saveBtn) {
            const cardContainer = saveBtn.closest('[data-card-id]');
            saveCardChanges(cardContainer);
            return;
        }

        // Handle cancel button clicks
        const cancelBtn = event.target.closest('.cancel-edit-btn');
        if (cancelBtn) {
            const cardContainer = cancelBtn.closest('[data-card-id]');
            cancelEdit(cardContainer);
            return;
        }
    });

    // Initial setup
    showSlide(currentSlideIndex);

    // Keyboard navigation
    document.addEventListener('keydown', function(event) {
        // Handle ESC key to exit edit mode
        if (event.key === 'Escape') {
            const editModeCard = document.querySelector('.card-edit-mode:not(.hidden)');
            if (editModeCard) {
                const cardContainer = editModeCard.closest('[data-card-id]');
                if (cardContainer) {
                    cancelEdit(cardContainer);
                }
            }
            return;
        }

        // Disable arrow key navigation during edit mode
        if (document.body.getAttribute('data-edit-mode') === 'true') {
            return;
        }

        if (event.key === 'ArrowLeft') {
            prevSlide();
        } else if (event.key === 'ArrowRight') {
            nextSlide();
        }
    });

    // Swipe/Drag functionality
    let startX;
    let isDragging = false;
    let initialScrollLeft;

    carouselSlides.addEventListener('mousedown', (e) => {
        // Disable drag during edit mode
        if (document.body.getAttribute('data-edit-mode') === 'true') {
            return;
        }

        isDragging = true;
        startX = e.pageX;
        initialScrollLeft = carouselSlides.scrollLeft;
        carouselSlides.style.cursor = 'grabbing';
    });

    carouselSlides.addEventListener('mouseleave', () => {
        if (isDragging) {
            isDragging = false;
            carouselSlides.style.cursor = 'grab';
        }
    });

    carouselSlides.addEventListener('mouseup', () => {
        isDragging = false;
        carouselSlides.style.cursor = 'grab';
        // When mouseup, let scroll-snap handle the snapping.
        // No need to call showSlide here explicitly for snapping.
    });

    carouselSlides.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        // Disable drag during edit mode
        if (document.body.getAttribute('data-edit-mode') === 'true') {
            return;
        }

        e.preventDefault();
        const x = e.pageX;
        const walk = (x - startX) * 1.5;
        carouselSlides.scrollLeft = initialScrollLeft - walk;
    });

    carouselSlides.addEventListener('touchend', (e) => {
        // Prevent touch interactions during edit mode
        if (document.body.getAttribute('data-edit-mode') === 'true') {
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

    carouselSlides.addEventListener('touchstart', (e) => {
        startX = e.touches[0].pageX;
        initialScrollLeft = carouselSlides.scrollLeft;
    });

    carouselSlides.addEventListener('touchmove', (e) => {
        // Prevent touch interactions during edit mode
        if (document.body.getAttribute('data-edit-mode') === 'true') {
            e.preventDefault();
            return;
        }

        const x = e.touches[0].pageX;
        const walk = (x - startX) * 1.5;
        carouselSlides.scrollLeft = initialScrollLeft - walk;
    });

    carouselSlides.addEventListener('touchstart', (e) => {
        // Prevent touch interactions during edit mode
        if (document.body.getAttribute('data-edit-mode') === 'true') {
            e.preventDefault();
            return;
        }

        startX = e.touches[0].pageX;
        initialScrollLeft = carouselSlides.scrollLeft;
    });

    // Edit functionality functions
    function enterEditMode(cardContainer) {
        const viewMode = cardContainer.querySelector('.card-view-mode');
        const editMode = cardContainer.querySelector('.card-edit-mode');

        if (viewMode && editMode) {
            viewMode.classList.add('hidden');
            editMode.classList.remove('hidden');

            // Store original data for cancel functionality
            storeOriginalData(cardContainer);

            // Enable edit mode state
            enableEditModeState();
        }
    }

    function exitEditMode(cardContainer) {
        const viewMode = cardContainer.querySelector('.card-view-mode');
        const editMode = cardContainer.querySelector('.card-edit-mode');

        if (viewMode && editMode) {
            viewMode.classList.remove('hidden');
            editMode.classList.add('hidden');

            // Disable edit mode state
            disableEditModeState();
        }
    }

    function storeOriginalData(cardContainer) {
        const editMode = cardContainer.querySelector('.card-edit-mode');
        const originalData = {
            word: editMode.querySelector('.edit-word').value,
            phonetic: editMode.querySelector('.edit-phonetic').value,
            partOfSpeech: editMode.querySelector('.edit-part-of-speech').value,
            audioUrl: editMode.querySelector('.edit-audio-url').value,
            definitions: []
        };

        // Store definition data
        const englishDefs = editMode.querySelectorAll('.edit-english-def');
        const vietnameseDefs = editMode.querySelectorAll('.edit-vietnamese-def');

        for (let i = 0; i < englishDefs.length; i++) {
            originalData.definitions.push({
                english: englishDefs[i].value,
                vietnamese: vietnameseDefs[i] ? vietnameseDefs[i].value : ''
            });
        }

        cardContainer.dataset.originalData = JSON.stringify(originalData);
    }

    function restoreOriginalData(cardContainer) {
        const originalData = JSON.parse(cardContainer.dataset.originalData || '{}');
        const editMode = cardContainer.querySelector('.card-edit-mode');

        if (originalData && editMode) {
            editMode.querySelector('.edit-word').value = originalData.word || '';
            editMode.querySelector('.edit-phonetic').value = originalData.phonetic || '';
            editMode.querySelector('.edit-part-of-speech').value = originalData.partOfSpeech || '';
            editMode.querySelector('.edit-audio-url').value = originalData.audioUrl || '';

            // Restore definitions
            const englishDefs = editMode.querySelectorAll('.edit-english-def');
            const vietnameseDefs = editMode.querySelectorAll('.edit-vietnamese-def');

            originalData.definitions.forEach((def, index) => {
                if (englishDefs[index]) englishDefs[index].value = def.english;
                if (vietnameseDefs[index]) vietnameseDefs[index].value = def.vietnamese;
            });
        }
    }

    function cancelEdit(cardContainer) {
        const confirmCancel = window.manual_texts?.confirm_cancel_edit ||
                             'Are you sure you want to cancel? Unsaved changes will be lost.';

        if (confirm(confirmCancel)) {
            restoreOriginalData(cardContainer);
            exitEditMode(cardContainer);
        }
    }

    function saveCardChanges(cardContainer) {
        const cardId = cardContainer.dataset.cardId;
        const editMode = cardContainer.querySelector('.card-edit-mode');

        // Collect form data
        const formData = {
            card_id: cardId,
            word: editMode.querySelector('.edit-word').value.trim(),
            phonetic: editMode.querySelector('.edit-phonetic').value.trim(),
            part_of_speech: editMode.querySelector('.edit-part-of-speech').value.trim(),
            audio_url: editMode.querySelector('.edit-audio-url').value.trim(),
            definitions: []
        };

        // Collect definitions
        const englishDefs = editMode.querySelectorAll('.edit-english-def');
        const vietnameseDefs = editMode.querySelectorAll('.edit-vietnamese-def');

        for (let i = 0; i < englishDefs.length; i++) {
            const englishDef = englishDefs[i].value.trim();
            const vietnameseDef = vietnameseDefs[i] ? vietnameseDefs[i].value.trim() : '';

            if (englishDef && vietnameseDef) {
                formData.definitions.push({
                    english_definition: englishDef,
                    vietnamese_definition: vietnameseDef
                });
            }
        }

        // Validate required fields
        if (!formData.word) {
            showMessage('Word is required', 'error');
            return;
        }

        if (formData.definitions.length === 0) {
            showMessage('At least one definition is required', 'error');
            return;
        }

        // Show loading state
        const saveBtn = editMode.querySelector('.save-card-btn');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = 'Saving...';
        saveBtn.disabled = true;

        // Send update request
        fetch('/api/update-flashcard/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCardDisplay(cardContainer, data.card);
                exitEditMode(cardContainer);
                showMessage(window.manual_texts?.card_updated_successfully || 'Card updated successfully!', 'success');
            } else {
                showMessage(data.error || (window.manual_texts?.error_updating_card || 'Error updating card'), 'error');
            }
        })
        .catch(error => {
            console.error('Error updating card:', error);
            showMessage(window.manual_texts?.error_updating_card || 'Error updating card', 'error');
        })
        .finally(() => {
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        });
    }

    function updateCardDisplay(cardContainer, cardData) {
        const viewMode = cardContainer.querySelector('.card-view-mode');

        // Update word
        const wordLink = viewMode.querySelector('a');
        if (wordLink) {
            wordLink.textContent = cardData.word;
            wordLink.href = `https://dictionary.cambridge.org/dictionary/english/${cardData.word}`;
        }

        // Update part of speech
        const posElement = viewMode.querySelector('.text-lg.text-gray-400.mb-2.italic');
        if (posElement) {
            if (cardData.part_of_speech) {
                posElement.textContent = `(${cardData.part_of_speech})`;
                posElement.style.display = 'block';
            } else {
                posElement.style.display = 'none';
            }
        }

        // Update phonetic and audio
        const phoneticContainer = viewMode.querySelector('.text-lg.text-gray-400.font-serif.italic.mb-4');
        if (phoneticContainer) {
            const phoneticSpan = phoneticContainer.querySelector('span');
            const audioBtn = phoneticContainer.querySelector('.audio-icon-tailwind');

            if (cardData.phonetic) {
                phoneticSpan.textContent = cardData.phonetic;
                phoneticContainer.style.display = 'flex';

                if (cardData.audio_url && audioBtn) {
                    audioBtn.dataset.audioUrl = cardData.audio_url;
                    audioBtn.style.display = 'block';
                } else if (audioBtn) {
                    audioBtn.style.display = 'none';
                }
            } else {
                phoneticContainer.style.display = 'none';
            }
        }

        // Update definitions
        const definitionContainers = viewMode.querySelectorAll('.text-base.text-gray-300.leading-relaxed.mb-2');

        // Remove existing definitions
        definitionContainers.forEach(container => container.remove());

        // Add new definitions
        if (cardData.definitions && cardData.definitions.length > 0) {
            cardData.definitions.forEach(def => {
                const englishDiv = document.createElement('div');
                englishDiv.className = 'text-base text-gray-300 leading-relaxed mb-2';
                englishDiv.innerHTML = `<span class="font-semibold text-primary-color">EN:</span> ${def.english_definition}`;

                const vietnameseDiv = document.createElement('div');
                vietnameseDiv.className = 'text-base text-gray-300 leading-relaxed mb-2';
                vietnameseDiv.innerHTML = `<span class="font-semibold text-primary-color">VI:</span> ${def.vietnamese_definition}`;

                viewMode.appendChild(englishDiv);
                viewMode.appendChild(vietnameseDiv);
            });
        } else {
            // Show a message if no definitions
            const noDefDiv = document.createElement('div');
            noDefDiv.className = 'text-base text-gray-400 leading-relaxed mb-2 italic';
            noDefDiv.textContent = 'No definitions available';
            viewMode.appendChild(noDefDiv);
        }
    }

    function showMessage(message, type) {
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `fixed top-4 right-4 px-6 py-3 rounded-md text-white font-medium z-50 transition-all duration-300 ${
            type === 'success' ? 'bg-green-600' : 'bg-red-600'
        }`;
        messageDiv.textContent = message;

        document.body.appendChild(messageDiv);

        // Auto remove after 3 seconds
        setTimeout(() => {
            messageDiv.style.opacity = '0';
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 300);
        }, 3000);
    }

    // Edit mode state management functions
    function enableEditModeState() {
        document.body.setAttribute('data-edit-mode', 'true');

        // Disable scroll-snap behavior
        carouselSlides.style.scrollSnapType = 'none';

        // Add visual feedback
        carouselSlides.style.cursor = 'default';

        // Prevent accidental scrolling
        carouselSlides.style.overflowX = 'hidden';
    }

    function disableEditModeState() {
        document.body.removeAttribute('data-edit-mode');

        // Re-enable scroll-snap behavior
        carouselSlides.style.scrollSnapType = 'x mandatory';

        // Restore cursor
        carouselSlides.style.cursor = 'grab';

        // Re-enable scrolling
        carouselSlides.style.overflowX = 'auto';
    }
});