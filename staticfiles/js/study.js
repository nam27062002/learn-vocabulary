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
      selectedDecksText.textContent = STUDY_CFG.labels.no_decks_selected || STUDY_CFG.labels.no_decks_selected;
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
    } else if (q.type === 'dictation') {
      // Dictation mode: chỉ hiện nút nghe và ô nhập đáp án
      // Ẩn từ, nghĩa, phiên âm
      if (cardWordEl) cardWordEl.innerHTML = '';
      if (cardPhoneticEl) cardPhoneticEl.style.display = 'none';
      if (cardDefsEl) cardDefsEl.textContent = '';
      // Tạo container căn giữa cho loa và input
      const dictationBox = document.createElement('div');
      dictationBox.style.display = 'flex';
      dictationBox.style.flexDirection = 'column';
      dictationBox.style.alignItems = 'center';
      dictationBox.style.gap = '14px';
      dictationBox.style.margin = '18px 0 10px 0';
      // Nút nghe
      if (q.audio_url) {
        const replayAudioBtn = document.createElement('button');
        replayAudioBtn.className = 'replay-audio-btn fas fa-volume-up';
        replayAudioBtn.style.cssText = 'background:none;border:none;color:#007bff;font-size:2em;cursor:pointer;outline:none;';
        replayAudioBtn.addEventListener('click', () => {
          try {
            const audio = new Audio(q.audio_url);
            audio.play().catch(() => { });
          } catch (e) {
            console.log('Audio playback failed:', e);
          }
        });
        dictationBox.appendChild(replayAudioBtn);
      }
      // Ô nhập đáp án
      const inp = document.createElement('input');
      inp.type = 'text';
      inp.placeholder = STUDY_CFG.labels.answer_placeholder;
      inp.className = 'type-input';
      inp.style.cssText = 'padding:12px 16px;border:2px solid #dee2e6;border-radius:8px;font-size:18px;width:260px;max-width:100%;margin:0 auto;';
      const btn = document.createElement('button');
      btn.textContent = STUDY_CFG.labels.check;
      btn.className = 'check-btn';
      btn.style.cssText = 'background:#007bff;color:#fff;padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-weight:600;margin-left:10px;font-size:1em;';
      // Đặt input và button trên cùng một dòng
      const inputRow = document.createElement('div');
      inputRow.style.display = 'flex';
      inputRow.style.justifyContent = 'center';
      inputRow.style.alignItems = 'center';
      inputRow.style.gap = '10px';
      inputRow.appendChild(inp);
      inputRow.appendChild(btn);
      dictationBox.appendChild(inputRow);
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

    feedbackMsg.style.display = 'block';
    if (correct) {
      correctCnt++;
      feedbackMsg.textContent = STUDY_CFG.labels.correct;
      feedbackMsg.style.color = '#38c172';
    } else {
      incorrectCnt++;
      const label = STUDY_CFG.labels.answerLabel;
      feedbackMsg.textContent = `${STUDY_CFG.labels.incorrect} – ${label}: ${currentQuestion.word}`;
      feedbackMsg.style.color = '#e3342f';
    }
    updateStats();

    // Nếu là dictation, show nghĩa tiếng Việt sau khi trả lời
    if (currentQuestion && currentQuestion.type === 'dictation' && cardDefsEl && currentQuestion.definitions && currentQuestion.definitions.length > 0) {
      // Lấy nghĩa tiếng Việt đầu tiên (hoặc tất cả)
      const viDefs = currentQuestion.definitions.map(d => d.vietnamese_definition).filter(Boolean);
      if (viDefs.length > 0) {
        // Làm đẹp: tạo div nổi bật, có icon, dùng label dịch
        cardDefsEl.innerHTML = `<div style="background:#f3f4f6;border-radius:10px;padding:10px 18px;margin:12px auto 0 auto;display:flex;align-items:center;justify-content:center;max-width:90%;font-size:1.08em;box-shadow:0 2px 8px #0001;">
          <span style='font-size:1.2em;margin-right:8px;'>🇻🇳</span>
          <span style='font-weight:600;color:#4b5563;'>${STUDY_CFG.labels.vietnamese_meaning}:</span>
          <span style='margin-left:8px;color:#111827;'>${viDefs.join(' | ')}</span>
        </div>`;
      }
    }

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

      // Thêm từ loại nếu có
      if (currentQuestion.part_of_speech) {
        const partOfSpeechSpan = document.createElement('span');
        partOfSpeechSpan.textContent = ` (${getAbbreviatedPartOfSpeech(currentQuestion.part_of_speech)})`;
        partOfSpeechSpan.style.cssText = 'font-style: italic; font-size: 0.7em; color: gray; margin-left: 5px;'; // Đổi font-size nhỏ hơn
        cardWordEl.appendChild(partOfSpeechSpan);
      }

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
    if (selectedDecks.length === 0) { alert(STUDY_CFG.labels.select_at_least_one_deck); return; }
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