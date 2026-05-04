# Fetch Missing Images Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Fetch Missing Images" button to `/decks/{deck_id}/` that batch-generates AI images for all flashcards missing both `image` and `related_image_url`, with a live progress bar.

**Architecture:** A new `POST /api/ai/save-generated-image/` endpoint accepts a `flashcard_id`, calls the existing `generate_word_image()` service, and saves the result as a local file to `Flashcard.image`. The frontend in `deck_detail.js` reads card IDs from DOM data attributes and processes them sequentially, updating a progress panel after each card.

**Tech Stack:** Django (views, URL routing), `image_service.generate_word_image` (existing), `ContentFile` (existing import), Vanilla JS (existing `deck_detail.js`), CSS class `.audio-fetch-progress` (existing in `main.css`)

---

## File Map

| File | Change |
|------|--------|
| `vocabulary/views.py` | Add `api_save_generated_image` view after line 2585 |
| `vocabulary/api_urls.py` | Add URL for the new view in AI features section |
| `vocabulary/templates/vocabulary/deck_detail.html` | Add `data-has-image` attribute (line 169), add button (after line 139) |
| `static/js/deck_detail.js` | Add `initializeImageFetching()` call (line 275), add two functions after line 1567 |
| `tests/test_save_generated_image.py` | New test file for the endpoint |

---

## Task 1: Write failing tests for `api_save_generated_image`

**Files:**
- Create: `tests/test_save_generated_image.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_save_generated_image.py
import json
import base64
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, Definition, Deck

User = get_user_model()


class SaveGeneratedImageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='imgtest@test.com', password='pass')
        self.client.force_login(self.user)
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')
        self.card = Flashcard.objects.create(user=self.user, deck=self.deck, word='resilient')
        Definition.objects.create(
            flashcard=self.card,
            english_definition='able to recover quickly from difficulties',
            vietnamese_definition='kiên cường',
        )

    def test_save_generated_image_success(self):
        """Endpoint saves b64 image to card.image and returns success."""
        fake_b64 = base64.b64encode(b'fake-png-data').decode()
        with patch('vocabulary.views.generate_word_image', return_value=fake_b64):
            response = self.client.post(
                '/api/ai/save-generated-image/',
                data=json.dumps({'flashcard_id': self.card.id}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['word'], 'resilient')
        self.card.refresh_from_db()
        self.assertTrue(bool(self.card.image))

    def test_returns_404_for_card_of_other_user(self):
        """Endpoint returns 404 when card belongs to a different user."""
        other = User.objects.create_user(email='other@test.com', password='pass')
        other_card = Flashcard.objects.create(user=other, word='agile')
        response = self.client.post(
            '/api/ai/save-generated-image/',
            data=json.dumps({'flashcard_id': other_card.id}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_returns_error_when_generation_fails(self):
        """Endpoint returns success=False when image_service returns None."""
        with patch('vocabulary.views.generate_word_image', return_value=None):
            response = self.client.post(
                '/api/ai/save-generated-image/',
                data=json.dumps({'flashcard_id': self.card.id}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    def test_requires_post_method(self):
        """Endpoint rejects GET requests."""
        response = self.client.get('/api/ai/save-generated-image/')
        self.assertEqual(response.status_code, 405)

    def test_unauthenticated_user_is_redirected(self):
        """Endpoint redirects unauthenticated users."""
        self.client.logout()
        response = self.client.post(
            '/api/ai/save-generated-image/',
            data=json.dumps({'flashcard_id': self.card.id}),
            content_type='application/json',
        )
        self.assertIn(response.status_code, [302, 401, 403])
```

- [ ] **Step 2: Run tests to verify they fail**

```
python manage.py test tests.test_save_generated_image -v 2
```

Expected: All tests FAIL with errors like `404 Not Found` (URL not registered yet) or `AttributeError` (view not defined yet).

- [ ] **Step 3: Commit the test file**

```
git add tests/test_save_generated_image.py
git commit -m "test: add failing tests for api_save_generated_image endpoint"
```

---

## Task 2: Add `api_save_generated_image` view

**Files:**
- Modify: `vocabulary/views.py` — add after line 2585 (after `api_generate_word_image`)

- [ ] **Step 1: Add the view function**

In `vocabulary/views.py`, locate the end of `api_generate_word_image` (line ~2585, just before `def debug_study_template`). Insert this new function:

```python
@login_required
@require_POST
def api_save_generated_image(request):
    """Generate an AI image for a flashcard and save it as a local file."""
    import base64
    from .image_service import generate_word_image
    try:
        data = json.loads(request.body)
        card_id = data.get('flashcard_id')

        try:
            card = Flashcard.objects.get(id=card_id, user=request.user)
        except Flashcard.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Flashcard not found'}, status=404)

        first_def = card.definitions.first()
        definition = first_def.english_definition if first_def else ''

        b64 = generate_word_image(card.word, definition)
        if not b64:
            return JsonResponse({'success': False, 'error': 'Image generation failed'})

        image_bytes = base64.b64decode(b64)
        filename = f'{card.word}.png'
        card.image.save(filename, ContentFile(image_bytes), save=True)

        return JsonResponse({'success': True, 'word': card.word})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

Note: `ContentFile` is already imported at the top of `views.py` (line 12). `base64` is imported locally to avoid adding a new top-level import.

- [ ] **Step 2: Commit**

```
git add vocabulary/views.py
git commit -m "feat: add api_save_generated_image view"
```

---

## Task 3: Register URL for the new endpoint

**Files:**
- Modify: `vocabulary/api_urls.py` — add inside the `# AI features` section

- [ ] **Step 1: Add URL entry**

In `vocabulary/api_urls.py`, locate the AI features section (around line 67). Add the new path after the existing `api/ai/generate-image/` entry:

```python
    # AI features
    path('api/ai/word-examples/', views.api_ai_word_examples, name='api_ai_word_examples'),
    path('api/ai/vstep-suggestions/', views.api_vstep_suggestions, name='api_vstep_suggestions'),
    path('api/ai/generate-image/', views.api_generate_word_image, name='api_generate_word_image'),
    path('api/ai/save-generated-image/', views.api_save_generated_image, name='api_save_generated_image'),
```

- [ ] **Step 2: Run tests to verify they now pass**

```
python manage.py test tests.test_save_generated_image -v 2
```

Expected: All 5 tests PASS.

- [ ] **Step 3: Commit**

```
git add vocabulary/api_urls.py
git commit -m "feat: register api_save_generated_image URL"
```

---

## Task 4: Add `data-has-image` attribute to card slides in template

**Files:**
- Modify: `vocabulary/templates/vocabulary/deck_detail.html` — card slide div around line 166-170

- [ ] **Step 1: Add attribute**

Locate this block (around line 166-170):

```html
        <div
          class="flex-shrink-0 snap-center"
          style="width: 100%"
          data-card-id="{{ card.id }}"
        >
```

Change it to:

```html
        <div
          class="flex-shrink-0 snap-center"
          style="width: 100%"
          data-card-id="{{ card.id }}"
          data-has-image="{% if card.image or card.related_image_url %}true{% else %}false{% endif %}"
        >
```

- [ ] **Step 2: Commit**

```
git add vocabulary/templates/vocabulary/deck_detail.html
git commit -m "feat: add data-has-image attribute to deck card slides"
```

---

## Task 5: Add "Fetch Missing Images" button to deck detail template

**Files:**
- Modify: `vocabulary/templates/vocabulary/deck_detail.html` — inside `.audio-filter-controls` div, after the fetch audio button (around line 139)

- [ ] **Step 1: Add the button**

Locate this section (around line 132-140):

```html
    <!-- Fetch Missing Audio Button -->
    <button
      id="fetch-missing-audio-btn"
      class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center gap-2"
    >
      <i class="fas fa-download"></i>
      {{ manual_texts.fetch_missing_audio }}
    </button>
  </div>
```

Change it to:

```html
    <!-- Fetch Missing Audio Button -->
    <button
      id="fetch-missing-audio-btn"
      class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center gap-2"
    >
      <i class="fas fa-download"></i>
      {{ manual_texts.fetch_missing_audio }}
    </button>

    <!-- Fetch Missing Images Button -->
    <button
      id="fetch-missing-images-btn"
      class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center gap-2"
    >
      <i class="fas fa-image"></i>
      Fetch Missing Images
    </button>
  </div>
```

- [ ] **Step 2: Commit**

```
git add vocabulary/templates/vocabulary/deck_detail.html
git commit -m "feat: add Fetch Missing Images button to deck detail"
```

---

## Task 6: Add JS image fetching logic to `deck_detail.js`

**Files:**
- Modify: `static/js/deck_detail.js` — two changes

- [ ] **Step 1: Add `initializeImageFetching()` call**

Locate around line 274-275:

```javascript
  // Initialize audio fetching functionality
  initializeAudioFetching();
```

Change to:

```javascript
  // Initialize audio fetching functionality
  initializeAudioFetching();

  // Initialize image fetching functionality
  initializeImageFetching();
```

- [ ] **Step 2: Add the two new functions**

Locate the end of `updateProgressIndicator` (around line 1567, just before `function fetchAudioForSingleCard`):

```javascript
  function fetchAudioForSingleCard(cardId) {
```

Insert before it:

```javascript
  // Image fetching functionality
  function initializeImageFetching() {
    const fetchBtn = document.getElementById("fetch-missing-images-btn");
    if (!fetchBtn) return;
    fetchBtn.addEventListener("click", fetchMissingImagesForDeck);
  }

  async function fetchMissingImagesForDeck() {
    const fetchBtn = document.getElementById("fetch-missing-images-btn");

    const cardIds = [
      ...document.querySelectorAll("[data-card-id][data-has-image='false']"),
    ].map((el) => el.dataset.cardId);

    if (cardIds.length === 0) {
      Notify.info("No cards need images");
      return;
    }

    fetchBtn.disabled = true;
    const originalText = fetchBtn.innerHTML;
    fetchBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Generating images...`;

    const progressDiv = document.createElement("div");
    progressDiv.className = "audio-fetch-progress";
    progressDiv.innerHTML = `
      <button class="close-btn" onclick="this.parentNode.remove()">
        <i class="fas fa-times"></i>
      </button>
      <div class="progress-header">
        <i class="fas fa-image"></i>
        <span>Generating images... 0/${cardIds.length}</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" style="width: 0%"></div>
      </div>
      <div class="progress-text">
        <span class="current-word">Starting...</span>
      </div>
    `;
    document.body.appendChild(progressDiv);

    const header = progressDiv.querySelector(".progress-header span");
    const progressFill = progressDiv.querySelector(".progress-fill");
    const currentWordEl = progressDiv.querySelector(".current-word");
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    let generated = 0;
    let failed = 0;

    for (let i = 0; i < cardIds.length; i++) {
      progressFill.style.width = `${(i / cardIds.length) * 100}%`;
      header.textContent = `Generating images... ${i}/${cardIds.length}`;

      try {
        const res = await fetch("/api/ai/save-generated-image/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({ flashcard_id: cardIds[i] }),
        });
        const data = await res.json();

        if (data.success) {
          generated++;
          currentWordEl.textContent = `✓ ${data.word}`;
        } else {
          failed++;
          currentWordEl.textContent = `✗ failed`;
        }
      } catch {
        failed++;
        currentWordEl.textContent = `✗ error`;
      }

      progressFill.style.width = `${((i + 1) / cardIds.length) * 100}%`;
      header.textContent = `Generating images... ${i + 1}/${cardIds.length}`;
    }

    header.textContent = "Image generation complete";
    currentWordEl.textContent = `Generated: ${generated} / Failed: ${failed}`;
    progressFill.style.width = "100%";

    fetchBtn.disabled = false;
    fetchBtn.innerHTML = originalText;

    if (generated > 0) {
      Notify.success(`${generated} images generated!`);
      setTimeout(() => window.location.reload(), 2000);
    } else {
      Notify.info("No images could be generated");
      setTimeout(() => {
        if (progressDiv.parentNode) progressDiv.parentNode.removeChild(progressDiv);
      }, 3000);
    }
  }

  function fetchAudioForSingleCard(cardId) {
```

- [ ] **Step 3: Commit**

```
git add static/js/deck_detail.js
git commit -m "feat: add fetchMissingImagesForDeck JS with live progress bar"
```

---

## Task 7: Manual verification

- [ ] **Step 1: Run the dev server**

```
python manage.py runserver
```

- [ ] **Step 2: Open a deck with flashcards that have no images**

Navigate to `http://localhost:8000/decks/{id}/`. Confirm:
- "Fetch Missing Images" purple button appears in the audio filter controls area
- Button is visible alongside the "Fetch Missing Audio" button

- [ ] **Step 3: Click "Fetch Missing Images"**

Confirm:
- Button disables and shows spinner
- Progress panel appears in top-right corner (same style as audio fetch panel)
- Progress bar fills live, header shows "X/N" count, current word shows after each card
- On completion, panel shows "Generated: X / Failed: Y"
- Page reloads after 2 seconds if any images were generated
- After reload, generated images appear on the cards

- [ ] **Step 4: Test 0-card edge case**

Open a deck where all cards already have images. Click the button. Confirm:
- A toast "No cards need images" appears immediately
- No progress panel appears
- Page does not reload

- [ ] **Step 5: Run all tests**

```
python manage.py test -v 2
```

Expected: All tests pass, no regressions.
