/**
 * Enhanced Audio Manager
 * Manages enhanced audio fetching, preview, and selection functionality
 */

class EnhancedAudioManager {
    constructor() {
        this.modal = null;
        this.currentCardId = null;
        this.currentWord = null;
        this.audioOptions = [];
        this.selectedAudioUrl = null;
        this.currentAudio = null;
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        // Create modal HTML structure
        this.createModalStructure();
        
        // Bind event listeners
        this.bindEventListeners();
        
        this.isInitialized = true;
        console.log('Enhanced Audio Manager initialized');
    }
    
    createModalStructure() {
        const modalHTML = `
            <div id="enhanced-audio-modal" class="audio-modal">
                <div class="audio-modal-overlay"></div>
                <div class="audio-modal-content">
                    <div class="audio-modal-header">
                        <h3 class="audio-modal-title">
                            ${window.manual_texts?.select_audio_pronunciation || 'Select Audio Pronunciation for:'} 
                            <span class="word-display"></span>
                        </h3>
                        <button class="audio-modal-close" type="button">&times;</button>
                    </div>
                    <div class="audio-modal-body">
                        <div class="current-audio-section">
                            <div class="current-audio-title">
                                <i class="fas fa-volume-up"></i>
                                ${window.manual_texts?.current_audio || 'Current Audio'}
                            </div>
                            <div class="current-audio-content">
                                <!-- Current audio will be inserted here -->
                            </div>
                        </div>
                        <div class="audio-options-container">
                            <div class="audio-options-title">
                                <i class="fas fa-list"></i>
                                ${window.manual_texts?.available_audio_options || 'Available Audio Options'}
                            </div>
                            <div class="audio-options-content">
                                <!-- Audio options will be inserted here -->
                            </div>
                        </div>
                    </div>
                    <div class="audio-modal-footer">
                        <button class="btn-cancel" type="button">
                            ${window.manual_texts?.cancel || 'Cancel'}
                        </button>
                        <button class="btn-keep-current" type="button">
                            ${window.manual_texts?.keep_current || 'Keep Current'}
                        </button>
                        <button class="btn-confirm-selection" type="button" disabled>
                            ${window.manual_texts?.confirm_selection || 'Confirm Selection'}
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Insert modal into DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('enhanced-audio-modal');
    }
    
    bindEventListeners() {
        if (!this.modal) return;
        
        // Close modal events
        const closeBtn = this.modal.querySelector('.audio-modal-close');
        const overlay = this.modal.querySelector('.audio-modal-overlay');
        const cancelBtn = this.modal.querySelector('.btn-cancel');
        
        closeBtn?.addEventListener('click', () => this.closeModal());
        overlay?.addEventListener('click', () => this.closeModal());
        cancelBtn?.addEventListener('click', () => this.closeModal());
        
        // Footer button events
        const keepCurrentBtn = this.modal.querySelector('.btn-keep-current');
        const confirmBtn = this.modal.querySelector('.btn-confirm-selection');
        
        keepCurrentBtn?.addEventListener('click', () => this.closeModal());
        confirmBtn?.addEventListener('click', () => this.confirmSelection());
        
        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (this.modal?.classList.contains('show') && e.key === 'Escape') {
                this.closeModal();
            }
        });
    }
    
    async showAudioSelectionModal(cardId, word) {
        if (!this.modal) {
            console.error('Modal not initialized');
            return;
        }

        // Validate input parameters
        if (!cardId || !word) {
            console.error('Invalid parameters:', { cardId, word });
            return;
        }

        console.log(`Opening enhanced audio modal for card ${cardId}, word: ${word}`);

        // Clean up any previous state
        this.cleanupAudio();
        this.resetModalUI();

        // Set new state
        this.currentCardId = cardId;
        this.currentWord = word;
        this.selectedAudioUrl = null;
        this.audioOptions = [];

        // Update modal title
        const wordDisplay = this.modal.querySelector('.word-display');
        if (wordDisplay) {
            wordDisplay.textContent = word;
        }

        // Show modal
        this.modal.classList.add('show');
        document.body.style.overflow = 'hidden';

        // Show loading state
        this.showLoadingState();

        try {
            // Fetch audio options
            const response = await this.fetchAudioOptions(cardId, word);

            if (response.success) {
                this.audioOptions = response.audio_options || [];
                this.renderCurrentAudio(response.current_audio);
                this.renderAudioOptions(this.audioOptions);

                if (this.audioOptions.length === 0) {
                    this.showNoOptionsState();
                }
            } else {
                this.showErrorState(response.error || 'Failed to fetch audio options');
            }
        } catch (error) {
            console.error('Error fetching audio options:', error);
            this.showErrorState('Network error occurred while fetching audio options');
        }
    }
    
    async fetchAudioOptions(cardId, word) {
        const response = await fetch('/api/fetch-enhanced-audio/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            },
            body: JSON.stringify({
                card_id: cardId,
                word: word
            })
        });
        
        return await response.json();
    }
    
    renderCurrentAudio(currentAudioUrl) {
        const container = this.modal.querySelector('.current-audio-content');
        if (!container) return;

        console.log(`Rendering current audio: ${currentAudioUrl}`);

        if (currentAudioUrl && currentAudioUrl.trim()) {
            container.innerHTML = `
                <div class="current-audio-item">
                    <div class="current-audio-info">
                        ${window.manual_texts?.current_audio || 'Current Audio'}
                    </div>
                    <button class="btn-preview" data-audio-url="${currentAudioUrl}">
                        <i class="fas fa-play"></i> ${window.manual_texts?.preview || 'Preview'}
                    </button>
                </div>
            `;
            console.log('Current audio preview button created with URL:', currentAudioUrl);
        } else {
            container.innerHTML = `
                <div class="no-current-audio">
                    ${window.manual_texts?.no_current_audio || 'No current audio'}
                </div>
            `;
            console.log('No current audio available');
        }

        // Rebind events after rendering new content
        this.bindCurrentAudioEvents();
    }
    
    renderAudioOptions(options) {
        const container = this.modal.querySelector('.audio-options-content');
        if (!container) return;
        
        if (options.length === 0) {
            this.showNoOptionsState();
            return;
        }
        
        const optionsHTML = options.map((option, index) => {
            if (!option.is_valid) {
                return `
                    <div class="audio-option error">
                        <div class="audio-option-header">
                            <input type="radio" name="audio-selection" value="${option.url}" id="audio-${index}" disabled>
                            <label for="audio-${index}" class="audio-label">${option.label}</label>
                        </div>
                        <div class="audio-controls">
                            <div class="audio-status">
                                <span class="status-indicator error"></span>
                                <span class="status-text">${option.error_message || 'Error'}</span>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            return `
                <div class="audio-option" data-audio-url="${option.url}">
                    <div class="audio-option-header">
                        <input type="radio" name="audio-selection" value="${option.url}" id="audio-${index}">
                        <label for="audio-${index}" class="audio-label">${option.label}</label>
                    </div>
                    <div class="audio-controls">
                        <button class="btn-preview" data-audio-url="${option.url}">
                            <i class="fas fa-play"></i> ${window.manual_texts?.preview || 'Preview'}
                        </button>
                        <div class="audio-status">
                            <span class="status-indicator ready"></span>
                            <span class="status-text">${window.manual_texts?.ready || 'Ready'}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = optionsHTML;
        
        // Bind events for new elements
        this.bindAudioOptionEvents();
    }
    
    bindAudioOptionEvents() {
        const container = this.modal.querySelector('.audio-options-content');
        if (!container) return;

        // Remove any existing event listeners to prevent duplicates
        this.unbindAudioOptionEvents();

        // Also bind events for current audio section
        this.bindCurrentAudioEvents();

        // Click-to-select functionality for entire audio option containers
        this.audioOptionsClickHandler = (e) => {
            const previewBtn = e.target.closest('.btn-preview');
            const audioOption = e.target.closest('.audio-option');

            // Handle preview button clicks
            if (previewBtn) {
                const audioUrl = previewBtn.dataset.audioUrl;
                if (audioUrl) {
                    this.previewAudio(audioUrl, previewBtn);
                }
                return; // Don't trigger selection when clicking preview button
            }

            // Handle audio option container clicks (click-to-select)
            if (audioOption && !audioOption.classList.contains('error')) {
                const radioButton = audioOption.querySelector('input[type="radio"]');
                if (radioButton && !radioButton.disabled) {
                    // Select the radio button
                    radioButton.checked = true;

                    // Trigger the change event manually to ensure all handlers run
                    const changeEvent = new Event('change', { bubbles: true });
                    radioButton.dispatchEvent(changeEvent);

                    console.log(`Audio option selected via container click: ${radioButton.value}`);
                }
            }
        };

        // Radio button change events
        this.audioOptionsChangeHandler = (e) => {
            if (e.target.type === 'radio') {
                this.handleAudioSelection(e.target.value);

                // Update visual selection
                container.querySelectorAll('.audio-option').forEach(option => {
                    option.classList.remove('selected');
                });

                const selectedOption = e.target.closest('.audio-option');
                if (selectedOption) {
                    selectedOption.classList.add('selected');
                }
            }
        };

        // Attach event listeners
        container.addEventListener('click', this.audioOptionsClickHandler);
        container.addEventListener('change', this.audioOptionsChangeHandler);
    }

    unbindAudioOptionEvents() {
        const container = this.modal?.querySelector('.audio-options-content');
        if (!container) return;

        // Remove existing event listeners if they exist
        if (this.audioOptionsClickHandler) {
            container.removeEventListener('click', this.audioOptionsClickHandler);
            this.audioOptionsClickHandler = null;
        }

        if (this.audioOptionsChangeHandler) {
            container.removeEventListener('change', this.audioOptionsChangeHandler);
            this.audioOptionsChangeHandler = null;
        }

        // Also clean up current audio events
        this.unbindCurrentAudioEvents();

        console.log('Audio option event listeners cleaned up');
    }

    bindCurrentAudioEvents() {
        const currentAudioContainer = this.modal.querySelector('.current-audio-content');
        if (!currentAudioContainer) return;

        // Remove existing event listener if it exists
        if (this.currentAudioClickHandler) {
            currentAudioContainer.removeEventListener('click', this.currentAudioClickHandler);
        }

        // Create event handler for current audio preview button
        this.currentAudioClickHandler = (e) => {
            const previewBtn = e.target.closest('.btn-preview');
            if (previewBtn) {
                const audioUrl = previewBtn.dataset.audioUrl;
                if (audioUrl) {
                    console.log(`Current audio preview clicked: ${audioUrl}`);
                    this.previewAudio(audioUrl, previewBtn);
                } else {
                    console.warn('Current audio preview button has no audio URL');
                }
            }
        };

        // Attach event listener
        currentAudioContainer.addEventListener('click', this.currentAudioClickHandler);
        console.log('Current audio event listeners bound');
    }

    unbindCurrentAudioEvents() {
        const currentAudioContainer = this.modal?.querySelector('.current-audio-content');
        if (!currentAudioContainer) return;

        // Remove existing event listener if it exists
        if (this.currentAudioClickHandler) {
            currentAudioContainer.removeEventListener('click', this.currentAudioClickHandler);
            this.currentAudioClickHandler = null;
            console.log('Current audio event listeners cleaned up');
        }
    }
    
    previewAudio(audioUrl, buttonElement) {
        console.log(`Previewing audio: ${audioUrl}`);

        // Stop current audio if playing
        this.cleanupAudio();

        try {
            // Create new audio instance
            this.currentAudio = new Audio(audioUrl);

            // Set up audio event handlers before playing
            this.currentAudio.addEventListener('ended', () => {
                console.log('Audio playback ended');
                buttonElement.classList.remove('playing');
                buttonElement.innerHTML = `<i class="fas fa-play"></i> ${window.manual_texts?.preview || 'Preview'}`;
                this.currentAudio = null;
            });

            this.currentAudio.addEventListener('error', (error) => {
                console.error('Audio error:', error);
                this.showAudioError(buttonElement, 'Audio load failed');
            });

            // Update button state
            buttonElement.classList.add('playing');
            buttonElement.innerHTML = `<i class="fas fa-pause"></i> ${window.manual_texts?.playing || 'Playing'}`;

            // Play audio with proper error handling
            const playPromise = this.currentAudio.play();

            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        console.log('Audio playback started successfully');
                    })
                    .catch(error => {
                        console.error('Audio playback error:', error);
                        this.showAudioError(buttonElement, 'Playback failed');
                    });
            }

        } catch (error) {
            console.error('Error creating Audio object:', error);
            this.showAudioError(buttonElement, 'Audio not supported');
        }
    }
    
    showAudioError(buttonElement, message) {
        buttonElement.classList.remove('playing');
        buttonElement.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${window.manual_texts?.error || 'Error'}`;
        buttonElement.disabled = true;
        
        const statusText = buttonElement.parentElement?.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = message;
        }
    }
    
    handleAudioSelection(audioUrl) {
        this.selectedAudioUrl = audioUrl;
        
        // Enable confirm button
        const confirmBtn = this.modal.querySelector('.btn-confirm-selection');
        if (confirmBtn) {
            confirmBtn.disabled = false;
        }
    }
    
    async confirmSelection() {
        if (!this.selectedAudioUrl) {
            // Show validation error using the existing showMessage function
            if (window.showMessage) {
                window.showMessage(window.manual_texts?.please_select_audio || 'Please select an audio option', 'error');
            } else {
                // Fallback notification if showMessage is not available
                this.showMessage(window.manual_texts?.please_select_audio || 'Please select an audio option', 'warning');
            }
            return;
        }

        // Disable confirm button to prevent double-clicks
        const confirmBtn = this.modal.querySelector('.btn-confirm-selection');
        if (confirmBtn) {
            confirmBtn.disabled = true;
            confirmBtn.textContent = window.manual_texts?.saving || 'Saving...';
        }

        try {
            console.log(`Updating flashcard ${this.currentCardId} with audio URL: ${this.selectedAudioUrl}`);

            const response = await this.updateFlashcardAudio(this.currentCardId, this.selectedAudioUrl);

            console.log('Update response:', response);

            if (response.success) {
                // Store values before closing modal (which resets state)
                const cardId = this.currentCardId;
                const audioUrl = this.selectedAudioUrl;

                console.log(`Success! Updating UI for card ${cardId} with audio: ${audioUrl}`);

                // Show success notification FIRST (while modal is still open)
                if (window.showMessage) {
                    window.showMessage(
                        window.manual_texts?.audio_selection_updated || 'Audio pronunciation updated successfully!',
                        'success'
                    );
                } else {
                    // Fallback notification if showMessage is not available
                    this.showMessage(
                        window.manual_texts?.audio_selection_updated || 'Audio pronunciation updated successfully!',
                        'success'
                    );
                }

                // Trigger UI refresh BEFORE closing modal
                if (window.updateCardDisplayForAudio) {
                    console.log(`Calling updateCardDisplayForAudio with cardId: ${cardId}, audioUrl: ${audioUrl}`);
                    window.updateCardDisplayForAudio(cardId, { audio_url: audioUrl });
                } else {
                    console.warn('updateCardDisplayForAudio function not available');
                }

                // Update audio statistics
                if (window.updateAudioStats) {
                    console.log('Updating audio stats...');
                    window.updateAudioStats();
                } else {
                    console.warn('updateAudioStats function not available');
                }

                // Close modal LAST (after all updates are complete)
                this.closeModal();

            } else {
                console.error('API returned error:', response.error);

                // Show error notification using the existing showMessage function
                if (window.showMessage) {
                    window.showMessage(
                        response.error || window.manual_texts?.error_updating_audio || 'Error updating audio selection',
                        'error'
                    );
                } else {
                    // Fallback notification if showMessage is not available
                    this.showMessage(
                        response.error || window.manual_texts?.error_updating_audio || 'Error updating audio selection',
                        'error'
                    );
                }

                // Re-enable button on error
                if (confirmBtn) {
                    confirmBtn.disabled = false;
                    confirmBtn.textContent = window.manual_texts?.confirm_selection || 'Confirm Selection';
                }
            }
        } catch (error) {
            console.error('Network error updating flashcard audio:', error);

            // Show error notification using the existing showMessage function
            if (window.showMessage) {
                window.showMessage(
                    window.manual_texts?.error_updating_audio || 'Network error occurred while updating audio selection',
                    'error'
                );
            } else {
                // Fallback notification if showMessage is not available
                this.showMessage(
                    window.manual_texts?.error_updating_audio || 'Network error occurred while updating audio selection',
                    'error'
                );
            }

            // Re-enable button on error
            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.textContent = window.manual_texts?.confirm_selection || 'Confirm Selection';
            }
        }
    }
    
    async updateFlashcardAudio(cardId, audioUrl) {
        // Get CSRF token from multiple possible sources
        let csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (!csrfToken) {
            csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        }
        if (!csrfToken) {
            csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
        }

        console.log('CSRF Token found:', csrfToken ? 'Yes' : 'No');
        console.log('Making API request to /api/update-flashcard-audio/');

        const requestData = {
            card_id: cardId,
            audio_url: audioUrl
        };

        console.log('Request data:', requestData);

        const response = await fetch('/api/update-flashcard-audio/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken || ''
            },
            body: JSON.stringify(requestData)
        });

        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Response error text:', errorText);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const responseData = await response.json();
        console.log('Response data:', responseData);

        return responseData;
    }
    
    showLoadingState() {
        const container = this.modal.querySelector('.audio-options-content');
        if (!container) return;
        
        container.innerHTML = `
            <div class="audio-loading-state">
                <div class="audio-loading-spinner">
                    <i class="fas fa-spinner"></i>
                </div>
                <p class="audio-loading-text">
                    ${window.manual_texts?.fetching_audio_options || 'Fetching audio options...'}
                </p>
            </div>
        `;
    }
    
    showNoOptionsState() {
        const container = this.modal.querySelector('.audio-options-content');
        if (!container) return;
        
        container.innerHTML = `
            <div class="no-audio-options">
                <div class="no-audio-icon">
                    <i class="fas fa-volume-mute"></i>
                </div>
                <p class="no-audio-message">
                    ${window.manual_texts?.no_audio_options_found || 'No audio options found'}
                </p>
                <p class="no-audio-suggestion">
                    ${window.manual_texts?.try_checking_spelling || 'Try checking the word spelling or search manually on Cambridge Dictionary'}
                </p>
            </div>
        `;
    }
    
    showErrorState(errorMessage) {
        const container = this.modal.querySelector('.audio-options-content');
        if (!container) return;
        
        container.innerHTML = `
            <div class="audio-error-state">
                <div class="audio-error-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <p class="audio-error-message">
                    ${window.manual_texts?.error || 'Error'}
                </p>
                <p class="audio-error-details">
                    ${errorMessage}
                </p>
            </div>
        `;
    }
    
    closeModal() {
        if (!this.modal) return;

        console.log('Closing enhanced audio modal and cleaning up state...');

        // Stop any playing audio and clean up
        this.cleanupAudio();

        // Clean up event listeners
        this.unbindAudioOptionEvents();

        // Hide modal
        this.modal.classList.remove('show');
        document.body.style.overflow = '';

        // Reset all state variables
        this.currentCardId = null;
        this.currentWord = null;
        this.audioOptions = [];
        this.selectedAudioUrl = null;

        // Reset UI elements
        this.resetModalUI();

        console.log('Modal closed and state reset successfully');
    }

    cleanupAudio() {
        // Stop current audio if playing
        if (this.currentAudio) {
            try {
                this.currentAudio.pause();
                this.currentAudio.currentTime = 0;
                this.currentAudio = null;
                console.log('Audio cleanup completed');
            } catch (error) {
                console.warn('Error during audio cleanup:', error);
                this.currentAudio = null;
            }
        }

        // Reset all preview buttons
        if (this.modal) {
            const previewButtons = this.modal.querySelectorAll('.btn-preview');
            previewButtons.forEach(btn => {
                btn.classList.remove('playing');
                btn.innerHTML = `<i class="fas fa-play"></i> ${window.manual_texts?.preview || 'Preview'}`;
                btn.disabled = false;
            });
        }
    }

    resetModalUI() {
        if (!this.modal) return;

        // Reset confirm button
        const confirmBtn = this.modal.querySelector('.btn-confirm-selection');
        if (confirmBtn) {
            confirmBtn.disabled = true;
            confirmBtn.textContent = window.manual_texts?.confirm_selection || 'Confirm Selection';
        }

        // Clear content areas
        const currentAudioContent = this.modal.querySelector('.current-audio-content');
        if (currentAudioContent) {
            currentAudioContent.innerHTML = '';
        }

        const audioOptionsContent = this.modal.querySelector('.audio-options-content');
        if (audioOptionsContent) {
            audioOptionsContent.innerHTML = '';
        }

        // Reset word display
        const wordDisplay = this.modal.querySelector('.word-display');
        if (wordDisplay) {
            wordDisplay.textContent = '';
        }

        console.log('Modal UI reset completed');
    }
    
    showMessage(message, type = 'info') {
        // Use existing message system if available
        if (window.showMessage) {
            window.showMessage(message, type);
        } else {
            // Fallback to console
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// Initialize Enhanced Audio Manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.EnhancedAudioManager = new EnhancedAudioManager();
});
