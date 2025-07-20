// study.js - handles study session with multiple modes

(function () {
  const deckSelect = document.getElementById('deckSelect');
  const startBtn = document.getElementById('startBtn');
  const deckSelectWrapper = document.getElementById('deckSelectWrapper');
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
  let correctCnt = 0, incorrectCnt = 0;
  let nextTimeout = null;

  function updateStats() {
    if (statsInfo) {
      statsInfo.textContent = `${STUDY_CFG.labels.correct}: ${correctCnt} | ${STUDY_CFG.labels.incorrect}: ${incorrectCnt}`;
    }
  }

  const modeSelect = null; // removed
  let currentQuestion = null;

  // New elements for custom deck select
  const deckDropdownToggle = document.getElementById('deckDropdownToggle');
  const deckDropdown = document.getElementById('deckDropdown');
  const selectedDecksText = document.getElementById('selectedDecksText');
  const deckCheckboxes = deckDropdown ? deckDropdown.querySelectorAll('input[type="checkbox"][name="deck_ids"]') : [];

  function updateSelectedDecksText() {
    const selectedOptions = Array.from(deckCheckboxes).filter(cb => cb.checked).map(cb => cb.nextElementSibling.textContent);
    if (selectedOptions.length > 0) {
      selectedDecksText.textContent = selectedOptions.join(', ');
    } else {
      selectedDecksText.textContent = STUDY_CFG.labels.no_decks_selected || 'Chưa chọn bộ thẻ nào';
    }
  }

  function qsToParams() {
    const params = new URLSearchParams();
    Array.from(deckCheckboxes).filter(cb => cb.checked).forEach(cb => params.append('deck_ids[]', cb.value));
    return params.toString();
  }

  function fetchNext() {
    fetch(`${STUDY_CFG.nextUrl}?${qsToParams()}`)
      .then(r => r.json())
      .then(data => {
        if (data.done) {
          noCardMsg.style.display = 'block';
          studyArea.style.display = 'none';
          return;
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
    if (cardWordEl) { cardWordEl.textContent = ''; }
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

    // Show definitions
    if (cardDefsEl) {
      cardDefsEl.textContent = q.definitions.map(d => `EN: ${d.english_definition}\nVI: ${d.vietnamese_definition}`).join('\n\n');
    }

    // Clear and rebuild options area
    optionsArea.innerHTML = '';

    if (q.type === 'mc') {
      // Multiple choice mode
      q.options.forEach(opt => {
        const btn = document.createElement('button');
        btn.textContent = opt;
        btn.className = 'option-btn';
        btn.style.cssText = 'background:#f8f9fa;border:2px solid #dee2e6;color:#495057;padding:12px 20px;margin:5px;border-radius:8px;cursor:pointer;font-weight:500;transition:all 0.2s;';
        btn.addEventListener('click', () => {
          if (!btn.disabled) submitAnswer(opt === q.word);
        });
        btn.addEventListener('mouseenter', () => {
          if (!btn.disabled) btn.style.background = '#e9ecef';
        });
        btn.addEventListener('mouseleave', () => {
          if (!btn.disabled) btn.style.background = '#f8f9fa';
        });
        optionsArea.appendChild(btn);
      });
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

      // Focus on input for better UX
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

    feedbackMsg.style.display = 'block';
    if (correct) {
      correctCnt++;
      feedbackMsg.textContent = STUDY_CFG.labels.correct;
      feedbackMsg.style.color = '#38c172';
    } else {
      incorrectCnt++;
      const label = STUDY_CFG.labels.answerLabel || 'Đáp án';
      feedbackMsg.textContent = `${STUDY_CFG.labels.incorrect} – ${label}: ${currentQuestion.word}`;
      feedbackMsg.style.color = '#e3342f';
    }
    updateStats();

    // Show word and phonetic after answer
    if (cardWordEl) {
      // Xóa nội dung hiện có để tránh trùng lặp
      cardWordEl.innerHTML = '';

      // Tạo thẻ <a> để bọc từ vựng và làm cho nó có thể nhấp
      const wordLink = document.createElement('a');
      wordLink.href = `https://dictionary.cambridge.org/dictionary/english/${currentQuestion.word}`;
      wordLink.target = "_blank"; // Mở trong tab mới
      wordLink.textContent = currentQuestion.word;
      wordLink.style.cssText = 'text-decoration: none; color: inherit; cursor: pointer;'; // Đảm bảo không có gạch chân và màu sắc phù hợp

      cardWordEl.appendChild(wordLink); // Thêm thẻ <a> vào cardWordEl

      // Append Replay Audio button if audio is available
      if (currentQuestion.audio_url) {
        const replayAudioBtn = document.createElement('button');
        replayAudioBtn.className = 'replay-audio-btn fas fa-volume-up'; // Font Awesome speaker icon
        replayAudioBtn.style.cssText = 'background:none;border:none;color:#007bff;font-size:0.6em;margin-left:10px;cursor:pointer;';
        replayAudioBtn.addEventListener('click', (e) => {
          e.stopPropagation(); // Ngăn chặn sự kiện click lan truyền lên thẻ <a>
          try {
            const audio = new Audio(currentQuestion.audio_url);
            audio.play().catch(() => { });
          } catch (e) {
            console.log('Audio playback failed:', e);
          }
        });
        cardWordEl.appendChild(replayAudioBtn); // Append to cardWordEl directly
      }
    }
    if (cardPhoneticEl && currentQuestion.phonetic) {
      cardPhoneticEl.textContent = currentQuestion.phonetic;
      cardPhoneticEl.style.display = 'block';
    }

    // Show Cambridge Dictionary link
    if (cambridgeLinkEl && cambridgeAnchorEl && currentQuestion.word) {
      cambridgeAnchorEl.href = `https://dictionary.cambridge.org/dictionary/english/${currentQuestion.word}`;
      cambridgeLinkEl.style.display = 'block';
    }

    // Disable all option buttons to prevent multiple clicks
    const optionBtns = optionsArea.querySelectorAll('.option-btn, .check-btn');
    optionBtns.forEach(btn => btn.disabled = true);

    // Add "Next Card" button for user control
    const nextBtn = document.createElement('button');
    nextBtn.textContent = STUDY_CFG.labels.nextCard;
    nextBtn.className = 'next-card-btn';
    nextBtn.style.cssText = 'background:#4dc0b5;color:#fff;padding:10px 20px;border:none;border-radius:6px;margin-top:15px;cursor:pointer;font-weight:600;';
    nextBtn.addEventListener('click', () => {
      fetchNext();
    });
    optionsArea.appendChild(nextBtn);

    // Play audio if available (but don't auto-advance)
    if (correct && currentQuestion.audio_url) {
      try {
        const audio = new Audio(currentQuestion.audio_url);
        audio.play().catch(() => { });
      } catch (e) {
        console.log('Audio playback failed:', e);
      }
    }

    // Submit the answer to backend
    fetch(STUDY_CFG.submitUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': STUDY_CFG.csrfToken },
      body: JSON.stringify({ card_id: currentQuestion.id, correct: correct })
    }).catch(err => {
      console.error('Failed to submit answer:', err);
    });
  }

  startBtn.addEventListener('click', () => {
    const selectedDecks = Array.from(deckCheckboxes).filter(cb => cb.checked);
    if (selectedDecks.length === 0) { alert('Vui lòng chọn ít nhất một bộ thẻ'); return; }
    deckSelectWrapper.style.display = 'none';
    correctCnt = 0; incorrectCnt = 0; updateStats();
    studyArea.style.display = 'block';
    if (cardPhoneticEl) { cardPhoneticEl.style.display = 'none'; }
    fetchNext();
  });

  backBtn.addEventListener('click', () => {
    deckSelectWrapper.style.display = 'block';
    studyArea.style.display = 'none';
  });

    // Event listeners for custom deck select
    if (deckDropdownToggle) {
      deckDropdownToggle.addEventListener('click', () => {
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