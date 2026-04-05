/**
 * dictation.js — YouTube-based dictation practice
 * Requires: window.DICTATION_DATA set by practice.html
 */

/* ── State ── */
const D = window.DICTATION_DATA;
let ytPlayer       = null;
let ytReady        = false;
let segments       = D.segments;
let activeSegIdx   = null;
let progress       = {};
let segmentTimer   = null;
let currentSpeed   = 1.0;
let videoVisible   = false;
let isPlaying      = false;

// Timeline state
let tlStart        = 0;
let tlEnd          = 0;
let tlRafId        = null;
let tlDragging     = false;

/* ── YouTube IFrame API ── */
window.onYouTubeIframeAPIReady = function () {
  ytPlayer = new YT.Player('ytPlayer', {
    videoId: D.videoId,
    playerVars: {
      autoplay: 0,
      cc_load_policy: 0,
      iv_load_policy: 3,
      rel: 0,
      modestbranding: 1,
      controls: 1,
    },
    events: {
      onReady: () => { ytReady = true; },
      onStateChange: (e) => {
        if (e.data === YT.PlayerState.PLAYING) {
          setPlaying(true);
        } else if (e.data === YT.PlayerState.PAUSED || e.data === YT.PlayerState.ENDED) {
          setPlaying(false);
        }
      },
    },
  });
};

function setPlaying(val) {
  isPlaying = val;
  const wave = document.getElementById('audioWave');
  if (wave) wave.classList.toggle('playing', val);
  const status = document.getElementById('audioStatus');
  if (status && activeSegIdx !== null) {
    status.textContent = val ? 'Playing…' : 'Paused';
  }
}

function playSegment(start, end) {
  if (!ytReady) return;
  clearInterval(segmentTimer);
  ytPlayer.setPlaybackRate(currentSpeed);
  ytPlayer.seekTo(start, true);
  ytPlayer.playVideo();

  segmentTimer = setInterval(() => {
    if (!ytPlayer) return;
    const cur = ytPlayer.getCurrentTime();
    if (cur >= end) {
      ytPlayer.pauseVideo();
      clearInterval(segmentTimer);
    }
  }, 150);
}

/* ── localStorage helpers ── */
const LS_DRAFT   = (segId) => `d_draft_${D.videoId}_${segId}`;
const LS_RESULT  = (segId) => `d_result_${D.videoId}_${segId}`;

function saveDraft(segId, text) {
  if (text) localStorage.setItem(LS_DRAFT(segId), text);
  else      localStorage.removeItem(LS_DRAFT(segId));
}
function loadDraft(segId)  { return localStorage.getItem(LS_DRAFT(segId)) || ''; }
function clearDraft(segId) { localStorage.removeItem(LS_DRAFT(segId)); }

function saveResult(segId, resultObj, userInput) {
  localStorage.setItem(LS_RESULT(segId), JSON.stringify({result: resultObj, input: userInput}));
}
function loadResult(segId) {
  try { return JSON.parse(localStorage.getItem(LS_RESULT(segId))); } catch { return null; }
}

/* ── DOM refs ── */
const segmentListEl  = document.getElementById('segmentList');
const segmentHeading = document.getElementById('segmentHeading');
const segTitle       = document.getElementById('segTitle');
const segTime        = document.getElementById('segTime');
const segDuration    = document.getElementById('segDuration');
const playControls   = document.getElementById('playControls');
const inputArea      = document.getElementById('inputArea');
const resultArea     = document.getElementById('resultArea');
const dictationInput = document.getElementById('dictationInput');
const scoreRow       = document.getElementById('scoreRow');
const tokenDisplay   = document.getElementById('tokenDisplay');
const btnPlay        = document.getElementById('btnPlay');
const btnReplay      = document.getElementById('btnReplay');
const btnCheck       = document.getElementById('btnCheck');
const btnReveal      = document.getElementById('btnReveal');
const btnNext        = document.getElementById('btnNext');
const btnRetry       = document.getElementById('btnRetry');
const answerReveal     = document.getElementById('answerReveal');
const answerText       = document.getElementById('answerText');
const progressBar      = document.getElementById('progressBar');
const progressLabel    = document.getElementById('progressLabel');
const avgScoreEl       = document.getElementById('avgScore');
const audioStatus      = document.getElementById('audioStatus');
const prevAttemptWrap  = document.getElementById('prevAttemptWrap');
const btnTogglePrev    = document.getElementById('btnTogglePrev');
const prevAttemptBody  = document.getElementById('prevAttemptBody');
const prevAttemptLabel = document.getElementById('prevAttemptLabel');
const prevChevron      = document.getElementById('prevChevron');
const prevScoreRow     = document.getElementById('prevScoreRow');
const prevTokenDisplay = document.getElementById('prevTokenDisplay');
const draftBadge       = document.getElementById('draftBadge');

// Toggle previous attempt panel
btnTogglePrev.addEventListener('click', () => {
  const open = !prevAttemptBody.classList.contains('hidden');
  prevAttemptBody.classList.toggle('hidden', open);
  prevChevron.style.transform = open ? '' : 'rotate(180deg)';
});

// Auto-save draft while typing (debounced 600ms)
let draftTimer = null;
dictationInput.addEventListener('input', () => {
  if (activeSegIdx === null) return;
  const segId = segments[activeSegIdx].id;
  clearTimeout(draftTimer);
  draftTimer = setTimeout(() => saveDraft(segId, dictationInput.value), 600);
});

/* ── Speed control ── */
const speedSlider  = document.getElementById('speedSlider');
const speedDisplay = document.getElementById('speedDisplay');
const speedPresets = document.querySelectorAll('.speed-preset');

function setSpeed(val) {
  currentSpeed = parseFloat(val);
  speedSlider.value = currentSpeed;
  speedDisplay.textContent = currentSpeed % 1 === 0
    ? currentSpeed + '×'
    : currentSpeed.toFixed(2).replace(/0+$/, '') + '×';

  // Sync preset active state
  speedPresets.forEach(btn => {
    btn.classList.toggle('active', parseFloat(btn.dataset.speed) === currentSpeed);
  });

  // Apply to live player if playing
  if (ytReady && ytPlayer) {
    try { ytPlayer.setPlaybackRate(currentSpeed); } catch (_) {}
  }
}

speedSlider.addEventListener('input', () => setSpeed(speedSlider.value));

speedPresets.forEach(btn => {
  btn.addEventListener('click', () => setSpeed(btn.dataset.speed));
});

/* ── Video toggle ── */
const btnToggleVideo  = document.getElementById('btnToggleVideo');
const playerWrap      = document.getElementById('playerWrap');
const audioPlaceholder = document.getElementById('audioPlaceholder');
const lblToggle       = document.getElementById('lblToggleVideo');

function setVideoVisible(visible) {
  videoVisible = visible;
  playerWrap.classList.toggle('hidden', !visible);
  audioPlaceholder.classList.toggle('hidden', visible);
  btnToggleVideo.classList.toggle('active', visible);
  lblToggle.textContent = visible ? 'Hide video' : 'Show video';
}

btnToggleVideo.addEventListener('click', () => setVideoVisible(!videoVisible));

/* ── Segment list ── */
function buildSegmentList() {
  segmentListEl.innerHTML = '';
  segments.forEach((seg, idx) => {
    const item = document.createElement('div');
    item.className = 'segment-item';
    item.dataset.idx = idx;

    const num = document.createElement('span');
    num.className = 'segment-num';
    num.textContent = seg.order;

    const time = document.createElement('span');
    time.className = 'segment-time';
    time.textContent = formatTime(seg.start_time);

    const badge = document.createElement('span');
    badge.className = 'segment-badge';
    badge.id = `badge-${seg.id}`;
    applyBadge(badge, progress[seg.id]);

    item.append(num, time, badge);
    item.addEventListener('click', () => activateSegment(idx));
    segmentListEl.appendChild(item);
  });
}

function applyBadge(badge, prog) {
  if (!prog) {
    badge.textContent = '–';
    badge.className = 'segment-badge badge-pending';
  } else if (prog.revealed) {
    badge.textContent = '👁';
    badge.className = 'segment-badge badge-revealed';
  } else if (prog.score >= 0.8) {
    badge.textContent = Math.round(prog.score * 100) + '%';
    badge.className = 'segment-badge badge-correct';
  } else {
    badge.textContent = Math.round(prog.score * 100) + '%';
    badge.className = 'segment-badge badge-partial';
  }
}

function refreshBadge(segId, prog) {
  progress[segId] = prog;
  const badge = document.getElementById(`badge-${segId}`);
  if (badge) applyBadge(badge, prog);
  updateOverallProgress();
}

/* ── Activate segment ── */
function activateSegment(idx) {
  activeSegIdx = idx;
  const seg = segments[idx];

  // Sidebar active
  document.querySelectorAll('.segment-item').forEach((el, i) => {
    el.classList.toggle('active', i === idx);
  });

  // Heading
  segmentHeading.classList.remove('hidden');
  segTitle.textContent = `Segment ${seg.order}`;
  segTime.textContent = `${formatTime(seg.start_time)} – ${formatTime(seg.end_time)}`;
  const dur = (seg.end_time - seg.start_time).toFixed(1);
  segDuration.textContent = `${dur}s`;

  // Show controls
  playControls.style.display = 'flex';
  inputArea.style.display = 'block';
  resultArea.style.display = 'none';
  answerReveal.style.display = 'none';
  btnNext.style.display = 'none';
  btnRetry.style.display = 'none';

  // ── Restore draft or last attempt ──
  const draft   = loadDraft(seg.id);
  const savedResult = loadResult(seg.id);

  // Show previous attempt panel if there's a saved result
  if (savedResult) {
    prevAttemptWrap.classList.remove('hidden');
    const pct = Math.round(savedResult.result.score * 100);
    prevScoreRow.innerHTML = scoreBadgeHTML(savedResult.result);
    renderTokensInto(savedResult.result.tokens, prevTokenDisplay);
    prevAttemptLabel.textContent = `Last attempt · ${pct}%`;
    // Keep body collapsed by default
    prevAttemptBody.classList.add('hidden');
    prevChevron.style.transform = '';
  } else {
    prevAttemptWrap.classList.add('hidden');
  }

  // Restore draft (takes priority for textarea) or fall back to last attempt's input
  if (draft) {
    dictationInput.value = draft;
    draftBadge.classList.remove('hidden');
  } else if (savedResult) {
    dictationInput.value = savedResult.input || '';
    draftBadge.classList.add('hidden');
  } else {
    dictationInput.value = '';
    draftBadge.classList.add('hidden');
  }

  // Update audio status
  if (audioStatus) audioStatus.textContent = `Segment ${seg.order} — ready`;

  // Init timeline for this segment
  initTimeline(seg.start_time, seg.end_time);

  // Auto-play
  if (ytReady) playSegment(seg.start_time, seg.end_time);

  dictationInput.focus();
}

/* ── Play / Replay ── */
btnPlay.addEventListener('click', () => {
  if (activeSegIdx === null) return;
  const seg = segments[activeSegIdx];
  playSegment(seg.start_time, seg.end_time);
});

btnReplay.addEventListener('click', () => {
  if (activeSegIdx === null) return;
  const seg = segments[activeSegIdx];
  playSegment(seg.start_time, seg.end_time);
});

/* ── Check answer ── */
btnCheck.addEventListener('click', checkAnswer);

async function checkAnswer() {
  if (activeSegIdx === null) return;
  const seg = segments[activeSegIdx];
  const input = dictationInput.value.trim();
  if (!input) { dictationInput.focus(); return; }

  btnCheck.disabled = true;
  const orig = btnCheck.innerHTML;
  btnCheck.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Checking…';

  try {
    const resp = await fetch(D.checkUrl, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': D.csrfToken},
      body: JSON.stringify({segment_id: seg.id, user_input: input}),
    });
    const result = await resp.json();

    await fetch(D.saveUrl, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': D.csrfToken},
      body: JSON.stringify({segment_id: seg.id, user_input: input, score: result.score, revealed_answer: false}),
    });

    renderResult(result);
    saveResult(seg.id, result, input);
    clearDraft(seg.id);
    draftBadge.classList.add('hidden');
    refreshBadge(seg.id, {score: result.score, revealed: false});

    if (activeSegIdx < segments.length - 1) btnNext.style.display = 'inline-flex';
    btnRetry.style.display = 'inline-flex';

  } finally {
    btnCheck.disabled = false;
    btnCheck.innerHTML = orig;
  }
}

/* ── Show answer ── */
btnReveal.addEventListener('click', async () => {
  if (activeSegIdx === null) return;
  const seg = segments[activeSegIdx];

  const resp = await fetch(D.checkUrl, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': D.csrfToken},
    body: JSON.stringify({segment_id: seg.id, user_input: ''}),
  });
  const result = await resp.json();
  answerText.textContent = result.transcript || '';
  answerReveal.style.display = 'block';

  await fetch(D.saveUrl, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': D.csrfToken},
    body: JSON.stringify({segment_id: seg.id, user_input: dictationInput.value, score: 0, revealed_answer: true}),
  });

  clearDraft(seg.id);
  draftBadge.classList.add('hidden');
  refreshBadge(seg.id, {score: 0, revealed: true});
});

/* ── Retry ── */
btnRetry.addEventListener('click', () => {
  resultArea.style.display = 'none';
  answerReveal.style.display = 'none';
  btnNext.style.display = 'none';
  btnRetry.style.display = 'none';
  dictationInput.value = '';
  dictationInput.focus();
  if (activeSegIdx !== null) {
    const seg = segments[activeSegIdx];
    if (ytReady) playSegment(seg.start_time, seg.end_time);
  }
});

/* ── Next segment ── */
btnNext.addEventListener('click', goNext);
function goNext() {
  if (activeSegIdx < segments.length - 1) {
    activateSegment(activeSegIdx + 1);
    scrollActiveSegment();
  }
}

function scrollActiveSegment() {
  const items = segmentListEl.querySelectorAll('.segment-item');
  const active = items[activeSegIdx];
  if (active) active.scrollIntoView({block: 'nearest', behavior: 'smooth'});
}

/* ── Shared token renderer ── */
function renderTokensInto(tokens, container) {
  container.innerHTML = '';
  tokens.forEach(tok => {
    const span = document.createElement('span');
    span.className = `token ${tok.status}`;
    if (tok.status === 'correct') {
      span.textContent = tok.word;
      span.appendChild(addWordButton(tok.word));
    } else if (tok.status === 'proper') {
      const typed = tok.user_word || tok.word;
      const same = typed.toLowerCase() === tok.word.toLowerCase();
      span.innerHTML = escHtml(typed) +
        (same ? '' : `<span class="proper-hint">${escHtml(tok.word)}</span>`);
      span.title = 'Proper noun — accepted';
      span.appendChild(addWordButton(tok.word));
    } else if (tok.status === 'wrong') {
      span.innerHTML = `<span style="text-decoration:line-through">${escHtml(tok.user_word)}</span><span class="correct-hint">${escHtml(tok.word)}</span>`;
      span.appendChild(addWordButton(tok.word));
    } else if (tok.status === 'missing') {
      span.textContent = `[${tok.word}]`;
      span.title = 'Missing';
      span.appendChild(addWordButton(tok.word));
    } else {
      span.textContent = tok.word;
      span.title = 'Extra';
    }
    container.appendChild(span);
    container.appendChild(document.createTextNode(' '));
  });
}

function scoreBadgeHTML(result) {
  const pct = Math.round(result.score * 100);
  const cls = pct >= 80 ? 'high' : pct >= 50 ? 'medium' : 'low';
  const emoji = pct >= 80 ? '🎉' : pct >= 50 ? '👍' : '🔄';
  const properNote = (result.proper_count > 0)
    ? ` <span class="text-xs text-purple-500 ml-1">(${result.proper_count} proper noun${result.proper_count > 1 ? 's' : ''} accepted)</span>` : '';
  return `<span class="score-badge ${cls}">${emoji} ${pct}%</span>
          <span class="text-sm text-gray-500">${result.correct_count} / ${result.total_count} words${properNote}</span>`;
}

/* ── Render result ── */
function renderResult(result) {
  resultArea.style.display = 'block';
  scoreRow.innerHTML = scoreBadgeHTML(result);
  renderTokensInto(result.tokens, tokenDisplay);
}

/* ── Progress ── */
function updateOverallProgress() {
  const attempted = Object.keys(progress).length;
  const total = segments.length;
  progressBar.style.width = (total ? Math.round(attempted / total * 100) : 0) + '%';
  progressLabel.textContent = `${attempted} / ${total}`;

  const scores = Object.values(progress).filter(p => !p.revealed).map(p => p.score);
  if (scores.length) {
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
    avgScoreEl.textContent = `Avg ${Math.round(avg * 100)}%`;
  } else {
    avgScoreEl.textContent = '';
  }
}

async function loadProgress() {
  try {
    const resp = await fetch(D.progressUrl);
    if (resp.ok) progress = (await resp.json()).progress || {};
  } catch (_) {}
}

/* ── Keyboard shortcuts ── */
document.addEventListener('keydown', e => {
  // Ctrl+Enter → check
  if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); checkAnswer(); return; }
  // Ctrl+Space → play
  if (e.ctrlKey && !e.shiftKey && e.key === ' ') { e.preventDefault(); btnPlay.click(); return; }
  // Tab (when input focused) → next segment
  if (e.key === 'Tab' && document.activeElement === dictationInput) {
    e.preventDefault(); goNext();
  }
});

/* ── Timeline scrubber ── */
const timelineWrap  = document.getElementById('timelineWrap');
const timelineTrack = document.getElementById('timelineTrack');
const timelineFill  = document.getElementById('timelineFill');
const timelineThumb = document.getElementById('timelineThumb');
const tlCurrentEl   = document.getElementById('tlCurrent');
const tlTotalEl     = document.getElementById('tlTotal');

function initTimeline(start, end) {
  tlStart = start;
  tlEnd   = end;
  const dur = end - start;
  tlTotalEl.textContent = dur.toFixed(1) + 's';
  tlCurrentEl.textContent = '0.0s';
  setTimelinePos(0);
  timelineWrap.classList.remove('hidden');
  cancelAnimationFrame(tlRafId);
  tlRafId = requestAnimationFrame(tickTimeline);
}

function tickTimeline() {
  if (ytReady && ytPlayer && !tlDragging) {
    const cur = ytPlayer.getCurrentTime();
    const pos = Math.min(Math.max(cur - tlStart, 0), tlEnd - tlStart);
    setTimelinePos(pos / (tlEnd - tlStart));
    tlCurrentEl.textContent = pos.toFixed(1) + 's';
  }
  tlRafId = requestAnimationFrame(tickTimeline);
}

function setTimelinePos(ratio /* 0–1 */) {
  const pct = Math.min(Math.max(ratio * 100, 0), 100);
  timelineFill.style.width  = pct + '%';
  timelineThumb.style.left  = pct + '%';
}

function seekFromEvent(e) {
  const rect  = timelineTrack.getBoundingClientRect();
  const ratio = Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1);
  const target = tlStart + ratio * (tlEnd - tlStart);
  if (ytReady) {
    // Clear auto-stop timer so it resets after seeking
    clearInterval(segmentTimer);
    ytPlayer.seekTo(target, true);
    // Resume auto-stop from new position
    segmentTimer = setInterval(() => {
      if (!ytPlayer) return;
      const cur = ytPlayer.getCurrentTime();
      if (cur >= tlEnd) {
        ytPlayer.pauseVideo();
        clearInterval(segmentTimer);
      }
    }, 150);
    setTimelinePos(ratio);
    tlCurrentEl.textContent = (ratio * (tlEnd - tlStart)).toFixed(1) + 's';
  }
}

// Mouse events — click & drag
timelineTrack.addEventListener('mousedown', e => {
  tlDragging = true;
  timelineTrack.classList.add('dragging');
  seekFromEvent(e);

  const onMove = ev => { if (tlDragging) seekFromEvent(ev); };
  const onUp   = () => {
    tlDragging = false;
    timelineTrack.classList.remove('dragging');
    window.removeEventListener('mousemove', onMove);
    window.removeEventListener('mouseup',   onUp);
  };
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup',   onUp);
});

// Touch events — mobile scrubbing
timelineTrack.addEventListener('touchstart', e => {
  tlDragging = true;
  timelineTrack.classList.add('dragging');
  seekFromEvent(e.touches[0]);

  const onMove = ev => { if (tlDragging) seekFromEvent(ev.touches[0]); };
  const onEnd  = () => {
    tlDragging = false;
    timelineTrack.classList.remove('dragging');
    timelineTrack.removeEventListener('touchmove', onMove);
    timelineTrack.removeEventListener('touchend',  onEnd);
  };
  timelineTrack.addEventListener('touchmove', onMove, {passive: true});
  timelineTrack.addEventListener('touchend',  onEnd);
}, {passive: true});

/* ── Helpers ── */
function formatTime(s) {
  const m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
}
function escHtml(str) {
  return (str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/* ══════════════════════════════════════════════
   Add-to-Flashcard modal
   ══════════════════════════════════════════════ */
const fcModal      = document.getElementById('fcModal');
const fcModalClose = document.getElementById('fcModalClose');
const fcCancelBtn  = document.getElementById('fcCancelBtn');
const fcSaveBtn    = document.getElementById('fcSaveBtn');
const fcWord       = document.getElementById('fcWord');
const fcPhonetic   = document.getElementById('fcPhonetic');
const fcPos        = document.getElementById('fcPos');
const fcLoading    = document.getElementById('fcLoading');
const fcFields     = document.getElementById('fcFields');
const fcEnDef      = document.getElementById('fcEnDef');
const fcViDef      = document.getElementById('fcViDef');
const fcDeckSelect = document.getElementById('fcDeckSelect');
const fcExistsNote = document.getElementById('fcExistsNote');
const fcSaveStatus = document.getElementById('fcSaveStatus');

let fcCurrentWord  = '';
let fcCurrentAudio = '';
let fcCurrentPos   = '';
let decksCache     = null;

// Open modal for a word
async function openAddWord(word) {
  fcCurrentWord  = word.toLowerCase().trim();
  fcCurrentAudio = '';
  fcCurrentPos   = '';

  // Reset UI
  fcWord.textContent     = fcCurrentWord;
  fcPhonetic.textContent = '';
  fcPos.textContent      = '';
  fcEnDef.value          = '';
  fcViDef.value          = '';
  fcSaveStatus.textContent = '';
  fcExistsNote.classList.add('hidden');
  fcLoading.classList.remove('hidden');
  fcFields.classList.add('hidden');
  fcSaveBtn.disabled = true;
  fcModal.classList.remove('hidden');

  // Parallel: fetch word details + check existence + load decks
  const [details, viResp, exists, decks] = await Promise.all([
    fetchWordDetails(fcCurrentWord),
    fetchViTranslation(fcCurrentWord),
    checkWordExists(fcCurrentWord),
    loadDecks(),
  ]);

  fcLoading.classList.add('hidden');
  fcFields.classList.remove('hidden');

  // Populate word details
  if (details && !details.error) {
    const ph = details.phonetics?.find(p => p.text) || {};
    fcPhonetic.textContent = ph.text || '';
    fcCurrentAudio = details.phonetics?.find(p => p.audio)?.audio || '';

    const meaning = details.meanings?.[0] || {};
    fcCurrentPos = meaning.part_of_speech || '';
    fcPos.textContent = fcCurrentPos;
    fcPos.style.display = fcCurrentPos ? '' : 'none';

    const defObj = meaning.definitions?.[0] || {};
    fcEnDef.value = defObj.en || '';
  }

  // Vietnamese translation from separate endpoint
  if (viResp && !viResp.error) {
    fcViDef.value = viResp.translated_text || '';
  }

  // Populate decks — first entry = most recently created (auto-selected)
  fcDeckSelect.innerHTML = '';
  if (decks.length === 0) {
    fcDeckSelect.innerHTML = '<option value="">No decks — create one first</option>';
  } else {
    decks.forEach((d, i) => {
      const opt = document.createElement('option');
      opt.value = d.id;
      opt.textContent = d.name;
      if (i === 0) opt.selected = true;   // newest deck pre-selected
      fcDeckSelect.appendChild(opt);
    });
    fcSaveBtn.disabled = false;
  }

  // Word already exists notice
  if (exists) {
    fcExistsNote.classList.remove('hidden');
  }
}

function closeFcModal() {
  fcModal.classList.add('hidden');
}
fcModalClose.addEventListener('click', closeFcModal);
fcCancelBtn.addEventListener('click', closeFcModal);
fcModal.addEventListener('click', e => { if (e.target === fcModal) closeFcModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeFcModal(); });

// Save flashcard
fcSaveBtn.addEventListener('click', async () => {
  const deckId = fcDeckSelect.value;
  if (!deckId || !fcCurrentWord) return;

  fcSaveBtn.disabled = true;
  fcSaveStatus.textContent = 'Saving…';

  const form = new FormData();
  form.append('deck_id', deckId);
  form.append('flashcards-0-word', fcCurrentWord);
  form.append('flashcards-0-phonetic', fcPhonetic.textContent || '');
  form.append('flashcards-0-part_of_speech', fcCurrentPos || '');
  form.append('flashcards-0-english_definition', fcEnDef.value.trim());
  form.append('flashcards-0-vietnamese_definition', fcViDef.value.trim());
  form.append('flashcards-0-audio_url', fcCurrentAudio || '');

  try {
    const resp = await fetch(D.saveFlashcardUrl, {
      method: 'POST',
      headers: {'X-CSRFToken': D.csrfToken},
      body: form,
    });
    const data = await resp.json();
    if (data.success) {
      fcSaveStatus.innerHTML = '<span class="text-green-600 font-semibold">✓ Saved!</span>';
      // Mark any matching token-add-btn as added
      document.querySelectorAll(`.token-add-btn[data-word="${CSS.escape(fcCurrentWord)}"]`).forEach(btn => {
        btn.textContent = '✓';
        btn.classList.add('added');
      });
      setTimeout(closeFcModal, 900);
    } else {
      fcSaveStatus.innerHTML = `<span class="text-red-500">${escHtml(data.error || 'Error')}</span>`;
      fcSaveBtn.disabled = false;
    }
  } catch (e) {
    fcSaveStatus.innerHTML = '<span class="text-red-500">Network error</span>';
    fcSaveBtn.disabled = false;
  }
});

// API helpers
async function fetchWordDetails(word) {
  try {
    const resp = await fetch(`${D.wordDetailsUrl}?word=${encodeURIComponent(word)}`);
    return resp.ok ? resp.json() : null;
  } catch { return null; }
}

async function fetchViTranslation(word) {
  try {
    const resp = await fetch(`/api/translate-to-vietnamese/?text=${encodeURIComponent(word)}`);
    return resp.ok ? resp.json() : null;
  } catch { return null; }
}

async function checkWordExists(word) {
  try {
    const resp = await fetch(`${D.checkWordUrl}?word=${encodeURIComponent(word)}`);
    return resp.ok ? (await resp.json()).exists : false;
  } catch { return false; }
}

async function loadDecks() {
  if (decksCache) return decksCache;
  try {
    const resp = await fetch(D.decksUrl);
    decksCache = resp.ok ? (await resp.json()).decks : [];
    return decksCache;
  } catch { return []; }
}

// Inject "+" button into a token span
function addWordButton(word) {
  const btn = document.createElement('button');
  btn.className = 'token-add-btn';
  btn.title = `Add "${word}" to flashcards`;
  btn.dataset.word = word;
  btn.textContent = '+';
  btn.addEventListener('click', e => {
    e.stopPropagation();
    if (!btn.classList.contains('added')) openAddWord(word);
  });
  return btn;
}

/* ── Init ── */
(async function init() {
  setVideoVisible(false);   // audio-only by default
  setSpeed(1.0);
  await loadProgress();
  buildSegmentList();
  updateOverallProgress();
})();
