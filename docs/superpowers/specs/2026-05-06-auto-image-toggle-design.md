# Design: Auto-generate Image Toggle on /add Page

**Date:** 2026-05-06  
**Status:** Approved

## Problem

Every time a new word is added on `/add`, the app automatically calls the LLM image generation API. This consumes tokens on every word, even when the user doesn't need images. There is no way to opt out.

## Goal

Add a toggle to the `/add` page that controls whether images are auto-generated when word details load. The toggle defaults to OFF, saving tokens unless the user explicitly enables it.

## Design

### Toggle Placement

The toggle lives inside the existing `.deck-selection-area` at the top of the page, separated from the deck selector by a vertical divider. It applies globally to the entire session.

```
[ 📁 Deck: My Vocabulary ▾ ] | [ 🖼️ Auto-generate image  ○── OFF ]
```

When enabled (ON), the toggle turns purple (`#6a6cff`) and the label shows "ON". When disabled (OFF, default), the track is dark gray and label shows "OFF".

### Persistence

Session-only. The toggle resets to OFF each time the user navigates to `/add`. No localStorage, no DB storage.

### Behavior

- **OFF (default):** Word details are still fetched and displayed normally. Only image generation is skipped.
- **ON:** Behavior identical to the current implementation — `generateImageForCard()` is called after word details load.

## Implementation

### 1. HTML — `add_flashcard.html`

Add toggle markup inside `.deck-selection-area`, after the deck selector and a divider:

```html
<div class="auto-image-toggle-group">
  <span>🖼️ Auto-generate image</span>
  <label class="toggle-switch">
    <input type="checkbox" id="auto-image-toggle">
    <span class="toggle-track"></span>
  </label>
  <span id="auto-image-toggle-label">OFF</span>
</div>
```

### 2. CSS — inline `<style>` block in the template

Style the toggle to match the existing dark theme (using `--primary-color`, `--border-color`, etc.).

### 3. JavaScript — inline `<script>` block in the template

```js
let autoImageEnabled = false;

const toggle = document.getElementById('auto-image-toggle');
toggle.addEventListener('change', e => {
  autoImageEnabled = e.target.checked;
  document.getElementById('auto-image-toggle-label').textContent = autoImageEnabled ? 'ON' : 'OFF';
});
```

Guard the auto-generation call (~line 1469 in current template):

```js
// Before:
generateImageForCard(termValue, firstDef, card);

// After:
if (autoImageEnabled) generateImageForCard(termValue, firstDef, card);
```

## Files Changed

| File | Change |
|------|--------|
| `vocabulary/templates/vocabulary/add_flashcard.html` | Add toggle HTML to `.deck-selection-area`, add CSS styles, add JS variable + event listener, add `if (autoImageEnabled)` guard |

No backend changes required.

## Out of Scope

- Persisting the preference (localStorage or DB)
- Cancelling in-flight image requests when toggling OFF
- Per-card image toggle
