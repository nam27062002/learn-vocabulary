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
  
  // New elements for study mode selection
  const studyModeRadios = document.querySelectorAll('input[name="study_mode"]');
  const randomStudyOptions = document.getElementById('randomStudyOptions');
  const randomWordCountInput = document.getElementById('randomWordCount');
  const totalWordsAvailableSpan = document.getElementById('totalWordsAvailable');
  const startBtnDecks = document.getElementById('startBtn');
  const startBtnRandom = document.getElementById('startRandomBtn');

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
        noCardMsg.className = 'no-cards-message show';
        studyArea.className = 'study-area';
        return;
      }
      
      // Add card ID to seen list for random mode
      if (currentStudyMode === 'random' && data.question.id) {
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

      // Reset options area to normal mode for input type
      if (optionsArea) {
        optionsArea.className = 'options-area';
      }

      // Hide phonetic initially
      if (cardPhoneticEl) {
        cardPhoneticEl.style.display = 'none';
      }

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

      optionsArea.appendChild(inp);
      optionsArea.appendChild(btn);
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
    // Clear any existing timeout
    if (nextTimeout) {
      clearTimeout(nextTimeout);
      nextTimeout = null;
    }

    // Disable all buttons
    const buttons = optionsArea.querySelectorAll('button, input');
    buttons.forEach(btn => btn.disabled = true);

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

    fetch(STUDY_CFG.submitUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': STUDY_CFG.csrfToken
      },
      body: JSON.stringify({
        card_id: currentQuestion.id,
        correct: grade >= 2, // Grade 2+ is considered correct
        response_time: responseTime,
        question_type: currentQuestion.type || 'multiple_choice'
      })
    })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        // Chuyển sang câu hỏi tiếp theo NGAY LẬP TỨC, không delay
        getNextQuestion();
      }
    });
  }

  // Study mode selection handling
  function handleStudyModeChange() {
    const selectedMode = document.querySelector('input[name="study_mode"]:checked').value;
    currentStudyMode = selectedMode;
    
    if (selectedMode === 'decks') {
      deckStudyOptions.classList.remove('hidden');
      randomStudyOptions.classList.add('hidden');
    } else {
      deckStudyOptions.classList.add('hidden');
      randomStudyOptions.classList.remove('hidden');
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
          alert('Please select at least one deck to study.');
          return;
        }

        // Store selected deck IDs
        deckIds = selectedDeckIds;
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
      if (gradeButtons) gradeButtons.style.display = 'none';
      
      const noCardMsg = document.getElementById('noCardMsg');
      if (noCardMsg) noCardMsg.className = 'no-cards-message';
      
      // Show study mode selection again
      const studyModeSection = document.querySelector('.study-mode-section');
      if (studyModeSection) studyModeSection.style.display = 'block';
      
      // Show appropriate options based on current mode
      if (currentStudyMode === 'decks') {
        if (deckStudyOptions) deckStudyOptions.classList.remove('hidden');
        if (randomStudyOptions) randomStudyOptions.classList.add('hidden');
      } else {
        if (deckStudyOptions) deckStudyOptions.classList.add('hidden');
        if (randomStudyOptions) randomStudyOptions.classList.remove('hidden');
      }
      
      // Reset stats
      correctCnt = 0;
      incorrectCnt = 0;
      updateStats();
      if (studyHeader) studyHeader.style.display = '';
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
      selectedDecksText.textContent = 'No decks selected';
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

})();