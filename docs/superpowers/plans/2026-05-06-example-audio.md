# Example Sentence Audio (Web Speech API) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 🔊 button next to every example sentence so the user can hear it spoken aloud using the browser's built-in Web Speech API.

**Architecture:** Add a global `speakText(text)` function to `static/js/main.js` (loaded on every page via `base.html`). Then add a 🔊 button in each of the three places example sentences appear: the study session, the flashcard detail view, and the /add page. No backend changes required.

**Tech Stack:** Vanilla JS (`window.speechSynthesis`), Django templates.

---

## File Map

| File | Action | What changes |
|---|---|---|
| `static/js/main.js` | Modify | Add global `speakText()` function above the DOMContentLoaded block |
| `vocabulary/templates/vocabulary/study.html` | Modify | Add 🔊 button inside `#cardExample` div |
| `vocabulary/templates/vocabulary/deck_detail.html` | Modify | Add 🔊 button next to example text |
| `vocabulary/templates/vocabulary/add_flashcard.html` | Modify | Add 🔊 button to example sentence label; show/hide in JS |

---

## Task 1: Add `speakText()` global utility to main.js

**Files:**
- Modify: `static/js/main.js` (add above line 5, before the `document.addEventListener` call)

Note: Web Speech API cannot be tested in Django's test runner (no browser). Manual browser verification is the test for all tasks in this plan.

- [ ] **Step 1: Add `speakText` function**

Open `static/js/main.js`. Add these lines at the very top, before the existing `document.addEventListener('DOMContentLoaded', ...)` block (i.e., before line 5):

```javascript
function speakText(text) {
  if (!window.speechSynthesis || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
}
```

The function must be global (outside DOMContentLoaded) so that `onclick` attributes in templates and code in `study.js` can call it directly.

- [ ] **Step 2: Verify in browser console**

Start the dev server: `.venv\Scripts\python.exe manage.py runserver`

Open any page, open browser DevTools console, run:

```javascript
speakText('Hello, this is a test sentence.')
```

Expected: browser speaks the sentence aloud.

- [ ] **Step 3: Commit**

```bash
git add static/js/main.js
git commit -m "feat: add speakText() Web Speech API utility to main.js"
```

---

## Task 2: 🔊 button in study session

**Files:**
- Modify: `vocabulary/templates/vocabulary/study.html` (lines 866–869)

- [ ] **Step 1: Add 🔊 button to `#cardExample`**

In `study.html`, find the `#cardExample` block (around line 866):

```html
<div id="cardExample" class="card-example" style="display:none; margin-top:12px; padding:10px 14px; border-left:3px solid var(--primary-color); background:rgba(106,108,255,0.08); border-radius:0 6px 6px 0;">
  <div style="font-size:10px; text-transform:uppercase; letter-spacing:1px; color:var(--text-muted); margin-bottom:4px;">Example</div>
  <div id="cardExampleText" style="font-style:italic; color:var(--text-main); line-height:1.6;"></div>
</div>
```

Replace with:

```html
<div id="cardExample" class="card-example" style="display:none; margin-top:12px; padding:10px 14px; border-left:3px solid var(--primary-color); background:rgba(106,108,255,0.08); border-radius:0 6px 6px 0;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
    <div style="font-size:10px; text-transform:uppercase; letter-spacing:1px; color:var(--text-muted);">Example</div>
    <button onclick="speakText(document.getElementById('cardExampleText').textContent)" title="Play example" style="background:none; border:none; cursor:pointer; color:var(--text-muted); font-size:14px; padding:2px 4px; border-radius:4px; line-height:1; transition:color 0.2s;" onmouseover="this.style.color='var(--primary-color)'" onmouseout="this.style.color='var(--text-muted)'">🔊</button>
  </div>
  <div id="cardExampleText" style="font-style:italic; color:var(--text-main); line-height:1.6;"></div>
</div>
```

- [ ] **Step 2: Verify in browser**

Go to `/study/`, answer a question. When the example sentence appears, click the 🔊 button.

Expected: browser speaks the example sentence.

- [ ] **Step 3: Commit**

```bash
git add vocabulary/templates/vocabulary/study.html
git commit -m "feat: add speak button to example sentence in study session"
```

---

## Task 3: 🔊 button in flashcard detail view

**Files:**
- Modify: `vocabulary/templates/vocabulary/deck_detail.html` (lines 327–332)

- [ ] **Step 1: Add 🔊 button to example section**

In `deck_detail.html`, find the `{% if card.example_sentence %}` block (around line 327):

```html
{% if card.example_sentence %}
<div class="mt-3" style="padding:8px 12px; border-left:3px solid rgba(106,108,255,0.6); background:rgba(106,108,255,0.06); border-radius:0 6px 6px 0;">
  <div class="text-xs font-medium mb-1" style="color:#7c7cbb; text-transform:uppercase; letter-spacing:0.05em;">Example</div>
  <div class="text-sm text-gray-300" style="font-style:italic; line-height:1.6;">{{ card.example_sentence }}</div>
</div>
{% endif %}
```

Replace with:

```html
{% if card.example_sentence %}
<div class="mt-3" style="padding:8px 12px; border-left:3px solid rgba(106,108,255,0.6); background:rgba(106,108,255,0.06); border-radius:0 6px 6px 0;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
    <div class="text-xs font-medium" style="color:#7c7cbb; text-transform:uppercase; letter-spacing:0.05em;">Example</div>
    <button onclick="speakText('{{ card.example_sentence|escapejs }}')" title="Play example" style="background:none; border:none; cursor:pointer; color:#7c7cbb; font-size:14px; padding:2px 4px; border-radius:4px; line-height:1; transition:color 0.2s;" onmouseover="this.style.color='#a5b4fc'" onmouseout="this.style.color='#7c7cbb'">🔊</button>
  </div>
  <div class="text-sm text-gray-300" style="font-style:italic; line-height:1.6;">{{ card.example_sentence }}</div>
</div>
{% endif %}
```

Note: `{{ card.example_sentence|escapejs }}` escapes quotes and special characters so the string is safe inside the `onclick` attribute.

- [ ] **Step 2: Verify in browser**

Go to any deck, open a flashcard detail that has an example sentence. Click 🔊.

Expected: browser speaks the example sentence.

- [ ] **Step 3: Commit**

```bash
git add vocabulary/templates/vocabulary/deck_detail.html
git commit -m "feat: add speak button to example sentence in flashcard detail view"
```

---

## Task 4: 🔊 button on /add page

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html` (lines 1168–1180 for HTML; the `updateCardUI` JS function for show/hide logic)

- [ ] **Step 1: Add hidden 🔊 button to example label**

In `add_flashcard.html`, find the example sentence `<div class="input-field">` block (around line 1168):

```html
<div class="input-field" style="margin-top: 10px;">
    <label style="display:flex; align-items:center; gap:8px;">
        Example Sentence
        <span class="example-auto-badge" style="display:none; font-size:0.75em; color:#4caf50; font-weight:normal;">✦ auto-generated</span>
    </label>
    <textarea
        class="example-textarea"
        rows="2"
        placeholder="e.g. She is a resilient person who bounced back after every setback."
        style="background:rgba(74,144,226,0.06); border-color:rgba(74,144,226,0.3);"
    ></textarea>
    <input type="hidden" class="example-source-input" value="">
</div>
```

Replace with:

```html
<div class="input-field" style="margin-top: 10px;">
    <label style="display:flex; align-items:center; gap:8px;">
        Example Sentence
        <span class="example-auto-badge" style="display:none; font-size:0.75em; color:#4caf50; font-weight:normal;">✦ auto-generated</span>
        <button type="button" class="example-speak-btn" title="Play example" style="display:none; background:none; border:none; cursor:pointer; color:var(--text-muted); font-size:14px; padding:2px 4px; border-radius:4px; line-height:1;">🔊</button>
    </label>
    <textarea
        class="example-textarea"
        rows="2"
        placeholder="e.g. She is a resilient person who bounced back after every setback."
        style="background:rgba(74,144,226,0.06); border-color:rgba(74,144,226,0.3);"
    ></textarea>
    <input type="hidden" class="example-source-input" value="">
</div>
```

- [ ] **Step 2: Wire 🔊 button in `updateCardUI`**

In `add_flashcard.html`, find the `updateCardUI` JavaScript function. After the block that sets `exampleTextarea.value` (around line 1636):

```javascript
if (exampleTextarea && data.example_sentence) {
    exampleTextarea.value = data.example_sentence;
    if (exampleSourceInput) exampleSourceInput.value = data.example_source || '';
    if (exampleBadge) exampleBadge.style.display = 'inline';
}
```

Add immediately after:

```javascript
const speakBtn = card.querySelector('.example-speak-btn');
if (speakBtn && data.example_sentence) {
    speakBtn.style.display = 'inline';
    speakBtn.onclick = () => speakText(card.querySelector('.example-textarea').value.trim());
}
```

- [ ] **Step 3: Hide 🔊 button in `resetCardUI`**

In `add_flashcard.html`, find the `resetCardUI` function. After the block that resets the example fields:

```javascript
if (exampleTextarea) exampleTextarea.value = '';
if (exampleSourceInput) exampleSourceInput.value = '';
if (exampleBadge) exampleBadge.style.display = 'none';
```

Add:

```javascript
const speakBtn = card.querySelector('.example-speak-btn');
if (speakBtn) speakBtn.style.display = 'none';
```

- [ ] **Step 4: Verify in browser**

Go to `/add/`, type a word, wait for auto-populate. When example sentence appears, the 🔊 button should appear next to the label. Click it.

Expected: browser speaks the example sentence. If you clear the card, the 🔊 button disappears.

- [ ] **Step 5: Commit**

```bash
git add vocabulary/templates/vocabulary/add_flashcard.html
git commit -m "feat: add speak button to example sentence on /add page"
```
