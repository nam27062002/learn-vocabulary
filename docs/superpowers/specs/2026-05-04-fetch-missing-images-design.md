# Fetch Missing Images Feature — Design Spec

**Date:** 2026-05-04  
**Scope:** Add "Fetch Missing Images" button to `/decks/{deck_id}/` page, similar to the existing "Fetch Missing Audio" feature.

---

## Overview

Users can trigger batch AI image generation for all flashcards in a deck that have no image. Generated images are saved as local files to the `Flashcard.image` field. A progress bar shows live updates per card.

---

## Backend

### New endpoint: `POST /api/ai/save-generated-image/`

**File:** `vocabulary/views.py`  
**Registered in:** `vocabulary/api_urls.py`

**Request body:**
```json
{ "flashcard_id": 42 }
```

**Logic:**
1. Authenticate user (`@login_required`, `@require_POST`)
2. Get `Flashcard` by `id` and `user=request.user` → 404 if not found
3. Get first English definition string from `card.definitions.first()` (empty string if none)
4. Call `generate_word_image(card.word, definition)` from `image_service.py` → returns base64 PNG or `None`
5. If `None` → return `{success: false, error: "Image generation failed"}`
6. Decode base64 → `ContentFile` → `card.image.save(f'{card.word}.png', content, save=True)`
7. Return `{success: true, word: card.word}`

**Error cases:**
- Card not found / not owned by user → 404
- LLM failure → `{success: false, error: "..."}`

---

## Frontend

### Template changes (`vocabulary/templates/vocabulary/deck_detail.html`)

1. **Data attribute on each card container:**
```html
<div data-card-id="{{ card.id }}"
     data-has-image="{% if card.image or card.related_image_url %}true{% else %}false{% endif %}">
```

2. **Button** added next to existing "Fetch Missing Audio" button:
```html
<button id="fetch-missing-images-btn"
  class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center gap-2">
  <i class="fas fa-image"></i>
  Fetch Missing Images
</button>
```

3. **Progress modal** (new, inline HTML):
```html
<div id="fetch-images-modal" class="hidden fixed inset-0 ...">
  <div>
    <p id="fetch-images-status">Generating images... 0/N</p>
    <div class="progress-bar"><div id="fetch-images-bar" style="width:0%"></div></div>
    <p id="fetch-images-current-word"></p>
  </div>
</div>
```

### JS logic (inline script in template)

```javascript
document.getElementById('fetch-missing-images-btn').addEventListener('click', async () => {
  // 1. Collect cards without images
  const cards = [...document.querySelectorAll('[data-card-id][data-has-image="false"]')]
    .map(el => el.dataset.cardId);

  if (cards.length === 0) {
    // Show toast: "No cards need images"
    return;
  }

  // 2. Show progress modal
  showFetchImagesModal(cards.length);

  let generated = 0, failed = 0;

  // 3. Sequential loop
  for (let i = 0; i < cards.length; i++) {
    updateProgress(i, cards.length, currentWord);

    const res = await fetch('/api/ai/save-generated-image/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
      body: JSON.stringify({ flashcard_id: cards[i] })
    });
    const data = await res.json();

    if (data.success) generated++;
    else failed++;

    updateProgress(i + 1, cards.length, data.word || '');
  }

  // 4. Show summary then reload
  showSummary(generated, failed);
  setTimeout(() => location.reload(), 1500);
});
```

---

## Data flow

```
User clicks button
  → JS reads DOM for card IDs with data-has-image="false"
  → Loop: POST /api/ai/save-generated-image/ per card
    → views.py: generate_word_image() → b64
    → Save b64 as file → card.image field
    → Return {success, word}
  → JS updates progress bar
  → On complete: show summary, reload page
```

---

## What is NOT in scope

- Cancel button for in-progress batch (keep simple, same as fetch audio)
- Overwriting existing images (only cards with both `image` AND `related_image_url` empty are processed)
- SSE or polling-based progress (frontend-driven sequential requests chosen for simplicity)
