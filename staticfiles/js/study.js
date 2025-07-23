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
  const cambridgeLinkEl = document.getElementById('cambridgeLink');
  const cambridgeAnchorEl = document.getElementById('cambridgeAnchor');
  
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
        noCardMsg.style.display = 'block';
        studyArea.style.display = 'none';
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
    currentQuestion = q;

    // Clear any existing timeout
    if (nextTimeout) {
      clearTimeout(nextTimeout);
      nextTimeout = null;
    }

    // Reset UI elements
    feedbackMsg.style.display = 'none';
    if (cambridgeLinkEl) { cambridgeLinkEl.style.display = 'none'; }
    if (cardWordEl) { cardWordEl.innerHTML = ''; } // Đảm bảo làm sạch nội dung HTML trước khi thêm
    if (cardPhoneticEl) { cardPhoneticEl.style.display = 'none'; }

    // Handle image display
    if (cardImageEl) {
      if (q.image_url) {
        cardImageEl.src = q.image_url;
        cardImageEl.style.display = 'block';
      } else {
        cardImageEl.style.display = 'none';
      }
    }

    // Display word and phonetic
    if (cardWordEl) {
      cardWordEl.textContent = q.word;
    }
    
    if (cardPhoneticEl && q.phonetic) {
      cardPhoneticEl.textContent = `/${q.phonetic}/`;
      cardPhoneticEl.style.display = 'block';
    }

    // Clear previous options
    if (optionsArea) {
      optionsArea.innerHTML = '';
    }

    // Handle different question types
    if (q.type === 'mc') {
      // Multiple choice mode
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
      // Dictation mode
      const dictationBox = document.createElement('div');
      dictationBox.style.cssText = 'text-align:center;margin-top:15px;';
      
      const audioBtn = document.createElement('button');
      audioBtn.textContent = '🔊 Play Audio';
      audioBtn.style.cssText = 'background:#007bff;color:#fff;padding:10px 20px;border:none;border-radius:6px;margin-bottom:15px;cursor:pointer;font-weight:600;';
      audioBtn.addEventListener('click', () => {
        if (q.audio_url) {
          const audio = new Audio(q.audio_url);
          audio.play();
        }
      });
      dictationBox.appendChild(audioBtn);

      const inputRow = document.createElement('div');
      inputRow.style.cssText = 'display:flex;justify-content:center;align-items:center;gap:10px;';
      
      const inp = document.createElement('input');
      inp.type = 'text';
      inp.placeholder = 'Type what you hear...';
      inp.className = 'type-input';
      inp.style.cssText = 'padding:12px;border:2px solid #dee2e6;border-radius:8px;font-size:16px;width:200px;';
      
      const btn = document.createElement('button');
      btn.textContent = STUDY_CFG.labels.check;
      btn.className = 'check-btn';
      btn.style.cssText = 'background:#007bff;color:#fff;padding:12px 20px;border:none;border-radius:8px;cursor:pointer;font-weight:600;';
      
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
      dictationBox.appendChild(inputRow);
      optionsArea.appendChild(dictationBox);
      setTimeout(() => inp.focus(), 100);
    } else {
      // Type answer mode
      const inp = document.createElement('input');
      inp.type = 'text';
      inp.placeholder = STUDY_CFG.labels.placeholder;
      inp.className = 'type-input';
      inp.style.cssText = 'padding:12px;border:2px solid #dee2e6;border-radius:8px;font-size:16px;width:200px;margin-right:10px;';
      
      const btn = document.createElement('button');
      btn.textContent = STUDY_CFG.labels.check;
      btn.className = 'check-btn';
      btn.style.cssText = 'background:#007bff;color:#fff;padding:12px 20px;border:none;border-radius:8px;cursor:pointer;font-weight:600;';
      
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

    if (answerArea.style) { answerArea.style.display = 'block'; }
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

    // Show feedback
    if (feedbackMsg) {
      feedbackMsg.textContent = correct ? '✅ Correct!' : '❌ Incorrect';
      feedbackMsg.style.color = correct ? '#28a745' : '#dc3545';
      feedbackMsg.style.display = 'block';
    }

    // Show definitions and Cambridge link
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
    }

    // Show Cambridge link
    if (cambridgeLinkEl && cambridgeAnchorEl) {
      const cambridgeUrl = `https://dictionary.cambridge.org/dictionary/english/${encodeURIComponent(currentQuestion.word)}`;
      cambridgeAnchorEl.href = cambridgeUrl;
      cambridgeLinkEl.style.display = 'block';
    }

    // Show grade buttons
    const gradeButtons = document.getElementById('gradeButtons');
    if (gradeButtons) {
      gradeButtons.style.display = 'block';
    }

    // Handle grade button clicks
    const gradeBtns = document.querySelectorAll('.gradeBtn');
    gradeBtns.forEach(btn => {
      btn.onclick = () => {
        const grade = parseInt(btn.dataset.grade);
        submitGrade(grade);
      };
    });
  }

  function submitGrade(grade) {
    fetch(STUDY_CFG.submitUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': STUDY_CFG.csrfToken
      },
      body: JSON.stringify({
        card_id: currentQuestion.id,
        correct: grade >= 2 // Grade 2+ is considered correct
      })
    })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        // Move to next question after a short delay
        nextTimeout = setTimeout(() => {
          getNextQuestion();
        }, 1500);
      }
    });
  }

  // Study mode selection handling
  function handleStudyModeChange() {
    const selectedMode = document.querySelector('input[name="study_mode"]:checked').value;
    currentStudyMode = selectedMode;
    
    if (selectedMode === 'decks') {
      deckStudyOptions.style.display = 'block';
      randomStudyOptions.style.display = 'none';
    } else {
      deckStudyOptions.style.display = 'none';
      randomStudyOptions.style.display = 'block';
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
      }
      
      // Reset session data
      correctCnt = 0;
      incorrectCnt = 0;
      seenCardIds = [];
      updateStats();
      
      // Hide all selection areas and show study area
      document.querySelector('.mb-8.p-6.bg-white.dark\\:bg-gray-800.rounded-lg.shadow-md').style.display = 'none'; // Hide study mode selection
      deckStudyOptions.style.display = 'none';
      randomStudyOptions.style.display = 'none';
      studyArea.style.display = 'block';
      
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
      document.querySelector('.mb-8.p-6.bg-white.dark\\:bg-gray-800.rounded-lg.shadow-md').style.display = 'none'; // Hide study mode selection
      deckStudyOptions.style.display = 'none';
      randomStudyOptions.style.display = 'none';
      studyArea.style.display = 'block';
      
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
      if (cambridgeLinkEl) cambridgeLinkEl.style.display = 'none';
      
      const gradeButtons = document.getElementById('gradeButtons');
      if (gradeButtons) gradeButtons.style.display = 'none';
      
      const noCardMsg = document.getElementById('noCardMsg');
      if (noCardMsg) noCardMsg.style.display = 'none';
      
      // Show study mode selection again
      document.querySelector('.mb-8.p-6.bg-white.dark\\:bg-gray-800.rounded-lg.shadow-md').style.display = 'block';
      
      // Show appropriate options based on current mode
      if (currentStudyMode === 'decks') {
        deckStudyOptions.style.display = 'block';
        randomStudyOptions.style.display = 'none';
      } else {
        deckStudyOptions.style.display = 'none';
        randomStudyOptions.style.display = 'block';
      }
      
      // Reset stats
      correctCnt = 0;
      incorrectCnt = 0;
      updateStats();
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
      deckDropdown.classList.toggle('hidden');
      deckDropdownToggle.querySelector('i').classList.toggle('fa-chevron-down');
      deckDropdownToggle.querySelector('i').classList.toggle('fa-chevron-up');
    });
  }

  deckCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', updateSelectedDecksText);
  });

  // Close dropdown if clicked outside
  document.addEventListener('click', (event) => {
    if (deckDropdown && !deckDropdown.contains(event.target) && !deckDropdownToggle.contains(event.target)) {
      deckDropdown.classList.add('hidden');
      deckDropdownToggle.querySelector('i').classList.remove('fa-chevron-up');
      deckDropdownToggle.querySelector('i').classList.add('fa-chevron-down');
    }
  });

  updateSelectedDecksText(); // Initial update

})(); 