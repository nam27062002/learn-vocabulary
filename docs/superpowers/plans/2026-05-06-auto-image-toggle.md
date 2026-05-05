# Auto-generate Image Toggle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a toggle to the /add page that defaults to OFF and prevents the LLM image generation API from being called unless the user explicitly enables it.

**Architecture:** Single-file change in `add_flashcard.html` — add toggle HTML to the existing `.deck-selection-area`, add CSS styles in the inline `<style>` block, add a JS boolean variable + event listener in the inline `<script>` block, and guard the `generateImageForCard()` call.

**Tech Stack:** Django template, vanilla JS, inline CSS

---

## File Map

| File | Change |
|------|--------|
| `vocabulary/templates/vocabulary/add_flashcard.html` | Add toggle HTML (lines ~858), CSS styles (in `<style>` block), JS variable + listener (in `<script>` block), guard at line ~1469 |

---

### Task 1: Add toggle HTML to `.deck-selection-area`

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html:858`

The current structure of `.deck-selection-area` ends at line 859 with `</div>`. Insert the divider + toggle group between the closing `</select>` (line 858) and closing `</div>` (line 859).

- [ ] **Step 1: Open the template and locate the deck-selection-area**

The block to modify is at lines 850–859:

```html
<div class="deck-selection-area">
  <label for="deck-selector">{{ manual_texts.select_deck }}</label>
  <select id="deck-selector" name="deck">
    <option value="">{{ manual_texts.please_select_deck }}</option>
    <option value="new_deck">{{ manual_texts.create_new_deck }}</option>
    {% for deck in decks %}
      <option value="{{ deck.id }}">{{ deck.name }}</option>
    {% endfor %}
  </select>
</div>
```

- [ ] **Step 2: Add the toggle HTML after `</select>` and before `</div>`**

Replace the closing `</select>\n  </div>` with:

```html
    </select>
    <div class="auto-image-divider"></div>
    <div class="auto-image-toggle-group">
      <span class="auto-image-toggle-label">🖼️ Auto-generate image</span>
      <label class="toggle-switch" for="auto-image-toggle">
        <input type="checkbox" id="auto-image-toggle">
        <span class="toggle-track"></span>
      </label>
      <span id="auto-image-toggle-state">OFF</span>
    </div>
  </div>
```

- [ ] **Step 3: Verify the HTML renders correctly**

Start the dev server (`python manage.py runserver`) and open `http://127.0.0.1:8000/add/`. Confirm the toggle element appears in the deck selection bar (unstyled is fine at this stage).

---

### Task 2: Add CSS styles for the toggle

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html` — inside the inline `<style>` block (after the existing `#deck-selector:focus` rule, around line 88)

- [ ] **Step 1: Add styles for the divider and toggle group**

Inside the `<style>` block, after the `#deck-selector:focus { ... }` rule, add:

```css
.auto-image-divider {
  width: 1px;
  height: 36px;
  background-color: var(--border-color);
  flex-shrink: 0;
}

.auto-image-toggle-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.auto-image-toggle-label {
  font-size: 0.9em;
  color: var(--text-muted);
  white-space: nowrap;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 42px;
  height: 22px;
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}

.toggle-track {
  position: absolute;
  inset: 0;
  background-color: var(--border-color);
  border-radius: 11px;
  transition: background-color 0.2s ease;
}

.toggle-track::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  background-color: #6a6a8a;
  border-radius: 50%;
  transition: left 0.2s ease, background-color 0.2s ease;
}

.toggle-switch input:checked + .toggle-track {
  background-color: var(--primary-color);
}

.toggle-switch input:checked + .toggle-track::after {
  left: 23px;
  background-color: #fff;
}

#auto-image-toggle-state {
  font-size: 0.82em;
  color: #6a6a8a;
  min-width: 26px;
  font-weight: 500;
}

#auto-image-toggle-state.is-on {
  color: var(--primary-color);
  font-weight: 600;
}
```

- [ ] **Step 2: Verify styling in browser**

Reload `http://127.0.0.1:8000/add/`. Confirm:
- A vertical divider appears between the deck selector and the toggle
- The toggle track is dark gray (OFF state)
- Clicking the toggle visually switches to purple (ON state)
- The label reads "OFF" / "ON" (JS not wired yet, so text won't change — that's expected)

---

### Task 3: Add JS variable and event listener

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html` — inside the inline `<script>` block

- [ ] **Step 1: Locate the JS variable declarations block**

Around line 1080–1081, the script block starts with:

```js
let cardCount = 1;
let wordApiCache = {};
```

- [ ] **Step 2: Add `autoImageEnabled` variable after `wordApiCache`**

Insert after `let wordApiCache = {};`:

```js
let autoImageEnabled = false;
```

- [ ] **Step 3: Add the toggle event listener**

After the `styleCreateNewDeckOption();` call (around line 1103), add:

```js
const autoImageToggle = document.getElementById('auto-image-toggle');
const autoImageToggleState = document.getElementById('auto-image-toggle-state');
autoImageToggle.addEventListener('change', function() {
    autoImageEnabled = this.checked;
    autoImageToggleState.textContent = autoImageEnabled ? 'ON' : 'OFF';
    autoImageToggleState.classList.toggle('is-on', autoImageEnabled);
});
```

- [ ] **Step 4: Verify toggle state label updates in browser**

Reload the page, click the toggle. Confirm:
- Label changes from "OFF" to "ON" when toggled on
- Label changes back to "OFF" when toggled off
- `autoImageEnabled` variable reflects the state (open DevTools console, type `autoImageEnabled` after toggling)

---

### Task 4: Guard the `generateImageForCard()` call

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html:1469`

- [ ] **Step 1: Locate the auto-generate call**

Find this block (around line 1466–1469):

```js
        // Auto-generate image (async, non-blocking)
        const termValue = card.querySelector('.term-input').value.trim();
        const firstDef = data.meanings?.[0]?.definitions?.[0]?.en || '';
        generateImageForCard(termValue, firstDef, card);
```

- [ ] **Step 2: Wrap with the guard**

Replace the `generateImageForCard(...)` call with:

```js
        // Auto-generate image (async, non-blocking)
        const termValue = card.querySelector('.term-input').value.trim();
        const firstDef = data.meanings?.[0]?.definitions?.[0]?.en || '';
        if (autoImageEnabled) generateImageForCard(termValue, firstDef, card);
```

- [ ] **Step 3: Test the full flow with toggle OFF (default)**

1. Reload `http://127.0.0.1:8000/add/`
2. Ensure toggle shows "OFF"
3. Type a word (e.g. "apple") in the term input
4. Wait for word details to load
5. Confirm **no image appears** and **no request to `/api/ai/generate-image/`** is made (check Network tab in DevTools)

- [ ] **Step 4: Test the full flow with toggle ON**

1. Click the toggle to ON
2. Type a new word (e.g. "river")
3. Wait for word details to load
4. Confirm an image **does** appear (or a loading spinner, then image)
5. Check Network tab — `/api/ai/generate-image/` request should be present

- [ ] **Step 5: Commit**

```bash
git add vocabulary/templates/vocabulary/add_flashcard.html
git commit -m "feat: add auto-generate image toggle to /add page (off by default)"
```
