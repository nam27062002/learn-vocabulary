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
let videoVisible   = false;   // default: audio-only mode
let isPlaying      = false;

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
const answerReveal   = document.getElementById('answerReveal');
const answerText     = document.getElementById('answerText');
const progressBar    = document.getElementById('progressBar');
const progressLabel  = document.getElementById('progressLabel');
const avgScoreEl     = document.getElementById('avgScore');
const audioStatus    = document.getElementById('audioStatus');

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
  dictationInput.value = '';

  // Update audio status
  if (audioStatus) audioStatus.textContent = `Segment ${seg.order} — ready`;

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

/* ── Render result ── */
function renderResult(result) {
  resultArea.style.display = 'block';
  const pct = Math.round(result.score * 100);
  const cls = pct >= 80 ? 'high' : pct >= 50 ? 'medium' : 'low';
  const emoji = pct >= 80 ? '🎉' : pct >= 50 ? '👍' : '🔄';
  scoreRow.innerHTML =
    `<span class="score-badge ${cls}">${emoji} ${pct}%</span>
     <span class="text-sm text-gray-500">${result.correct_count} / ${result.total_count} words</span>`;

  tokenDisplay.innerHTML = '';
  result.tokens.forEach(tok => {
    const span = document.createElement('span');
    span.className = `token ${tok.status}`;
    if (tok.status === 'correct') {
      span.textContent = tok.word;
    } else if (tok.status === 'wrong') {
      span.innerHTML = `<span style="text-decoration:line-through">${escHtml(tok.user_word)}</span><span class="correct-hint">${escHtml(tok.word)}</span>`;
    } else if (tok.status === 'missing') {
      span.textContent = `[${tok.word}]`;
      span.title = 'Missing';
    } else {
      span.textContent = tok.word;
      span.title = 'Extra';
    }
    tokenDisplay.appendChild(span);
    tokenDisplay.appendChild(document.createTextNode(' '));
  });
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

/* ── Helpers ── */
function formatTime(s) {
  const m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
}
function escHtml(str) {
  return (str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/* ── Init ── */
(async function init() {
  setVideoVisible(false);   // audio-only by default
  setSpeed(1.0);
  await loadProgress();
  buildSegmentList();
  updateOverallProgress();
})();
