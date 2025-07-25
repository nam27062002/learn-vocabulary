// study.js - handles study session with multiple modes

(function () {
  // Existing elements
  const deckStudyOptions = document.getElementById('deckStudyOptions');
  const studyArea = document.getElementById('studyArea');
  const cardWordEl = document.getElementById('cardWord');
  const cardPhoneticEl = document.getElementById('cardPhonetic');
  const cardImageEl = document.getElementById('cardImage');
  const cardDefsEl = document.getElementById('cardDefs');
  const answerArea = document.getElementById('answerSection') || { innerHTML: '', appendChild: () => { }, style: {} };
  const feedbackMsg = document.getElementById('feedbackMsg') || { style: {}, textContent: '' };
  const noCardMsg = document.getElementById('noCardMsg') || { style: {} };
  const optionsArea = document.getElementById('optionsArea') || answerArea;
  const backBtn = document.getElementById('backBtn');
  const statsInfo = document.getElementById('statsInfo');
  const studyHeader = document.querySelector('.study-header');

  const audioButton = document.getElementById('audioButton');
  const audioToggle = document.getElementById('audioToggle');

  // Audio feedback system
  const AudioFeedback = {
    correctSound: null,
    incorrectSound: null,
    enabled: true,

    init() {
      try {
        // Load audio files
        this.correctSound = new Audio('/static/audio/correct.mp3');
        this.incorrectSound = new Audio('/static/audio/incorrect.mp3');

        // Set volume levels
        this.correctSound.volume = 0.6;
        this.incorrectSound.volume = 0.6;

        // Add error event listeners
        this.correctSound.addEventListener('error', (e) => {
          console.warn('Failed to load correct sound:', e);
          this.correctSound = null;
        });

        this.incorrectSound.addEventListener('error', (e) => {
          console.warn('Failed to load incorrect sound:', e);
          this.incorrectSound = null;
        });

        // Load saved preference from localStorage
        const savedPreference = localStorage.getItem('audioFeedbackEnabled');
        if (savedPreference !== null) {
          this.enabled = savedPreference === 'true';
        }

        // Update toggle state
        if (audioToggle) {
          audioToggle.checked = this.enabled;
          audioToggle.addEventListener('change', (e) => {
            this.enabled = e.target.checked;
            localStorage.setItem('audioFeedbackEnabled', this.enabled.toString());
            console.log('Audio feedback', this.enabled ? 'enabled' : 'disabled');
          });
        }

        // Preload audio files
        this.preloadAudio();

        console.log('Audio feedback system initialized. Enabled:', this.enabled);
      } catch (error) {
        console.error('Failed to initialize audio feedback system:', error);
        this.enabled = false;
      }
    },

    preloadAudio() {
      // Preload audio files to avoid delays
      if (this.correctSound) {
        this.correctSound.load();
      }
      if (this.incorrectSound) {
        this.incorrectSound.load();
      }
    },

    playCorrect() {
      if (this.enabled && this.correctSound) {
        try {
          this.correctSound.currentTime = 0; // Reset to beginning
          this.correctSound.play().catch(err => {
            console.log('Correct sound play failed:', err);
          });
          console.log('Playing correct answer sound');
        } catch (error) {
          console.error('Error playing correct sound:', error);
        }
      }
    },

    playIncorrect() {
      if (this.enabled && this.incorrectSound) {
        try {
          this.incorrectSound.currentTime = 0; // Reset to beginning
          this.incorrectSound.play().catch(err => {
            console.log('Incorrect sound play failed:', err);
          });
          console.log('Playing incorrect answer sound');
        } catch (error) {
          console.error('Error playing incorrect sound:', error);
        }
      }
    }
  };

  // New elements for study mode selection
  const studyModeRadios = document.querySelectorAll('input[name="study_mode"]');
  const randomStudyOptions = document.getElementById('randomStudyOptions');
  const randomWordCountInput = document.getElementById('randomWordCount');
  const totalWordsAvailableSpan = document.getElementById('totalWordsAvailable');
  const startBtnDecks = document.getElementById('startBtn');
  const startBtnRandom = document.getElementById('startRandomBtn');
  const startBtnReview = document.getElementById('startReviewBtn');
  const reviewModeOption = document.getElementById('reviewModeOption');
  const reviewStudyOptions = document.getElementById('reviewStudyOptions');
  const reviewCount = document.getElementById('reviewCount');
  const reviewCountText = document.getElementById('reviewCountText');
  const reviewDetails = document.getElementById('reviewDetails');
  const mcCount = document.getElementById('mcCount');
  const typeCount = document.getElementById('typeCount');
  const dictationCount = document.getElementById('dictationCount');

  // Slider elements
  const modeSlider = document.getElementById('modeSlider');
  const sliderPrev = document.getElementById('sliderPrev');
  const sliderNext = document.getElementById('sliderNext');
  const indicators = document.querySelectorAll('.indicator');
  const modeSlides = document.querySelectorAll('.mode-slide');

  let correctCnt = 0, incorrectCnt = 0;
  let nextTimeout = null;
  let currentStudyMode = 'decks'; // Default mode
  let seenCardIds = []; // To track cards seen in the current session for random mode
  let wordCount = 10; // Default word count for random mode

  // Hàm chuyển đổi từ loại sang viết tắt
  function getAbbreviatedPartOfSpeech(fullPartOfSpeech) {
    if (!fullPartOfSpeech) return '';
    const lowerCase = fullPartOfSpeech.toLowerCase();
    switch (lowerCase) {
      case 'noun': return 'n';
      case 'verb': return 'v';
      case 'adjective': return 'adj';
      case 'adverb': return 'adv';
      case 'preposition': return 'prep';
      case 'conjunction': return 'conj';
      case 'pronoun': return 'pron';
      case 'interjection': return 'interj';
      case 'determiner': return 'det';
      case 'article': return 'art';
      case 'auxiliary verb': return 'aux.v';
      default: return fullPartOfSpeech; // Trả về nguyên gốc nếu không tìm thấy viết tắt
    }
  }

  function updateStats() {
    if (statsInfo) {
      statsInfo.textContent = `${STUDY_CFG.labels.correct}: ${correctCnt} | ${STUDY_CFG.labels.incorrect}: ${incorrectCnt}`;
    }
  }

  let currentQuestion = null;
  let questionStartTime = null;

  function getNextQuestion() {
    const params = new URLSearchParams();
    
    if (currentStudyMode === 'random') {
      params.append('study_mode', 'random');
      params.append('word_count', wordCount);
      seenCardIds.forEach(id => params.append('seen_card_ids[]', id));
    } else if (currentStudyMode === 'review') {
      params.append('study_mode', 'review');
      seenCardIds.forEach(id => params.append('seen_card_ids[]', id));
    } else {
      // Normal deck study mode
      const selectedDeckIds = Array.from(document.querySelectorAll('input[name="deck_ids"]:checked')).map(cb => cb.value);
      selectedDeckIds.forEach(id => params.append('deck_ids[]', id));
    }

    fetch(`${STUDY_CFG.nextUrl}?${params.toString()}`, {
      headers: {
        'X-CSRFToken': STUDY_CFG.csrfToken
      }
    })
    .then(r => r.json())
    .then(data => {
      if (data.done) {
        if (currentStudyMode === 'review') {
          // Check if this is a session completion (all words resolved)
          if (data.session_completed) {
            console.log('Review session completed successfully!');
            showReviewCompletionModal();
            return;
          } else {
            // For review mode, loop back to the beginning instead of ending
            seenCardIds = []; // Reset seen cards to start over
            getNextQuestion(); // Restart the loop
            return;
          }
        } else {
          noCardMsg.className = 'no-cards-message show';
          studyArea.className = 'study-area';
          return;
        }
      }

      // Add card ID to seen list for random mode and review mode
      if ((currentStudyMode === 'random' || currentStudyMode === 'review') && data.question.id) {
        seenCardIds.push(data.question.id);
      }

      renderQuestion(data.question);
    });
  }

  function renderQuestion(q) {
    // Reset border feedback NGAY LẬP TỨC
    const flashcardContainer = document.getElementById('cardBox');
    if (flashcardContainer) {
      flashcardContainer.classList.remove('flashcard-correct', 'flashcard-incorrect');
      flashcardContainer.classList.remove('dictation-layout'); // giữ lại logic cũ
    }
    currentQuestion = q;
    questionStartTime = Date.now(); // Track when question was shown

    // Clear any existing timeout
    if (nextTimeout) {
      clearTimeout(nextTimeout);
      nextTimeout = null;
    }

    // Reset UI elements
    feedbackMsg.className = 'feedback-message';

    if (cardWordEl) { cardWordEl.innerHTML = ''; }
    if (cardPhoneticEl) { cardPhoneticEl.style.display = 'none'; }
    if (cardDefsEl) { cardDefsEl.className = 'card-definitions'; }

    // Hide grade buttons initially
    const gradeButtons = document.getElementById('gradeButtons');
    if (gradeButtons) {
      gradeButtons.className = 'grade-buttons';
      gradeButtons.classList.remove('hidden'); // Ensure no hidden class
    }

    // Hide audio button during question phase - it will be shown after answer submission
    if (audioButton) {
      audioButton.style.display = 'none';
    }

    // Remove any existing temporary audio containers
    const existingAudioContainer = document.getElementById('tempAudioContainer');
    if (existingAudioContainer) {
      existingAudioContainer.remove();
    }

    // Handle image display
    if (cardImageEl) {
      if (q.image_url) {
        cardImageEl.src = q.image_url;
        cardImageEl.style.display = 'block';
      } else {
        cardImageEl.style.display = 'none';
      }
    }

    // Clear previous options
    if (optionsArea) {
      optionsArea.innerHTML = '';
    }

    // Handle different question types
    if (q.type === 'mc') {
      // Multiple choice mode - show definitions in the main word area
      if (cardWordEl && q.definitions && q.definitions.length > 0) {
        let defsText = '';
        q.definitions.forEach(def => {
          if (def.english_definition) {
            defsText += `<div class="definition-item"><strong>${STUDY_CFG.labels.english_label}</strong> ${def.english_definition}</div>`;
          }
          if (def.vietnamese_definition) {
            defsText += `<div class="definition-item"><strong>${STUDY_CFG.labels.vietnamese_label}</strong> ${def.vietnamese_definition}</div>`;
          }
        });
        cardWordEl.innerHTML = defsText;
      }

      // Reset options area to grid mode for multiple choice
      if (optionsArea) {
        optionsArea.className = 'options-area';
      }

      // Hide phonetic initially
      if (cardPhoneticEl) {
        cardPhoneticEl.style.display = 'none';
      }

      // Hide definitions area for MC mode since we show them in word area
      if (cardDefsEl) {
        cardDefsEl.className = 'card-definitions';
      }

      q.options.forEach(option => {
        const btn = document.createElement('button');
        btn.textContent = option;
        btn.className = 'option-btn';
        btn.addEventListener('click', () => {
          const correct = option === q.word;
          submitAnswer(correct);
        });
        optionsArea.appendChild(btn);
      });
    } else if (q.type === 'dictation') {
      // Dictation mode - hide word, show instruction
      if (cardWordEl) {
        cardWordEl.innerHTML = `<strong>🎧 ${STUDY_CFG.labels.listen_and_type}</strong>`;
      }

      // Hide phonetic initially
      if (cardPhoneticEl) {
        cardPhoneticEl.style.display = 'none';
      }

      // Set dictation mode class for proper centering and layout
      if (optionsArea) {
        optionsArea.className = 'options-area dictation-mode';
      }

      // Add dictation layout class to flashcard container for proper spacing
      const flashcardContainer = document.getElementById('cardBox');
      if (flashcardContainer) {
        flashcardContainer.classList.add('dictation-layout');
      }

      // Auto-play audio once when dictation question loads
      if (q.audio_url) {
        setTimeout(() => {
          const audio = new Audio(q.audio_url);
          audio.play().catch(err => console.log('Auto-play failed:', err));
        }, 1000); // Delay 1 second to let user read the instruction
      }

      // Create dictation container with proper classes
      const dictationContainer = document.createElement('div');
      dictationContainer.className = 'dictation-container';

      // Add replay audio button for dictation mode
      if (q.audio_url) {
        const replayButton = document.createElement('button');
        replayButton.innerHTML = `<i class="fas fa-redo"></i> ${STUDY_CFG.labels.replay_audio}`;
        replayButton.className = 'replay-audio-btn';
        replayButton.addEventListener('click', () => {
          const audio = new Audio(q.audio_url);
          audio.play().catch(err => console.log('Audio replay failed:', err));
        });
        dictationContainer.appendChild(replayButton);
      }

      const inputRow = document.createElement('div');
      inputRow.className = 'dictation-input-row';

      const inp = document.createElement('input');
      inp.type = 'text';
      inp.placeholder = STUDY_CFG.labels.type_what_you_hear;
      inp.className = 'type-input';

      const btn = document.createElement('button');
      btn.textContent = STUDY_CFG.labels.check;
      btn.className = 'check-btn';

      btn.addEventListener('click', () => {
        if (!btn.disabled) {
          const correct = inp.value.trim().toLowerCase() === q.answer.toLowerCase();
          submitAnswer(correct);
        }
      });

      inp.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          if (!btn.disabled) btn.click();
        }
      });

      inputRow.appendChild(inp);
      inputRow.appendChild(btn);
      dictationContainer.appendChild(inputRow);
      optionsArea.appendChild(dictationContainer);
      setTimeout(() => inp.focus(), 100);
    } else {
      // Type answer mode - show definitions, hide word initially
      if (cardDefsEl && q.definitions && q.definitions.length > 0) {
        let defsText = '';
        q.definitions.forEach(def => {
          if (def.english_definition) {
            defsText += `${def.english_definition}\n`;
          }
          if (def.vietnamese_definition) {
            defsText += `${def.vietnamese_definition}\n`;
          }
          defsText += '\n';
        });
        cardDefsEl.textContent = defsText.trim();
        cardDefsEl.className = 'card-definitions show';
      }

      // Set options area to input mode for proper centering
      if (optionsArea) {
        optionsArea.className = 'options-area input-mode';
      }

      // Hide phonetic initially
      if (cardPhoneticEl) {
        cardPhoneticEl.style.display = 'none';
      }

      // Create horizontal input row container
      const inputRow = document.createElement('div');
      inputRow.className = 'input-row';

      const inp = document.createElement('input');
      inp.type = 'text';
      inp.placeholder = STUDY_CFG.labels.placeholder;
      inp.className = 'type-input';

      const btn = document.createElement('button');
      btn.textContent = STUDY_CFG.labels.check;
      btn.className = 'check-btn';

      btn.addEventListener('click', () => {
        if (!btn.disabled) {
          const correct = inp.value.trim().toLowerCase() === q.answer.toLowerCase();
          submitAnswer(correct);
        }
      });

      inp.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          if (!btn.disabled) btn.click();
        }
      });

      inputRow.appendChild(inp);
      inputRow.appendChild(btn);
      optionsArea.appendChild(inputRow);
      setTimeout(() => inp.focus(), 100);
    }

    // Show the answer section for user interaction
    if (answerArea) {
      answerArea.className = 'answer-section active';
    }

    // Hide definitions initially only for MC mode - input mode shows them before answering
    if (q.type === 'mc' && cardDefsEl) {
      cardDefsEl.className = 'card-definitions';
    }
  }

  function submitAnswer(correct) {
    // Store the actual correctness for later use in submitGrade
    window.currentAnswerCorrectness = correct;

    // Clear any existing timeout
    if (nextTimeout) {
      clearTimeout(nextTimeout);
      nextTimeout = null;
    }

    // Play audio feedback immediately
    if (correct) {
      AudioFeedback.playCorrect();
    } else {
      AudioFeedback.playIncorrect();
    }

    // Hide answer elements based on question type
    if (currentQuestion.type === 'mc') {
      // Multiple choice: hide all option buttons
      const optionButtons = optionsArea.querySelectorAll('.option-btn');
      optionButtons.forEach(btn => {
        btn.classList.add('hidden');
        btn.style.display = 'none';
      });
    } else if (currentQuestion.type === 'dictation') {
      // Dictation mode: hide replay button, input field, and check button
      const replayBtn = optionsArea.querySelector('.replay-audio-btn');
      const inputField = optionsArea.querySelector('.type-input');
      const checkBtn = optionsArea.querySelector('.check-btn');

      if (replayBtn) {
        replayBtn.classList.add('hidden');
        replayBtn.style.display = 'none';
      }
      if (inputField) {
        inputField.classList.add('hidden');
        inputField.style.display = 'none';
      }
      if (checkBtn) {
        checkBtn.classList.add('hidden');
        checkBtn.style.display = 'none';
      }
    } else {
      // Input mode: hide the entire input row (input field and check button)
      const inputRow = optionsArea.querySelector('.input-row');
      if (inputRow) {
        inputRow.classList.add('hidden');

        // Fallback: Force hide with inline styles if CSS doesn't work
        inputRow.style.display = 'none';
        inputRow.style.visibility = 'hidden';
        inputRow.style.opacity = '0';
        inputRow.style.height = '0';
        inputRow.style.overflow = 'hidden';
      }
    }

    // Update stats
    if (correct) {
      correctCnt++;
    } else {
      incorrectCnt++;
    }
    updateStats();

    // Remove feedbackMsg text
    if (feedbackMsg) {
      feedbackMsg.textContent = '';
      feedbackMsg.className = 'feedback-message';
    }
    // Border color feedback
    const flashcardContainer = document.getElementById('cardBox');
    if (flashcardContainer) {
      flashcardContainer.classList.remove('flashcard-correct', 'flashcard-incorrect');
      if (correct) {
        flashcardContainer.classList.add('flashcard-correct');
      } else {
        flashcardContainer.classList.add('flashcard-incorrect');
      }
    }

    // NOW reveal the correct answer and make word clickable for Cambridge Dictionary
    if (cardWordEl && currentQuestion.word) {
      const cambridgeUrl = `https://dictionary.cambridge.org/dictionary/english/${encodeURIComponent(currentQuestion.word)}`;
      cardWordEl.innerHTML = `<a href="${cambridgeUrl}" target="_blank" class="word-link"><strong>${currentQuestion.word}</strong></a>`;
      console.log('Clickable word created:', currentQuestion.word, 'URL:', cambridgeUrl);
    } else {
      console.log('Cannot create clickable word - cardWordEl:', !!cardWordEl, 'word:', currentQuestion.word);
    }

    // Show phonetic if available
    if (cardPhoneticEl && currentQuestion.phonetic) {
      cardPhoneticEl.textContent = `/${currentQuestion.phonetic}/`;
      cardPhoneticEl.style.display = 'block';
    }

    // Show definitions in the definitions area
    if (cardDefsEl && currentQuestion.definitions) {
      let defsText = '';
      currentQuestion.definitions.forEach(def => {
        if (def.english_definition) {
          defsText += `${def.english_definition}\n`;
        }
        if (def.vietnamese_definition) {
          defsText += `${def.vietnamese_definition}\n`;
        }
        defsText += '\n';
      });
      cardDefsEl.textContent = defsText.trim();
      cardDefsEl.className = 'card-definitions show';
    }



    // NOW show audio button after answer submission
    if (audioButton && currentQuestion.audio_url) {
      audioButton.style.display = 'block';
      audioButton.onclick = () => {
        const audio = new Audio(currentQuestion.audio_url);
        audio.play().catch(err => console.log('Audio play failed:', err));
      };
    }

    // Auto-play audio after revealing answer
    if (currentQuestion.audio_url) {
      setTimeout(() => {
        const audio = new Audio(currentQuestion.audio_url);
        audio.play().catch(err => console.log('Auto-play failed:', err));
      }, 500); // Delay 500ms to let user see the answer first
    }

    // Show grade buttons
    const gradeButtons = document.getElementById('gradeButtons');
    if (gradeButtons) {
      // Clear any inline styles and hidden classes
      gradeButtons.style.display = '';
      gradeButtons.classList.remove('hidden');
      gradeButtons.className = 'grade-buttons show';
    }

    // Handle grade button clicks
    const gradeBtns = document.querySelectorAll('.grade-btn');
    gradeBtns.forEach(btn => {
      btn.onclick = () => {
        const grade = parseInt(btn.dataset.grade);
        submitGrade(grade);
      };
    });
  }

  function submitGrade(grade) {
    // Calculate response time
    const responseTime = questionStartTime ? (Date.now() - questionStartTime) / 1000 : 0;

    // Use the actual answer correctness, not the grade
    const actualCorrectness = window.currentAnswerCorrectness !== undefined ? window.currentAnswerCorrectness : (grade >= 2);

    fetch(STUDY_CFG.submitUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': STUDY_CFG.csrfToken
      },
      body: JSON.stringify({
        card_id: currentQuestion.id,
        correct: actualCorrectness, // Use actual answer correctness, not grade-based
        response_time: responseTime,
        question_type: currentQuestion.type || 'multiple_choice',
        grade: grade // Also send the grade for spaced repetition algorithm
      })
    })
    .then(r => {
      if (!r.ok) {
        throw new Error(`HTTP ${r.status}: ${r.statusText}`);
      }
      return r.json();
    })
    .then(data => {
      if (data.success) {
        // Chuyển sang câu hỏi tiếp theo NGAY LẬP TỨC, không delay
        getNextQuestion();
      } else {
        console.error('Grade submission failed:', data.error || 'Unknown error');
        // Still proceed to next question to avoid getting stuck
        getNextQuestion();
      }
    })
    .catch(error => {
      console.error('Error submitting grade:', error);
      // Still proceed to next question to avoid getting stuck
      getNextQuestion();
    });
  }

  // Mode Slider Class
  class ModeSlider {
    constructor() {
      this.currentSlide = 0;
      this.totalSlides = modeSlides.length;
      this.isTransitioning = false;
      this.touchStartX = 0;
      this.touchEndX = 0;

      this.init();
    }

    init() {
      // Set initial state
      this.updateSlider();
      this.updateIndicators();
      this.updateNavButtons();

      // Add event listeners
      if (sliderPrev) {
        sliderPrev.addEventListener('click', () => this.prevSlide());
      }

      if (sliderNext) {
        sliderNext.addEventListener('click', () => this.nextSlide());
      }

      // Indicator clicks
      indicators.forEach((indicator, index) => {
        indicator.addEventListener('click', () => this.goToSlide(index));
      });

      // Touch/swipe support
      if (modeSlider) {
        modeSlider.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        modeSlider.addEventListener('touchend', (e) => this.handleTouchEnd(e));
        modeSlider.addEventListener('touchmove', (e) => e.preventDefault());
      }

      // Keyboard navigation
      document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') this.prevSlide();
        if (e.key === 'ArrowRight') this.nextSlide();
      });
    }

    updateSlider() {
      if (!modeSlider) return;

      const translateX = -this.currentSlide * 100;
      modeSlider.style.transform = `translateX(${translateX}%)`;

      // Update active slide
      modeSlides.forEach((slide, index) => {
        slide.classList.toggle('active', index === this.currentSlide);
      });

      // Trigger radio button change
      const activeSlide = modeSlides[this.currentSlide];
      if (activeSlide) {
        const radio = activeSlide.querySelector('input[type="radio"]');
        if (radio) {
          radio.checked = true;
          handleStudyModeChange();
        }
      }
    }

    updateIndicators() {
      indicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index === this.currentSlide);
      });
    }

    updateNavButtons() {
      if (sliderPrev) {
        sliderPrev.disabled = this.currentSlide === 0;
      }
      if (sliderNext) {
        sliderNext.disabled = this.currentSlide === this.totalSlides - 1;
      }
    }

    goToSlide(index) {
      if (this.isTransitioning || index === this.currentSlide) return;

      this.isTransitioning = true;
      this.currentSlide = Math.max(0, Math.min(index, this.totalSlides - 1));

      this.updateSlider();
      this.updateIndicators();
      this.updateNavButtons();

      setTimeout(() => {
        this.isTransitioning = false;
      }, 400);
    }

    nextSlide() {
      if (this.currentSlide < this.totalSlides - 1) {
        this.goToSlide(this.currentSlide + 1);
      }
    }

    prevSlide() {
      if (this.currentSlide > 0) {
        this.goToSlide(this.currentSlide - 1);
      }
    }

    handleTouchStart(e) {
      this.touchStartX = e.touches[0].clientX;
    }

    handleTouchEnd(e) {
      this.touchEndX = e.changedTouches[0].clientX;
      this.handleSwipe();
    }

    handleSwipe() {
      const swipeThreshold = 50;
      const diff = this.touchStartX - this.touchEndX;

      if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
          this.nextSlide();
        } else {
          this.prevSlide();
        }
      }
    }
  }

  // Initialize slider
  let modeSliderInstance;
  if (modeSlider) {
    modeSliderInstance = new ModeSlider();
  }

  // Study mode selection handling
  function handleStudyModeChange() {
    const selectedMode = document.querySelector('input[name="study_mode"]:checked').value;
    currentStudyMode = selectedMode;

    if (selectedMode === 'decks') {
      deckStudyOptions.classList.remove('hidden');
      randomStudyOptions.classList.add('hidden');
      if (reviewStudyOptions) reviewStudyOptions.classList.add('hidden');
    } else if (selectedMode === 'review') {
      deckStudyOptions.classList.add('hidden');
      randomStudyOptions.classList.add('hidden');
      if (reviewStudyOptions) reviewStudyOptions.classList.remove('hidden');
    } else {
      deckStudyOptions.classList.add('hidden');
      randomStudyOptions.classList.remove('hidden');
      if (reviewStudyOptions) reviewStudyOptions.classList.add('hidden');
    }
  }

  // Initialize study mode selection
  studyModeRadios.forEach(radio => {
    radio.addEventListener('change', handleStudyModeChange);
  });

  // Handle random word count input
  if (randomWordCountInput) {
    randomWordCountInput.addEventListener('input', (e) => {
      wordCount = parseInt(e.target.value) || 10;
    });
  }

  // Handle start buttons
  if (startBtnDecks) {
    startBtnDecks.addEventListener('click', () => {
      if (currentStudyMode === 'decks') {
        const selectedDeckIds = Array.from(document.querySelectorAll('input[name="deck_ids"]:checked')).map(cb => cb.value);
        if (selectedDeckIds.length === 0) {
          alert(STUDY_CFG.labels.select_deck_alert || 'Please select at least one deck to study.');
          return;
        }

        // Store selected deck IDs
        deckIds = selectedDeckIds;
      } else if (currentStudyMode === 'review') {
        // Check if there are incorrect words to review
        if (!reviewModeOption || reviewModeOption.classList.contains('disabled')) {
          alert('No incorrect words to review. Answer some questions incorrectly first!');
          return;
        }
      }

      // Reset session data
      correctCnt = 0;
      incorrectCnt = 0;
      seenCardIds = [];
      updateStats();
      
      // Hide all selection areas and show study area
      const studyModeSection = document.querySelector('.study-mode-section');
      if (studyModeSection) studyModeSection.style.display = 'none';
      if (deckStudyOptions) deckStudyOptions.classList.add('hidden');
      if (randomStudyOptions) randomStudyOptions.classList.add('hidden');
      if (reviewStudyOptions) reviewStudyOptions.classList.add('hidden');
      if (studyArea) {
        studyArea.style.display = 'block';
        studyArea.className = 'study-area active';
      }
      if (studyHeader) studyHeader.style.display = 'none';
      
      // Start studying
      getNextQuestion();
    });
  }

  if (startBtnRandom) {
    startBtnRandom.addEventListener('click', () => {
      // Reset session data
      correctCnt = 0;
      incorrectCnt = 0;
      seenCardIds = [];
      updateStats();

      // Hide all selection areas and show study area
      const studyModeSection = document.querySelector('.study-mode-section');
      if (studyModeSection) studyModeSection.style.display = 'none';
      if (deckStudyOptions) deckStudyOptions.classList.add('hidden');
      if (randomStudyOptions) randomStudyOptions.classList.add('hidden');
      if (reviewStudyOptions) reviewStudyOptions.classList.add('hidden');
      if (studyArea) {
        studyArea.style.display = 'block';
        studyArea.className = 'study-area active';
      }
      if (studyHeader) studyHeader.style.display = 'none';

      // Start studying
      getNextQuestion();
    });
  }

  if (startBtnReview) {
    startBtnReview.addEventListener('click', () => {
      // Check if there are incorrect words to review
      if (startBtnReview.disabled) {
        alert('No incorrect words to review. Answer some questions incorrectly first!');
        return;
      }

      // Reset session data
      correctCnt = 0;
      incorrectCnt = 0;
      seenCardIds = [];
      updateStats();

      // Hide all selection areas and show study area
      const studyModeSection = document.querySelector('.study-mode-section');
      if (studyModeSection) studyModeSection.style.display = 'none';
      if (deckStudyOptions) deckStudyOptions.classList.add('hidden');
      if (randomStudyOptions) randomStudyOptions.classList.add('hidden');
      if (reviewStudyOptions) reviewStudyOptions.classList.add('hidden');
      if (studyArea) {
        studyArea.style.display = 'block';
        studyArea.className = 'study-area active';
      }
      if (studyHeader) studyHeader.style.display = 'none';

      // Start studying
      getNextQuestion();
    });
  }

  // Back button handling
  if (backBtn) {
    backBtn.addEventListener('click', () => {
      // Hide study area
      studyArea.style.display = 'none';
      
      // Reset study area content
      if (cardWordEl) cardWordEl.innerHTML = '';
      if (cardPhoneticEl) cardPhoneticEl.style.display = 'none';
      if (cardImageEl) cardImageEl.style.display = 'none';
      if (cardDefsEl) cardDefsEl.innerHTML = '';
      if (optionsArea) optionsArea.innerHTML = '';
      if (feedbackMsg) feedbackMsg.style.display = 'none';

      const gradeButtons = document.getElementById('gradeButtons');
      if (gradeButtons) {
        gradeButtons.className = 'grade-buttons'; // Use class instead of inline style
        gradeButtons.style.display = ''; // Clear any inline styles
      }
      
      const noCardMsg = document.getElementById('noCardMsg');
      if (noCardMsg) noCardMsg.className = 'no-cards-message';
      
      // Show study mode selection again
      const studyModeSection = document.querySelector('.study-mode-section');
      if (studyModeSection) studyModeSection.style.display = 'block';
      
      // Show appropriate options based on current mode
      if (currentStudyMode === 'decks') {
        if (deckStudyOptions) deckStudyOptions.classList.remove('hidden');
        if (randomStudyOptions) randomStudyOptions.classList.add('hidden');
        if (reviewStudyOptions) reviewStudyOptions.classList.add('hidden');
      } else if (currentStudyMode === 'review') {
        if (deckStudyOptions) deckStudyOptions.classList.add('hidden');
        if (randomStudyOptions) randomStudyOptions.classList.add('hidden');
        if (reviewStudyOptions) reviewStudyOptions.classList.remove('hidden');
      } else {
        if (deckStudyOptions) deckStudyOptions.classList.add('hidden');
        if (randomStudyOptions) randomStudyOptions.classList.remove('hidden');
        if (reviewStudyOptions) reviewStudyOptions.classList.add('hidden');
      }
      
      // Reset stats
      correctCnt = 0;
      incorrectCnt = 0;
      updateStats();
      if (studyHeader) studyHeader.style.display = '';

      // Refresh incorrect words count when returning to study selection
      loadIncorrectWordsCount();
    });
  }

  // Initialize deck dropdown functionality
  const deckDropdownToggle = document.getElementById('deckDropdownToggle');
  const deckDropdown = document.getElementById('deckDropdown');
  const deckCheckboxes = document.querySelectorAll('input[name="deck_ids"]');

  function updateSelectedDecksText() {
    const selectedDecks = Array.from(deckCheckboxes).filter(cb => cb.checked);
    const selectedDecksText = document.getElementById('selectedDecksText');
    
    if (selectedDecks.length === 0) {
      selectedDecksText.textContent = STUDY_CFG.labels.no_decks_selected || 'No decks selected';
    } else if (selectedDecks.length === 1) {
      selectedDecksText.textContent = selectedDecks[0].nextElementSibling.textContent;
    } else {
      selectedDecksText.textContent = `${selectedDecks.length} decks selected`;
    }
  }

  if (deckDropdownToggle && deckDropdown) {
    deckDropdownToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      deckDropdown.classList.toggle('show');
      deckDropdownToggle.classList.toggle('active');
    });
  }

  deckCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', updateSelectedDecksText);
  });

  // Close dropdown if clicked outside
  document.addEventListener('click', (event) => {
    if (deckDropdown && !deckDropdown.contains(event.target) && !deckDropdownToggle.contains(event.target)) {
      deckDropdown.classList.remove('show');
      deckDropdownToggle.classList.remove('active');
    }
  });

  updateSelectedDecksText(); // Initial update

  // Function to end study session
  function endStudySession() {
    fetch('/api/study/end-session/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': STUDY_CFG.csrfToken
      }
    })
    .then(r => r.json())
    .then(data => {
      if (data.success && data.session_summary) {
        // Show session summary
        const summary = data.session_summary;
        console.log('Study session ended:', summary);
      }
    })
    .catch(err => console.error('Error ending session:', err));
  }

  // End session when user leaves the page
  window.addEventListener('beforeunload', endStudySession);

  // End session when user navigates away
  window.addEventListener('pagehide', endStudySession);

  // Load incorrect words count
  function loadIncorrectWordsCount() {
    // Check if required elements exist
    if (!reviewCountText || !reviewCount || !reviewModeOption) {
      console.log('Review mode elements not found, skipping incorrect words count loading');
      return;
    }

    fetch('/api/incorrect-words/count/', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(r => {
      console.log('API response status:', r.status);
      if (!r.ok) {
        throw new Error(`HTTP ${r.status}: ${r.statusText}`);
      }
      return r.json();
    })
    .then(data => {
      console.log('API response data:', data);
      if (data.success) {
        const totalCount = data.counts.total;
        const counts = data.counts;
        console.log('Total incorrect words count:', totalCount);

        if (totalCount > 0) {
          // Update main count display
          reviewCountText.textContent = `${totalCount} ${STUDY_CFG.labels.incorrect_words_count || 'incorrect words to review'}`;
          reviewCount.style.display = 'block';
          reviewModeOption.classList.remove('disabled');

          // Update detailed breakdown
          if (mcCount) mcCount.textContent = counts.mc || 0;
          if (typeCount) typeCount.textContent = counts.type || 0;
          if (dictationCount) dictationCount.textContent = counts.dictation || 0;

          // Show review details if any counts exist
          if (reviewDetails) reviewDetails.style.display = 'block';

          // Enable start review button
          if (startBtnReview) {
            startBtnReview.disabled = false;
            startBtnReview.classList.remove('disabled');
          }

          console.log('Review mode enabled with', totalCount, 'words');
        } else {
          reviewCount.style.display = 'none';
          reviewModeOption.classList.add('disabled');
          if (reviewDetails) reviewDetails.style.display = 'none';

          // Disable start review button
          if (startBtnReview) {
            startBtnReview.disabled = true;
            startBtnReview.classList.add('disabled');
          }

          console.log('Review mode disabled - no incorrect words found');
          // If review mode is selected but no words available, switch to decks mode
          if (currentStudyMode === 'review') {
            const decksRadio = document.querySelector('input[name="study_mode"][value="decks"]');
            if (decksRadio) {
              decksRadio.checked = true;
              handleStudyModeChange();
            }
          }
        }
      } else {
        console.error('API returned success: false', data);
      }
    })
    .catch(err => {
      console.error('Error loading incorrect words count:', err);
      // Disable review mode on error
      reviewCount.style.display = 'none';
      reviewModeOption.classList.add('disabled');
    });
  }

  // Initialize incorrect words count
  loadIncorrectWordsCount();

  // Initialize audio feedback system
  AudioFeedback.init();

  // Review Completion Modal Functions
  function showReviewCompletionModal() {
    const modal = document.getElementById('reviewCompletionModal');
    const continueBtn = document.getElementById('continueStudyingBtn');

    console.log('Showing review completion modal');

    if (modal) {
      modal.style.display = 'flex';

      // Handle continue button click
      if (continueBtn) {
        continueBtn.onclick = function() {
          console.log('Continue studying button clicked');
          hideReviewCompletionModal();
          returnToStudySelection();
        };
      }

      // Close modal when clicking outside
      modal.onclick = function(e) {
        if (e.target === modal) {
          console.log('Modal overlay clicked - closing');
          hideReviewCompletionModal();
          returnToStudySelection();
        }
      };
    }
  }

  function hideReviewCompletionModal() {
    const modal = document.getElementById('reviewCompletionModal');
    if (modal) {
      modal.style.display = 'none';
      console.log('Review completion modal hidden');
    }
  }

  function returnToStudySelection() {
    console.log('Returning to study selection after review completion');

    // Hide study area and show study selection
    if (studyArea) {
      studyArea.style.display = 'none';
      studyArea.className = 'study-area';
    }

    const studyModeSection = document.querySelector('.study-mode-section');
    if (studyModeSection) {
      studyModeSection.style.display = 'block';
    }

    // Show appropriate options based on current mode
    if (currentStudyMode === 'decks') {
      if (deckStudyOptions) deckStudyOptions.classList.remove('hidden');
      if (randomStudyOptions) randomStudyOptions.classList.add('hidden');
      if (reviewStudyOptions) reviewStudyOptions.classList.add('hidden');
    } else if (currentStudyMode === 'review') {
      if (deckStudyOptions) deckStudyOptions.classList.add('hidden');
      if (randomStudyOptions) randomStudyOptions.classList.add('hidden');
      if (reviewStudyOptions) reviewStudyOptions.classList.remove('hidden');
    } else {
      if (deckStudyOptions) deckStudyOptions.classList.add('hidden');
      if (randomStudyOptions) randomStudyOptions.classList.remove('hidden');
      if (reviewStudyOptions) reviewStudyOptions.classList.add('hidden');
    }

    // Reset stats
    correctCnt = 0;
    incorrectCnt = 0;
    updateStats();
    if (studyHeader) studyHeader.style.display = '';

    // Refresh incorrect words count to update the interface
    console.log('Refreshing incorrect words count after completion');
    loadIncorrectWordsCount();
  }

  // Make functions globally available
  window.showReviewCompletionModal = showReviewCompletionModal;
  window.hideReviewCompletionModal = hideReviewCompletionModal;
  window.returnToStudySelection = returnToStudySelection;

})();