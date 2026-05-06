# Example Sentence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an auto-generated example sentence to each flashcard, shown on /add, flashcard detail, and study session.

**Architecture:** Add `example_sentence` + `example_source` fields to `Flashcard`. `word_details_service.get_word_details()` already returns `example_en` from Cambridge — add LLM fallback when empty and surface both new fields in the returned dict. Wire through `save_flashcards` API, `api_next_question`, the add page UI, study session, and detail view. A management command backfills existing cards.

**Tech Stack:** Django ORM, `requests` (LLM via LiteLLM proxy), Django management commands, vanilla JS.

---

## File Map

| File | Action | What changes |
|---|---|---|
| `vocabulary/models.py` | Modify | Add `example_sentence`, `example_source` fields |
| `vocabulary/word_details_service.py` | Modify | Add `_generate_example_llm()`, `_enrich_example()`, call from `get_word_details()` |
| `vocabulary/views.py` | Modify | `save_flashcards` saves new fields; `api_next_question` includes `example_sentence` in payload |
| `vocabulary/templates/vocabulary/add_flashcard.html` | Modify | Add example textarea, populate in `updateCardUI`, append in formData |
| `vocabulary/templates/vocabulary/study.html` | Modify | Add `#cardExample` div |
| `static/js/study.js` | Modify | Show `#cardExample` on answer reveal, hide on new question |
| `vocabulary/templates/vocabulary/deck_detail.html` | Modify | Show example after definitions |
| `vocabulary/management/commands/populate_examples.py` | Create | Backfill command |
| `tests/test_example_sentence.py` | Create | Tests for service, API, command |

---

## Task 1: Add model fields + migration

**Files:**
- Modify: `vocabulary/models.py`
- Run: `python manage.py makemigrations && python manage.py migrate`
- Test: `tests/test_example_sentence.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_example_sentence.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from vocabulary.models import Flashcard, Deck

User = get_user_model()

class ExampleSentenceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.com', password='pass')
        self.deck = Deck.objects.create(user=self.user, name='Test')

    def test_flashcard_has_example_sentence_field(self):
        card = Flashcard.objects.create(user=self.user, deck=self.deck, word='resilient')
        card.example_sentence = 'She is a resilient person.'
        card.example_source = 'cambridge'
        card.save()
        card.refresh_from_db()
        self.assertEqual(card.example_sentence, 'She is a resilient person.')
        self.assertEqual(card.example_source, 'cambridge')

    def test_example_fields_nullable(self):
        card = Flashcard.objects.create(user=self.user, deck=self.deck, word='brave')
        self.assertIsNone(card.example_sentence)
        self.assertIsNone(card.example_source)
```

- [ ] **Step 2: Run test — expect FAIL**

```
python manage.py test tests.test_example_sentence.ExampleSentenceModelTest -v 2
```

Expected: `AttributeError` or migration error since fields don't exist yet.

- [ ] **Step 3: Add fields to model**

In `vocabulary/models.py`, after `cefr_level_auto` (line ~49), add:

```python
    example_sentence = models.TextField(blank=True, null=True, help_text="Example sentence showing word in context")
    example_source = models.CharField(max_length=10, blank=True, null=True, help_text="Source: 'cambridge', 'llm', or 'manual'")
```

- [ ] **Step 4: Create and apply migration**

```
python manage.py makemigrations vocabulary --name add_example_sentence
python manage.py migrate
```

Expected output: `Applying vocabulary.XXXX_add_example_sentence... OK`

- [ ] **Step 5: Run test — expect PASS**

```
python manage.py test tests.test_example_sentence.ExampleSentenceModelTest -v 2
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add vocabulary/models.py vocabulary/migrations/
git add tests/test_example_sentence.py
git commit -m "feat: add example_sentence and example_source fields to Flashcard"
```

---

## Task 2: word_details_service — LLM fallback for examples

**Files:**
- Modify: `vocabulary/word_details_service.py`
- Test: `tests/test_example_sentence.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_example_sentence.py`:

```python
from unittest.mock import patch, MagicMock
from vocabulary.word_details_service import get_word_details

class ExampleSentenceServiceTest(TestCase):
    @patch('vocabulary.word_details_service._cambridge_fetcher')
    @patch('vocabulary.word_details_service._translator')
    def test_cambridge_example_used_when_present(self, mock_translator, mock_fetcher):
        from vocabulary.audio_service import CambridgeWordData
        from vocabulary.llm_translator import TranslationResult
        mock_fetcher.fetch_word_data.return_value = CambridgeWordData(
            word='resilient',
            definition_en='able to recover quickly',
            example_en='She bounced back quickly.',
            part_of_speech='adjective',
        )
        mock_translator.translate_definition.return_value = TranslationResult(
            definition_vi='có khả năng phục hồi', short_meaning_vi='phục hồi', source='llm'
        )
        result = get_word_details('resilient')
        self.assertEqual(result['example_sentence'], 'She bounced back quickly.')
        self.assertEqual(result['example_source'], 'cambridge')

    @patch('vocabulary.word_details_service._generate_example_llm')
    @patch('vocabulary.word_details_service._cambridge_fetcher')
    @patch('vocabulary.word_details_service._translator')
    def test_llm_fallback_when_cambridge_has_no_example(self, mock_translator, mock_fetcher, mock_llm):
        from vocabulary.audio_service import CambridgeWordData
        from vocabulary.llm_translator import TranslationResult
        mock_fetcher.fetch_word_data.return_value = CambridgeWordData(
            word='test',
            definition_en='a procedure to assess',
            example_en='',  # empty — LLM should be called
            part_of_speech='noun',
        )
        mock_translator.translate_definition.return_value = TranslationResult(
            definition_vi='bài kiểm tra', short_meaning_vi='kiểm tra', source='llm'
        )
        mock_llm.return_value = 'The teacher gave a test on Friday.'
        result = get_word_details('test')
        self.assertEqual(result['example_sentence'], 'The teacher gave a test on Friday.')
        self.assertEqual(result['example_source'], 'llm')
        mock_llm.assert_called_once_with('test', 'a procedure to assess')
```

- [ ] **Step 2: Run test — expect FAIL**

```
python manage.py test tests.test_example_sentence.ExampleSentenceServiceTest -v 2
```

Expected: `KeyError: 'example_sentence'` — field not yet in service output.

- [ ] **Step 3: Implement `_generate_example_llm` and `_enrich_example`**

In `vocabulary/word_details_service.py`, add after the imports section (after line 11):

```python
def _generate_example_llm(word: str, definition_en: str) -> str:
    """Generate an example sentence for the word via LLM. Returns empty string on failure."""
    try:
        import requests as _requests
        from django.conf import settings as _settings
        response = _requests.post(
            _settings.LLM_URL,
            json={
                "model": _settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an English teacher. Respond with exactly one natural example sentence and nothing else. No quotation marks."},
                    {"role": "user", "content": f"Write one natural English example sentence for the word '{word}' meaning: {definition_en}"},
                ],
                "temperature": 0.7,
                "max_tokens": 80,
            },
            headers={"Authorization": f"Bearer {_settings.LLM_API_KEY}"},
            timeout=_settings.LLM_TIMEOUT,
            verify=False,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"LLM example generation failed for '{word}': {e}")
        return ""


def _enrich_example(word: str, result: dict) -> None:
    """Add example_sentence and example_source to result dict in-place."""
    cambridge_example = result.get("example_en", "")
    if cambridge_example:
        result["example_sentence"] = cambridge_example
        result["example_source"] = "cambridge"
    else:
        generated = _generate_example_llm(word, result.get("definition_en", ""))
        result["example_sentence"] = generated
        result["example_source"] = "llm" if generated else ""
```

- [ ] **Step 4: Call `_enrich_example` in `get_word_details`**

Replace the two `return` statements in `get_word_details` (lines 24 and 29) so they call `_enrich_example` before returning:

```python
def get_word_details(word: str) -> dict:
    """Fetch word details using Cambridge Dictionary first, with dictionaryapi.dev fallback."""
    if not word or not word.strip():
        return {"error": "No word provided"}

    word = word.strip()

    cambridge_data = _fetch_from_cambridge(word)
    if cambridge_data:
        translation = _translate(cambridge_data)
        result = _build_cambridge_response(cambridge_data, translation)
        _enrich_example(word, result)
        return result

    fallback_data = _fetch_from_dictionary_api(word)
    if fallback_data:
        translation = _translate_fallback(word, fallback_data)
        result = _build_fallback_response(fallback_data, translation)
        _enrich_example(word, result)
        return result

    return {"error": f"Không tìm thấy từ '{word}'."}
```

- [ ] **Step 5: Run tests — expect PASS**

```
python manage.py test tests.test_example_sentence.ExampleSentenceServiceTest -v 2
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add vocabulary/word_details_service.py tests/test_example_sentence.py
git commit -m "feat: add LLM example generation to word_details_service"
```

---

## Task 3: save_flashcards API — persist example_sentence

**Files:**
- Modify: `vocabulary/views.py` (lines ~964-983, `save_flashcards`)
- Test: `tests/test_example_sentence.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_example_sentence.py`:

```python
import json
from django.test import Client
from django.urls import reverse

class SaveFlashcardsExampleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='save@test.com', password='pass')
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')
        self.client.login(email='save@test.com', password='pass')

    def test_save_flashcard_persists_example(self):
        response = self.client.post(reverse('save_flashcards'), {
            'deck_id': self.deck.id,
            'flashcards-0-word': 'resilient',
            'flashcards-0-english_definition': 'able to recover quickly',
            'flashcards-0-vietnamese_definition': 'có khả năng phục hồi',
            'flashcards-0-example_sentence': 'She bounced back quickly.',
            'flashcards-0-example_source': 'cambridge',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        card = Flashcard.objects.get(user=self.user, word='resilient')
        self.assertEqual(card.example_sentence, 'She bounced back quickly.')
        self.assertEqual(card.example_source, 'cambridge')
```

- [ ] **Step 2: Run test — expect FAIL**

```
python manage.py test tests.test_example_sentence.SaveFlashcardsExampleTest -v 2
```

Expected: Test passes the save but `card.example_sentence` is `None` — field not wired yet.

- [ ] **Step 3: Add example fields to save_flashcards defaults**

In `vocabulary/views.py`, inside `save_flashcards`, find the `defaults` dict (around line 964) and add the two new fields:

```python
            defaults = {
                'phonetic': card_data.get('phonetic'),
                'part_of_speech': card_data.get('part_of_speech'),
                'audio_url': card_data.get('audio_url'),
                'deck': deck,
                'example_sentence': card_data.get('example_sentence') or None,
                'example_source': card_data.get('example_source') or None,
            }
```

- [ ] **Step 4: Run test — expect PASS**

```
python manage.py test tests.test_example_sentence.SaveFlashcardsExampleTest -v 2
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add vocabulary/views.py tests/test_example_sentence.py
git commit -m "feat: save example_sentence and example_source in save_flashcards"
```

---

## Task 4: api_next_question — include example_sentence in payload

**Files:**
- Modify: `vocabulary/views.py` (`api_next_question`, around line 497)
- Test: `tests/test_example_sentence.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_example_sentence.py`:

```python
class ApiNextQuestionExampleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='study@test.com', password='pass')
        self.deck = Deck.objects.create(user=self.user, name='Study Deck')
        self.card = Flashcard.objects.create(
            user=self.user, deck=self.deck, word='resilient',
            example_sentence='She bounced back quickly.',
            example_source='cambridge',
        )
        from vocabulary.models import Definition
        Definition.objects.create(
            flashcard=self.card,
            english_definition='able to recover quickly',
            vietnamese_definition='có khả năng phục hồi',
        )
        self.client.login(email='study@test.com', password='pass')

    def test_next_question_includes_example_sentence(self):
        response = self.client.post(
            reverse('api_next_question'),
            data=json.dumps({'deck_ids': [self.deck.id], 'study_mode': 'decks', 'seen_card_ids': []}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['done'])
        self.assertIn('example_sentence', data['question'])
        self.assertEqual(data['question']['example_sentence'], 'She bounced back quickly.')
```

- [ ] **Step 2: Run test — expect FAIL**

```
python manage.py test tests.test_example_sentence.ApiNextQuestionExampleTest -v 2
```

Expected: `KeyError: 'example_sentence'` — field not yet in payload.

- [ ] **Step 3: Add `example_sentence` to payload**

In `vocabulary/views.py` `api_next_question`, find the `payload['question']` dict (around line 497–501) and add `example_sentence`:

```python
    payload = {
        'done': False,
        'question': {
            'id': card.id, 'word': card.word, 'phonetic': card.phonetic,
            'part_of_speech': card.part_of_speech, 'image_url': card.image.url if card.image else card.related_image_url,
            'audio_url': card.audio_url, 'definitions': defs, 'cefr_level': card.cefr_level,
            'example_sentence': card.example_sentence or '',
        }
    }
```

- [ ] **Step 4: Run test — expect PASS**

```
python manage.py test tests.test_example_sentence.ApiNextQuestionExampleTest -v 2
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add vocabulary/views.py tests/test_example_sentence.py
git commit -m "feat: include example_sentence in api_next_question payload"
```

---

## Task 5: /add page UI — example textarea + JS

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html`

- [ ] **Step 1: Add example textarea HTML after Vietnamese block**

In `add_flashcard.html`, after line 1165 (`</div>` closing `vietnamese-block-container`), insert before the closing `</div>` on line 1166:

```html
            <!-- Example Sentence -->
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

- [ ] **Step 2: Populate example in `updateCardUI` JS function**

In `add_flashcard.html`, inside the `updateCardUI(card, data)` function (around line 1561), after the Vietnamese definition populate block (after `vietnameseTextarea.value = data.definition_vi`), add:

```javascript
        // Example sentence
        const exampleTextarea = card.querySelector('.example-textarea');
        const exampleSourceInput = card.querySelector('.example-source-input');
        const exampleBadge = card.querySelector('.example-auto-badge');
        if (exampleTextarea && data.example_sentence) {
            exampleTextarea.value = data.example_sentence;
            if (exampleSourceInput) exampleSourceInput.value = data.example_source || '';
            if (exampleBadge) exampleBadge.style.display = 'inline';
        }
```

- [ ] **Step 3: Track manual edits to update source**

After the code above (still inside `updateCardUI`), add:

```javascript
        if (exampleTextarea) {
            exampleTextarea.addEventListener('input', () => {
                if (exampleSourceInput) exampleSourceInput.value = 'manual';
                if (exampleBadge) exampleBadge.style.display = 'none';
            }, { once: true });
        }
```

- [ ] **Step 4: Clear example in `resetCardUI`**

In the `resetCardUI(card)` function, add:

```javascript
        const exampleTextarea = card.querySelector('.example-textarea');
        const exampleSourceInput = card.querySelector('.example-source-input');
        const exampleBadge = card.querySelector('.example-auto-badge');
        if (exampleTextarea) exampleTextarea.value = '';
        if (exampleSourceInput) exampleSourceInput.value = '';
        if (exampleBadge) exampleBadge.style.display = 'none';
```

- [ ] **Step 5: Append example fields to formData on save**

In the `formData.append` block (around line 2371), after the `vietnamese_definition` line, add:

```javascript
                formData.append(`flashcards-${idx}-example_sentence`, card.querySelector('.example-textarea')?.value.trim() || '');
                formData.append(`flashcards-${idx}-example_source`, card.querySelector('.example-source-input')?.value || '');
```

- [ ] **Step 6: Start dev server and manually test /add**

```
python manage.py runserver
```

1. Navigate to `/add`
2. Type a word (e.g. "resilient") — verify example textarea auto-fills
3. Edit the example — verify badge disappears
4. Save — check DB: `python manage.py shell -c "from vocabulary.models import Flashcard; c = Flashcard.objects.get(word='resilient'); print(c.example_sentence, c.example_source)"`

- [ ] **Step 7: Commit**

```bash
git add vocabulary/templates/vocabulary/add_flashcard.html
git commit -m "feat: add example sentence textarea to /add page with auto-populate"
```

---

## Task 6: Study session — show example after answer reveal

**Files:**
- Modify: `vocabulary/templates/vocabulary/study.html`
- Modify: `static/js/study.js`

- [ ] **Step 1: Add `#cardExample` div to study.html**

In `study.html`, after line 865 (`</div>` closing `#detailedFeedbackArea`) and before `</div>` closing `#answerSection` (line 866), add:

```html
        <div id="cardExample" class="card-example" style="display:none; margin-top:12px; padding:10px 14px; border-left:3px solid var(--primary-color); background:rgba(106,108,255,0.08); border-radius:0 6px 6px 0;">
          <div style="font-size:10px; text-transform:uppercase; letter-spacing:1px; color:var(--text-muted); margin-bottom:4px;">Example</div>
          <div id="cardExampleText" style="font-style:italic; color:var(--text-main); line-height:1.6;"></div>
        </div>
```

- [ ] **Step 2: Show example in study.js after answer reveal**

In `static/js/study.js`, after `showCefrLevelAfterAnswer()` call (around line 1650), add:

```javascript
    // Show example sentence if available
    const cardExampleEl = document.getElementById("cardExample");
    const cardExampleTextEl = document.getElementById("cardExampleText");
    if (cardExampleEl && cardExampleTextEl && currentQuestion.example_sentence) {
      cardExampleTextEl.textContent = currentQuestion.example_sentence;
      cardExampleEl.style.display = "block";
    } else if (cardExampleEl) {
      cardExampleEl.style.display = "none";
    }
```

- [ ] **Step 3: Hide example on new question load**

In `study.js`, in the block that hides grade buttons for a new question (around line 1128–1136), add:

```javascript
    const cardExampleEl = document.getElementById("cardExample");
    if (cardExampleEl) {
      cardExampleEl.style.display = "none";
    }
```

- [ ] **Step 4: Start dev server and manually test study session**

```
python manage.py runserver
```

1. Navigate to `/study`
2. Answer a question — verify example appears below definitions
3. Click next — verify example disappears for new question

- [ ] **Step 5: Commit**

```bash
git add vocabulary/templates/vocabulary/study.html static/js/study.js
git commit -m "feat: show example sentence after answer reveal in study session"
```

---

## Task 7: Flashcard detail view — show example

**Files:**
- Modify: `vocabulary/templates/vocabulary/deck_detail.html`

- [ ] **Step 1: Add example section after definitions loop**

In `deck_detail.html`, after line 325 (`{% endfor %}` closing the definitions loop), before the AI examples button (line 327), add:

```html
          {% if card.example_sentence %}
          <div class="mt-3" style="padding:8px 12px; border-left:3px solid rgba(106,108,255,0.6); background:rgba(106,108,255,0.06); border-radius:0 6px 6px 0;">
            <div class="text-xs font-medium mb-1" style="color:#7c7cbb; text-transform:uppercase; letter-spacing:0.05em;">Example</div>
            <div class="text-sm text-gray-300" style="font-style:italic; line-height:1.6;">{{ card.example_sentence }}</div>
          </div>
          {% endif %}
```

- [ ] **Step 2: Start dev server and manually test detail view**

```
python manage.py runserver
```

Navigate to any deck detail page — verify example appears under definitions for cards that have one.

- [ ] **Step 3: Commit**

```bash
git add vocabulary/templates/vocabulary/deck_detail.html
git commit -m "feat: show example sentence on flashcard detail view"
```

---

## Task 8: Management command — populate_examples backfill

**Files:**
- Create: `vocabulary/management/commands/populate_examples.py`
- Test: `tests/test_example_sentence.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_example_sentence.py`:

```python
from io import StringIO
from django.core.management import call_command

class PopulateExamplesCommandTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='cmd@test.com', password='pass')
        self.deck = Deck.objects.create(user=self.user, name='CMD Deck')
        self.card_no_example = Flashcard.objects.create(
            user=self.user, deck=self.deck, word='brave',
            example_sentence=None,
        )
        self.card_has_example = Flashcard.objects.create(
            user=self.user, deck=self.deck, word='kind',
            example_sentence='She is a kind person.',
            example_source='cambridge',
        )

    @patch('vocabulary.word_details_service.get_word_details')
    def test_dry_run_prints_words_without_writing(self, mock_get):
        mock_get.return_value = {'example_sentence': 'She was brave.', 'example_source': 'llm'}
        out = StringIO()
        call_command('populate_examples', '--dry-run', stdout=out)
        self.card_no_example.refresh_from_db()
        self.assertIsNone(self.card_no_example.example_sentence)
        self.assertIn('brave', out.getvalue())

    @patch('vocabulary.word_details_service.get_word_details')
    def test_fills_cards_without_example(self, mock_get):
        mock_get.return_value = {'example_sentence': 'She was brave.', 'example_source': 'llm'}
        call_command('populate_examples')
        self.card_no_example.refresh_from_db()
        self.card_has_example.refresh_from_db()
        self.assertEqual(self.card_no_example.example_sentence, 'She was brave.')
        # card with existing example should NOT be overwritten
        self.assertEqual(self.card_has_example.example_sentence, 'She is a kind person.')

    @patch('vocabulary.word_details_service.get_word_details')
    def test_force_flag_overwrites_existing(self, mock_get):
        mock_get.return_value = {'example_sentence': 'New sentence.', 'example_source': 'llm'}
        call_command('populate_examples', '--force')
        self.card_has_example.refresh_from_db()
        self.assertEqual(self.card_has_example.example_sentence, 'New sentence.')
```

- [ ] **Step 2: Run test — expect FAIL**

```
python manage.py test tests.test_example_sentence.PopulateExamplesCommandTest -v 2
```

Expected: `CommandError` or import error — command doesn't exist yet.

- [ ] **Step 3: Create the management command**

Create `vocabulary/management/commands/populate_examples.py`:

```python
"""
Management command to populate example sentences for all flashcards.
Uses word_details_service (Cambridge first, LLM fallback).
"""
from django.core.management.base import BaseCommand
from vocabulary.models import Flashcard
from vocabulary.word_details_service import get_word_details


class Command(BaseCommand):
    help = 'Populate example sentences for flashcards that are missing them'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
            help='Show what would be updated without writing to DB')
        parser.add_argument('--force', action='store_true',
            help='Re-generate examples even if already present')
        parser.add_argument('--limit', type=int,
            help='Process at most N flashcards')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        limit = options['limit']

        qs = Flashcard.objects.all().order_by('id')
        if not force:
            qs = qs.filter(example_sentence__isnull=True)
        if limit:
            qs = qs[:limit]

        cards = list(qs)
        total = len(cards)
        self.stdout.write(f'Found {total} flashcard(s) to process')

        if dry_run:
            for card in cards:
                self.stdout.write(f'  [dry-run] {card.word}')
            self.stdout.write(f'\nDry run complete. Would process {total} card(s).')
            return

        success, fail = 0, 0
        for i, card in enumerate(cards, 1):
            try:
                data = get_word_details(card.word)
                example = data.get('example_sentence', '')
                source = data.get('example_source', '')
                if example:
                    card.example_sentence = example
                    card.example_source = source
                    card.save(update_fields=['example_sentence', 'example_source'])
                    success += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  [{i}/{total}] {card.word} → {source}')
                    )
                else:
                    fail += 1
                    self.stdout.write(
                        self.style.WARNING(f'  [{i}/{total}] {card.word} → no example returned')
                    )
            except Exception as e:
                fail += 1
                self.stdout.write(
                    self.style.ERROR(f'  [{i}/{total}] {card.word} → ERROR: {e}')
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated {success}/{total}. Failed/skipped: {fail}'
        ))
```

- [ ] **Step 4: Run tests — expect PASS**

```
python manage.py test tests.test_example_sentence.PopulateExamplesCommandTest -v 2
```

Expected: `OK`

- [ ] **Step 5: Run a dry-run against real DB**

```
python manage.py populate_examples --dry-run --limit 5
```

Expected: prints 5 word names with `[dry-run]` prefix, no DB writes.

- [ ] **Step 6: Commit**

```bash
git add vocabulary/management/commands/populate_examples.py tests/test_example_sentence.py
git commit -m "feat: add populate_examples management command for backfilling"
```

---

## Task 9: Run all tests + full integration check

- [ ] **Step 1: Run all tests**

```
python manage.py test
```

Expected: All tests pass, no regressions.

- [ ] **Step 2: Run populate_examples on a small batch**

```
python manage.py populate_examples --limit 10
```

Verify 10 cards get example sentences written to DB:

```
python manage.py shell -c "from vocabulary.models import Flashcard; print(list(Flashcard.objects.exclude(example_sentence=None).values_list('word','example_source')[:10]))"
```

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "feat: complete example sentence feature — model, service, API, UI, backfill"
```
