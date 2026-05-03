# VSTEP Vocabulary Suggestions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a one-click "VSTEP Suggestions" button to the `/add` page that uses the LLM proxy to suggest 20 VSTEP exam words the user doesn't already know, then auto-populates flashcard cards.

**Architecture:** New backend endpoint calls the LLM proxy with a prompt requesting VSTEP words, excluding the user's existing vocabulary. Frontend adds a button that calls this endpoint and pipes the result into the existing `generateCardsFromWords()` flow.

**Tech Stack:** Django views, LLM proxy (OpenAI-compatible API at `settings.LLM_URL`), existing JavaScript on the `/add` page.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `vocabulary/ai_service.py` | Modify | Add `get_vstep_suggestions(existing_words)` function |
| `vocabulary/views.py` | Modify | Add `api_vstep_suggestions` view |
| `vocabulary/api_urls.py` | Modify | Add URL route for the new endpoint |
| `vocabulary/context_processors.py` | Modify | Add i18n text entries for VSTEP UI |
| `vocabulary/templates/vocabulary/add_flashcard.html` | Modify | Add VSTEP section (CSS + HTML + JS) |
| `vocabulary/tests.py` | Modify | Add tests for the endpoint |

---

### Task 1: Backend — `get_vstep_suggestions` in `ai_service.py`

**Files:**
- Modify: `vocabulary/ai_service.py` (append new function after line 57)
- Test: `vocabulary/tests.py`

- [ ] **Step 1: Write the failing test**

Add to the end of `vocabulary/tests.py`:

```python
from unittest.mock import patch, MagicMock


class VSTEPSuggestionsServiceTest(TestCase):
    @patch('vocabulary.ai_service.requests.post')
    def test_get_vstep_suggestions_returns_words(self, mock_post):
        """Test that get_vstep_suggestions returns a list of words from LLM."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '["phenomenon", "substantial", "prevalent"]'}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        from vocabulary.ai_service import get_vstep_suggestions
        result = get_vstep_suggestions(['hello', 'world'])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertIn('phenomenon', result)

    @patch('vocabulary.ai_service.requests.post')
    def test_get_vstep_suggestions_filters_existing_words(self, mock_post):
        """Test that words already in existing_words are filtered out."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '["hello", "phenomenon", "world"]'}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        from vocabulary.ai_service import get_vstep_suggestions
        result = get_vstep_suggestions(['hello', 'world'])
        self.assertEqual(result, ['phenomenon'])

    @patch('vocabulary.ai_service.requests.post')
    def test_get_vstep_suggestions_handles_llm_failure(self, mock_post):
        """Test graceful handling when LLM request fails."""
        mock_post.side_effect = Exception('Connection refused')

        from vocabulary.ai_service import get_vstep_suggestions
        with self.assertRaises(Exception):
            get_vstep_suggestions([])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test vocabulary.tests.VSTEPSuggestionsServiceTest -v 2`
Expected: FAIL — `ImportError: cannot import name 'get_vstep_suggestions'`

- [ ] **Step 3: Implement `get_vstep_suggestions` in `ai_service.py`**

Add the following function at the end of `vocabulary/ai_service.py` (after line 57):

```python
def get_vstep_suggestions(existing_words: list[str]) -> list[str]:
    """
    Return 20 VSTEP exam vocabulary words via the LLM proxy,
    excluding words the user already knows.
    Results are cached for 1 hour keyed by the sorted word set.
    """
    existing_lower = {w.lower() for w in existing_words}

    cache_key = f'vstep_suggestions:{hash(tuple(sorted(existing_lower)))}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    exclusion_text = ', '.join(existing_words[:200]) if existing_words else 'none'

    prompt = (
        'You are a VSTEP exam preparation expert. '
        'Give me exactly 20 English vocabulary words that are most commonly tested '
        'in VSTEP exams (levels B1 to C1).\n\n'
        'Rules:\n'
        '- Prioritize words by frequency of appearance in VSTEP exams (most common first)\n'
        '- Focus on academic and general English words used across Reading, Listening, Writing sections\n'
        '- Do NOT include any of these words the user already knows: '
        f'{exclusion_text}\n'
        '- Return ONLY a JSON array of 20 strings, no explanation\n'
        '- Example: ["phenomenon", "substantial", "prevalent"]'
    )

    response = requests.post(
        settings.LLM_URL,
        json={
            'model': settings.LLM_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 400,
        },
        headers={'Authorization': f'Bearer {settings.LLM_API_KEY}'},
        timeout=settings.LLM_TIMEOUT,
        verify=False,
    )
    response.raise_for_status()
    content = response.json()['choices'][0]['message']['content'].strip()

    match = re.search(r'\[.*?\]', content, re.DOTALL)
    if match:
        words = json.loads(match.group())
        words = [w for w in words if isinstance(w, str)]
    else:
        words = [
            re.sub(r'^[\d.\-) ]+', '', line).strip()
            for line in content.splitlines()
            if line.strip()
        ]

    result = [w for w in words if w.lower() not in existing_lower][:20]
    cache.set(cache_key, result, timeout=60 * 60)
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test vocabulary.tests.VSTEPSuggestionsServiceTest -v 2`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add vocabulary/ai_service.py vocabulary/tests.py
git commit -m "feat(vstep): add get_vstep_suggestions LLM service function"
```

---

### Task 2: Backend — `api_vstep_suggestions` view + URL route

**Files:**
- Modify: `vocabulary/views.py` (add view after `api_ai_word_examples` at ~line 2545)
- Modify: `vocabulary/api_urls.py` (add route)
- Test: `vocabulary/tests.py`

- [ ] **Step 1: Write the failing test**

Add to the end of `vocabulary/tests.py`:

```python
class VSTEPSuggestionsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='vstep-test@example.com',
            password='testpass123'
        )
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')
        Flashcard.objects.create(user=self.user, deck=self.deck, word='hello')
        Flashcard.objects.create(user=self.user, deck=self.deck, word='world')

    def test_vstep_suggestions_requires_login(self):
        """Unauthenticated requests should be redirected."""
        response = self.client.post(reverse('api_vstep_suggestions'))
        self.assertNotEqual(response.status_code, 200)

    def test_vstep_suggestions_requires_post(self):
        """GET requests should return 405."""
        self.client.login(email='vstep-test@example.com', password='testpass123')
        response = self.client.get(reverse('api_vstep_suggestions'))
        self.assertEqual(response.status_code, 405)

    @patch('vocabulary.views.get_vstep_suggestions')
    def test_vstep_suggestions_returns_words(self, mock_fn):
        """Successful request returns JSON with words array."""
        mock_fn.return_value = ['phenomenon', 'substantial']
        self.client.login(email='vstep-test@example.com', password='testpass123')
        response = self.client.post(reverse('api_vstep_suggestions'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['words'], ['phenomenon', 'substantial'])

    @patch('vocabulary.views.get_vstep_suggestions')
    def test_vstep_suggestions_excludes_existing_words(self, mock_fn):
        """The view passes the user's existing words to the service."""
        mock_fn.return_value = ['phenomenon']
        self.client.login(email='vstep-test@example.com', password='testpass123')
        self.client.post(reverse('api_vstep_suggestions'))
        called_words = mock_fn.call_args[0][0]
        self.assertIn('hello', called_words)
        self.assertIn('world', called_words)

    @patch('vocabulary.views.get_vstep_suggestions')
    def test_vstep_suggestions_handles_llm_error(self, mock_fn):
        """LLM failure returns error JSON."""
        mock_fn.side_effect = Exception('LLM down')
        self.client.login(email='vstep-test@example.com', password='testpass123')
        response = self.client.post(reverse('api_vstep_suggestions'))
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test vocabulary.tests.VSTEPSuggestionsViewTest -v 2`
Expected: FAIL — `NoReverseMatch: Reverse for 'api_vstep_suggestions' not found`

- [ ] **Step 3: Add URL route**

Add the following line to `vocabulary/api_urls.py`, inside the `urlpatterns` list, after the existing `api/ai/word-examples/` entry (line 67):

```python
    path('api/ai/vstep-suggestions/', views.api_vstep_suggestions, name='api_vstep_suggestions'),
```

- [ ] **Step 4: Add the view to `vocabulary/views.py`**

Add this import near the top of `views.py`, next to the existing `from .ai_service import ...` (there isn't one currently — the view imports inline). Actually, add a top-level import after the existing imports block (around line 24):

Actually — the existing pattern (see `api_ai_word_examples` at line 2535) imports inline: `from .ai_service import get_word_examples`. Follow the same pattern.

Add the following view after `api_ai_word_examples` (after line 2545 in `vocabulary/views.py`):

```python
@login_required
@require_POST
def api_vstep_suggestions(request):
    """Return 20 AI-generated VSTEP vocabulary words the user doesn't already know."""
    try:
        existing_words = list(
            Flashcard.objects.filter(user=request.user).values_list('word', flat=True)
        )
        from .ai_service import get_vstep_suggestions
        words = get_vstep_suggestions(existing_words)
        return JsonResponse({'success': True, 'words': words})
    except requests.exceptions.ConnectionError:
        return JsonResponse(
            {'success': False, 'error': 'Cannot connect to LLM service. Make sure it is running.'},
            status=503,
        )
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test vocabulary.tests.VSTEPSuggestionsViewTest -v 2`
Expected: 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add vocabulary/views.py vocabulary/api_urls.py vocabulary/tests.py
git commit -m "feat(vstep): add api_vstep_suggestions endpoint"
```

---

### Task 3: Frontend — i18n texts in context_processors.py

**Files:**
- Modify: `vocabulary/context_processors.py` (add entries to the `'en'` dict)

- [ ] **Step 1: Add i18n text entries**

In `vocabulary/context_processors.py`, find the `'en'` dict inside `legacy_translations`. Add the following entries after the `'yes_replace_all'` entry (around line 349, before the `# Blacklist Management` comment):

```python
            # VSTEP Vocabulary Suggestions
            'vstep_suggestion_title': 'VSTEP Vocabulary Suggestions',
            'vstep_suggestion_description': 'Auto-generate 20 common VSTEP exam words you haven\'t learned yet',
            'vstep_suggest_button': 'Suggest 20 VSTEP Words',
            'vstep_processing_text': 'Generating VSTEP suggestions...',
            'vstep_error_message': 'Failed to generate VSTEP suggestions. Please try again.',
            'vstep_connection_error': 'Cannot connect to AI service. Make sure it is running.',
```

- [ ] **Step 2: Verify the server starts without errors**

Run: `python manage.py check`
Expected: `System check identified no issues.`

- [ ] **Step 3: Commit**

```bash
git add vocabulary/context_processors.py
git commit -m "feat(vstep): add i18n text entries for VSTEP suggestion UI"
```

---

### Task 4: Frontend — CSS, HTML, and JS on the `/add` page

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html`

- [ ] **Step 1: Add CSS styles**

In `add_flashcard.html`, find the responsive media query section. Add the following CSS **before** the closing `</style>` tag (around line 762, before the `@media` block at line 738). Actually — add it right before the `/* Full-screen loading overlay */` comment (line 676):

```css
    /* VSTEP Suggestion Section */
    .vstep-suggestion-section {
      background: linear-gradient(135deg, rgba(106, 108, 255, 0.08), rgba(142, 68, 173, 0.08));
      border: 1px solid rgba(106, 108, 255, 0.3);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 25px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    .vstep-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;
    }

    .vstep-header h3 {
      margin: 0;
      color: var(--text-main);
      font-size: 1.2em;
      font-weight: 600;
    }

    .vstep-description {
      color: var(--text-muted);
      font-size: 0.9em;
      margin-bottom: 15px;
    }

    .vstep-suggest-btn {
      background: linear-gradient(135deg, #8e44ad, #6a6cff);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 12px 24px;
      font-size: 1em;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .vstep-suggest-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(142, 68, 173, 0.4);
    }

    .vstep-suggest-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
    }

    #vstep-processing {
      margin-top: 10px;
    }
```

- [ ] **Step 2: Add HTML section**

In `add_flashcard.html`, find the closing `</div>` of the quick-add section (line 801). Add the following **after** it and **before** the `<div class="flashcard-container"` (line 803):

```html
  <!-- VSTEP Vocabulary Suggestions Section -->
  <div class="vstep-suggestion-section">
    <div class="vstep-header">
      <span style="font-size: 1.3em;">🎓</span>
      <h3>{{ manual_texts.vstep_suggestion_title }}</h3>
    </div>
    <p class="vstep-description">{{ manual_texts.vstep_suggestion_description }}</p>
    <button id="vstep-suggest-btn" class="vstep-suggest-btn">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
      </svg>
      {{ manual_texts.vstep_suggest_button }}
    </button>
    <div id="vstep-processing" class="processing-indicator">
      <div class="spinner"></div>
      <span id="vstep-processing-text">{{ manual_texts.vstep_processing_text }}</span>
    </div>
  </div>
```

- [ ] **Step 3: Add JavaScript logic**

In `add_flashcard.html`, find the Quick Add event listener block (around line 1812, `if(generateCardsBtn) {`). Add the following **before** that block (before line 1811):

```javascript
    // VSTEP Suggestion elements
    const vstepSuggestBtn = document.getElementById('vstep-suggest-btn');
    const vstepProcessing = document.getElementById('vstep-processing');
    const vstepProcessingText = document.getElementById('vstep-processing-text');

    if (vstepSuggestBtn) {
        vstepSuggestBtn.addEventListener('click', async () => {
            const selectedDeckId = deckSelector.value;
            if (!selectedDeckId || selectedDeckId === 'new_deck') {
                Notify.warning('{{ manual_texts.select_deck_before_adding }}');
                return;
            }

            vstepSuggestBtn.disabled = true;
            vstepProcessing.classList.add('active');
            vstepProcessingText.textContent = '{{ manual_texts.vstep_processing_text }}';

            try {
                const response = await fetch("{% url 'api_vstep_suggestions' %}", {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken(),
                        'Content-Type': 'application/json',
                    },
                });

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error(data.error || '{{ manual_texts.vstep_error_message }}');
                }

                if (!data.words || data.words.length === 0) {
                    Notify.info('No new VSTEP words found. You may have learned them all!');
                    return;
                }

                // Check if there are existing cards with content
                const existingCards = flashcardContainer.querySelectorAll('.flashcard-section');
                const hasContent = Array.from(existingCards).some(card => {
                    const termInput = card.querySelector('.term-input');
                    return termInput && termInput.value.trim().length > 0;
                });

                if (hasContent && existingCards.length > 0) {
                    const confirmed = await Notify.confirm({
                        type: 'warning',
                        title: '{{ manual_texts.replace_existing_cards }}',
                        html: `{{ manual_texts.replace_cards_confirmation_html }}`.replace('{count}', data.words.length),
                        confirmText: '{{ manual_texts.yes_replace_all }}',
                        cancelText: '{{ manual_texts.cancel }}',
                    });
                    if (!confirmed) return;
                }

                await generateCardsFromWords(data.words);
                Notify.success(`Generated ${data.words.length} VSTEP vocabulary cards!`);

            } catch (error) {
                console.error('VSTEP suggestion error:', error);
                Notify.error(error.message || '{{ manual_texts.vstep_error_message }}');
            } finally {
                vstepSuggestBtn.disabled = false;
                vstepProcessing.classList.remove('active');
            }
        });
    }
```

- [ ] **Step 4: Start the dev server and test in browser**

Run: `python manage.py runserver`

Manual test checklist:
1. Navigate to `/add/`
2. Verify the "VSTEP Vocabulary Suggestions" section appears below Quick Add
3. Verify the "Suggest 20 VSTEP Words" button is visible with gradient styling
4. Select a deck, click the button
5. Verify loading spinner appears
6. Verify 20 flashcard cards are generated (or error notification if LLM is unreachable)
7. Verify clicking without selecting a deck shows warning notification

- [ ] **Step 5: Commit**

```bash
git add vocabulary/templates/vocabulary/add_flashcard.html
git commit -m "feat(vstep): add VSTEP suggestion button UI and JS on /add page"
```

---

### Task 5: Run all tests

- [ ] **Step 1: Run the full test suite**

Run: `python manage.py test vocabulary.tests -v 2`
Expected: All tests PASS, including the new VSTEP tests.

- [ ] **Step 2: Final commit (if any fixes needed)**

If all tests pass, no action needed. If fixes were required, commit them:

```bash
git add -A
git commit -m "fix(vstep): address test failures from integration"
```
