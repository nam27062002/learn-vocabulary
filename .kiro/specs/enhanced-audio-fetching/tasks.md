# Implementation Plan

- [ ] 1. Enhance the audio service backend infrastructure
  - Create enhanced audio fetching service class that extends existing CambridgeAudioFetcher
  - Implement multiple XPath selector support for audio1 and audio2 elements
  - Add audio URL validation and pronunciation label extraction functionality
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3_

- [ ] 1.1 Create AudioOption data structure and enhanced service class
  - Define AudioOption dataclass with url, label, selector_source, is_valid, and error_message fields
  - Create EnhancedCambridgeAudioFetcher class extending existing CambridgeAudioFetcher
  - Implement AUDIO_SELECTORS configuration with xpath and label extraction rules
  - _Requirements: 2.1, 2.2_

- [ ] 1.2 Implement multiple audio source extraction methods
  - Code fetch_multiple_audio_sources method to extract from both audio1 and audio2 selectors
  - Write extract_audio_from_multiple_selectors method to process HTML tree with multiple XPath queries
  - Implement validate_audio_urls method to verify audio URL accessibility
  - Create get_pronunciation_labels method to extract pronunciation type labels from Cambridge Dictionary
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 1.3 Add enhanced audio service integration utilities
  - Create service factory function to instantiate enhanced audio fetcher
  - Implement error handling and logging for multiple audio source failures
  - Add rate limiting protection for multiple XPath extractions
  - Write unit tests for enhanced audio service methods
  - _Requirements: 6.3, 7.3_

- [ ] 2. Create enhanced audio fetching API endpoint
  - Implement new API endpoint for fetching multiple audio options from Cambridge Dictionary
  - Add request validation and error handling for enhanced audio fetching
  - Create response formatting for multiple audio options with metadata
  - _Requirements: 1.1, 1.3, 6.1, 6.2_

- [ ] 2.1 Implement enhanced audio fetching API endpoint
  - Create api_fetch_enhanced_audio view function with POST method requirement
  - Add request parsing for card_id and word parameters with validation
  - Integrate enhanced audio service to fetch multiple pronunciation options
  - Implement comprehensive error handling for network failures and invalid responses
  - _Requirements: 1.1, 1.3, 6.3_

- [ ] 2.2 Add API response formatting and validation
  - Create response JSON structure with current_audio, audio_options array, and metadata
  - Implement audio URL validation before including in response
  - Add pronunciation label formatting and fallback handling
  - Write API endpoint unit tests covering success and failure scenarios
  - _Requirements: 2.3, 2.4, 6.2_

- [ ] 3. Build audio selection modal interface
  - Create modal HTML structure for audio option selection and preview
  - Implement responsive design for mobile and desktop compatibility
  - Add audio preview controls and selection radio buttons
  - _Requirements: 3.1, 3.2, 3.3, 7.1_

- [ ] 3.1 Create modal HTML structure and styling
  - Write modal HTML template with header, body, and footer sections
  - Implement CSS styling for modal overlay, content container, and responsive design
  - Create audio option component template with preview controls and selection inputs
  - Add modal animation and transition effects for smooth user experience
  - _Requirements: 3.1, 3.2, 7.1_

- [ ] 3.2 Implement audio option rendering and display logic
  - Create JavaScript function to dynamically render audio options from API response
  - Implement current audio display section showing existing flashcard audio
  - Add visual indicators for audio option status (loading, ready, error)
  - Write responsive layout handling for different screen sizes and orientations
  - _Requirements: 3.1, 3.2, 7.1_

- [ ] 4. Develop audio preview and selection functionality
  - Implement client-side audio preview system with play/pause controls
  - Add audio selection handling with radio button management
  - Create audio playback error handling and user feedback
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 4.1 Create audio preview system
  - Implement JavaScript audio preview functionality with HTML5 Audio API
  - Add play/pause button state management and visual feedback
  - Create audio loading states and error handling for failed playback
  - Implement audio cleanup and memory management for multiple preview instances
  - _Requirements: 3.1, 3.2, 6.4_

- [ ] 4.2 Implement audio selection and confirmation logic
  - Create radio button selection handling with visual feedback
  - Implement selection validation ensuring user has chosen an option
  - Add confirmation dialog and selection persistence during modal session
  - Write selection cancellation handling with original audio restoration
  - _Requirements: 3.3, 3.4, 4.4_

- [ ] 5. Integrate enhanced audio fetching with deck detail interface
  - Add enhanced audio fetch button to flashcard view mode in deck detail carousel
  - Implement modal trigger functionality from deck detail interface
  - Create seamless integration that doesn't interfere with existing carousel navigation
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 5.1 Add enhanced audio fetch button to deck detail template
  - Modify deck_detail.html template to include enhanced audio fetch button in card view mode
  - Position button appropriately within existing flashcard layout without disrupting design
  - Add button styling consistent with existing deck detail interface elements
  - Implement button state management for loading and disabled states
  - _Requirements: 5.1, 5.2_

- [ ] 5.2 Create modal integration with deck detail carousel
  - Implement modal trigger functionality in deck_detail.js
  - Add modal overlay that doesn't interfere with carousel navigation or edit mode
  - Create modal positioning and z-index management for proper layering
  - Implement modal cleanup and state restoration when closed
  - _Requirements: 5.2, 5.3_

- [ ] 6. Implement enhanced audio manager JavaScript module
  - Create comprehensive JavaScript module for managing enhanced audio functionality
  - Implement API communication for fetching and updating audio options
  - Add modal lifecycle management and user interaction handling
  - _Requirements: 1.1, 3.1, 4.1, 5.4_

- [ ] 6.1 Create EnhancedAudioManager class structure
  - Implement EnhancedAudioManager class with initialization and configuration
  - Add methods for modal display, audio fetching, and option rendering
  - Create event handler registration for modal interactions and audio preview
  - Implement error handling and user feedback messaging system
  - _Requirements: 1.1, 6.1, 6.2_

- [ ] 6.2 Implement API communication and data handling
  - Create fetchAudioOptions method for enhanced audio API communication
  - Implement updateFlashcardAudio method for saving selected audio to flashcard
  - Add response parsing and error handling for API communication failures
  - Write data validation and sanitization for audio URLs and metadata
  - _Requirements: 1.3, 4.4, 6.3_

- [ ] 6.3 Add modal lifecycle and interaction management
  - Implement showAudioSelectionModal and closeModal methods with proper cleanup
  - Create handleAudioSelection method for processing user audio choice
  - Add previewAudio method with audio playback management and error handling
  - Implement modal state persistence and restoration during user session
  - _Requirements: 3.4, 4.1, 5.3_

- [ ] 7. Update existing audio statistics and UI refresh functionality
  - Modify audio statistics calculation to account for enhanced audio updates
  - Implement UI refresh logic after audio selection to update deck detail display
  - Add integration with existing audio filter and statistics features
  - _Requirements: 5.4, 6.1_

- [ ] 7.1 Update audio statistics integration
  - Modify updateAudioStats function in deck_detail.js to handle enhanced audio updates
  - Update audio filter functionality to work with newly selected audio options
  - Implement real-time statistics refresh after audio selection confirmation
  - Add audio status indicator updates for flashcards with newly selected audio
  - _Requirements: 5.4_

- [ ] 7.2 Implement UI refresh and display updates
  - Create updateCardDisplay integration for enhanced audio selection results
  - Implement audio icon and phonetic display updates after audio selection
  - Add visual feedback for successful audio updates in deck detail interface
  - Write flashcard carousel refresh logic to reflect new audio information
  - _Requirements: 5.4, 6.1_

- [ ] 8. Add comprehensive error handling and user feedback
  - Implement robust error handling for network failures and service unavailability
  - Create user-friendly error messages and recovery suggestions
  - Add loading states and progress indicators for enhanced audio fetching
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 8.1 Create comprehensive error handling system
  - Implement error handling for Cambridge Dictionary service unavailability
  - Add network timeout and retry logic with exponential backoff
  - Create user-friendly error messages for different failure scenarios
  - Write error recovery suggestions and alternative action guidance
  - _Requirements: 6.3, 6.4, 7.3_

- [ ] 8.2 Implement loading states and user feedback
  - Add loading indicators during enhanced audio fetching process
  - Create progress feedback showing number of audio options found
  - Implement success messaging for completed audio selection
  - Add confirmation dialogs for critical user actions and selections
  - _Requirements: 6.1, 6.2_

- [ ] 9. Write comprehensive tests for enhanced audio functionality
  - Create unit tests for enhanced audio service methods and API endpoints
  - Implement integration tests for end-to-end audio selection workflow
  - Add JavaScript tests for modal functionality and audio preview system
  - _Requirements: All requirements - comprehensive testing coverage_

- [ ] 9.1 Create backend unit and integration tests
  - Write unit tests for EnhancedCambridgeAudioFetcher class methods
  - Create API endpoint tests for enhanced audio fetching functionality
  - Implement integration tests for audio service and database interactions
  - Add error handling and edge case tests for network failures and invalid data
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2_

- [ ] 9.2 Implement frontend JavaScript tests
  - Create unit tests for EnhancedAudioManager class methods
  - Write integration tests for modal functionality and user interactions
  - Implement audio preview and selection workflow tests
  - Add browser compatibility and responsive design tests
  - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 7.1_

- [ ] 10. Finalize integration and deployment preparation
  - Integrate all components into cohesive enhanced audio fetching system
  - Perform end-to-end testing of complete audio selection workflow
  - Update documentation and add feature usage instructions
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 10.1 Complete system integration and testing
  - Integrate enhanced audio service with existing deck detail interface
  - Perform comprehensive end-to-end testing of audio selection workflow
  - Test integration with existing audio statistics and filtering functionality
  - Validate mobile responsiveness and cross-browser compatibility
  - _Requirements: 5.1, 5.2, 5.3, 7.1_

- [ ] 10.2 Finalize documentation and deployment
  - Update existing audio service documentation to include enhanced functionality
  - Create user guide for enhanced audio selection feature
  - Perform final code review and optimization
  - Prepare feature for production deployment with proper error monitoring
  - _Requirements: All requirements - final integration and documentation_