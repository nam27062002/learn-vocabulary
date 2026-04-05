(function () {
  'use strict';

  // Inject loading animation CSS once.
  var style = document.createElement('style');
  style.textContent = [
    '@keyframes aiDotBounce {',
    '  0%,80%,100% { transform: translateY(0); opacity:.4; }',
    '  40%          { transform: translateY(-10px); opacity:1; }',
    '}',
    '@keyframes aiTextPulse {',
    '  0%,100% { opacity:.5; }',
    '  50%     { opacity:1; }',
    '}',
    '.ai-dot {',
    '  display:inline-block; width:10px; height:10px;',
    '  border-radius:50%; background:#6366f1;',
    '  animation: aiDotBounce 1.4s ease-in-out infinite;',
    '}',
    '.ai-dot:nth-child(2) { animation-delay:.16s; background:#818cf8; }',
    '.ai-dot:nth-child(3) { animation-delay:.32s; background:#a5b4fc; }',
    '.ai-loading-text {',
    '  margin-top:14px; font-size:.9rem; letter-spacing:.04em;',
    '  color:#a5b4fc; animation: aiTextPulse 2s ease-in-out infinite;',
    '}',
  ].join('\n');
  document.head.appendChild(style);

  // Escape special regex metacharacters in a string.
  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Build a sentence <li> safely using DOM API (no innerHTML on AI content).
  function buildSentenceLi(sentence, word, index) {
    const li = document.createElement('li');
    li.style.cssText =
      'background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.2);' +
      'border-radius:10px; padding:12px 16px; color:#e2e8f0; line-height:1.6; font-size:0.95rem;';

    const num = document.createElement('span');
    num.style.cssText = 'color:#9ca3af; font-size:0.75rem; font-weight:600; margin-right:6px;';
    num.textContent = `${index + 1}.`;
    li.appendChild(num);

    // Split sentence on word boundaries, highlight matches safely.
    const re = new RegExp(`(${escapeRegex(word)})`, 'gi');
    const parts = sentence.split(re);
    parts.forEach(function (part) {
      if (re.test(part)) {
        const strong = document.createElement('strong');
        strong.style.color = '#a5b4fc';
        strong.textContent = part;
        li.appendChild(strong);
      } else {
        li.appendChild(document.createTextNode(part));
      }
      re.lastIndex = 0; // reset stateful regex after each test()
    });

    return li;
  }

  function openAiExamplesModal(word) {
    const modal = document.getElementById('aiExamplesModal');
    const loading = document.getElementById('aiExamplesLoading');
    const list = document.getElementById('aiExamplesList');
    const errorEl = document.getElementById('aiExamplesError');

    document.getElementById('aiExamplesWord').textContent = word;
    loading.style.display = 'block';
    list.style.display = 'none';
    list.innerHTML = '';
    errorEl.style.display = 'none';
    modal.style.display = 'block';

    fetch('/api/ai/word-examples/?word=' + encodeURIComponent(word))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        loading.style.display = 'none';
        if (data.success && data.sentences && data.sentences.length) {
          data.sentences.forEach(function (s, i) {
            list.appendChild(buildSentenceLi(s, word, i));
          });
          list.style.display = 'flex';
        } else {
          errorEl.textContent = data.error || 'No examples returned.';
          errorEl.style.display = 'block';
        }
      })
      .catch(function () {
        loading.style.display = 'none';
        errorEl.textContent = 'Failed to connect to AI service.';
        errorEl.style.display = 'block';
      });
  }

  function closeAiExamplesModal() {
    document.getElementById('aiExamplesModal').style.display = 'none';
  }

  document.addEventListener('DOMContentLoaded', function () {
    var closeBtn = document.getElementById('closeAiExamplesModal');
    var overlay = document.getElementById('aiExamplesOverlay');
    var modal = document.getElementById('aiExamplesModal');

    if (closeBtn) closeBtn.addEventListener('click', closeAiExamplesModal);

    if (overlay) {
      overlay.addEventListener('click', function (e) {
        if (e.target === overlay) closeAiExamplesModal();
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && modal && modal.style.display !== 'none') {
        closeAiExamplesModal();
      }
    });

    // Deck detail: delegated click on .ai-examples-btn cards
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.ai-examples-btn');
      if (btn && btn.dataset.word) {
        openAiExamplesModal(btn.dataset.word);
      }
    });

    // Study page: direct button + MutationObserver to mirror edit button visibility
    var studyBtn = document.getElementById('aiExamplesButton');
    var editBtn = document.getElementById('editCardButton');

    if (studyBtn) {
      studyBtn.addEventListener('click', function () {
        var word = document.getElementById('cardWord').textContent.trim();
        if (word) openAiExamplesModal(word);
      });
    }

    if (editBtn && studyBtn) {
      var observer = new MutationObserver(function () {
        studyBtn.style.display = editBtn.style.display;
      });
      observer.observe(editBtn, { attributes: true, attributeFilter: ['style'] });
    }
  });
})();
