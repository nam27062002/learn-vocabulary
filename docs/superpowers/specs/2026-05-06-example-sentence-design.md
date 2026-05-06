# Example Sentence Feature — Design Spec

**Date:** 2026-05-06  
**Status:** Approved

---

## Overview

Add an example sentence to each flashcard showing how the word is used in context. Examples are auto-generated (Cambridge first, LLM fallback) and displayed everywhere: the /add page, flashcard detail view, and study sessions.

---

## 1. Data Model

Add two fields to `Flashcard` (`vocabulary/models.py`):

```python
example_sentence = models.TextField(blank=True, null=True)
example_source   = models.CharField(max_length=10, blank=True, null=True)
# source values: 'cambridge' | 'llm' | 'manual'
```

`example_source` tracks provenance — useful for backfill targeting and debugging.

Migration required: `python manage.py makemigrations && python manage.py migrate`.

---

## 2. word_details_service.py

Cambridge scraper already returns an `example` field. Update `get_word_details()` to:

1. Extract Cambridge example if present → `example_source = 'cambridge'`
2. If not present → call LLM with prompt:
   ```
   Write one natural example sentence for the word '{word}' meaning '{definition}'.
   Return only the sentence, no quotes, no extra text.
   ```
   → `example_source = 'llm'`
3. Include `example_sentence` and `example_source` in the returned dict.

LLM call reuses the existing `LiteLLMTranslator` infrastructure (same base URL, model, API key from settings).

---

## 3. save_flashcards API

Frontend sends `example_sentence` and `example_source` in the JSON payload alongside existing fields. The `save_flashcards` view saves both fields to the `Flashcard` instance.

If user edited the auto-generated text on the /add page, frontend sends `example_source = 'manual'`.

---

## 4. /add Page UI

In the card editor template (`add_flashcard.html`), after the Vietnamese definition field, add:

- Label: **"Example Sentence"** with a small `✦ auto-generated` badge (green)
- A `<textarea>` pre-populated from the word details API response
- User can edit before saving
- Styling: green accent border-left, consistent with the card editor aesthetic

---

## 5. Study Session UI

After the user answers (correct or incorrect), the answer reveal section shows:

- Word + definition (existing)
- Example sentence below a divider, with:
  - Small uppercase label: `EXAMPLE`
  - Italic text with green border-left accent (correct) or red (incorrect)
- Always shown regardless of correct/incorrect outcome

No change to the difficulty rating buttons (Again / Hard / Good / Easy).

---

## 6. Flashcard Detail View

On the flashcard detail page, add an **Example** section below the definitions:

- Read-only
- Italic text, border-left accent, same visual style as study session
- Only rendered if `example_sentence` is not empty

---

## 7. Management Command — populate_examples

New file: `vocabulary/management/commands/populate_examples.py`

```
python manage.py populate_examples [--limit N] [--force] [--dry-run]
```

| Flag | Behavior |
|---|---|
| `--limit N` | Process at most N flashcards |
| `--force` | Re-generate even if example already exists |
| `--dry-run` | Print actions without writing to DB |

**Logic:**
1. Query all `Flashcard` where `example_sentence` is null (or all if `--force`)
2. For each card: call `get_word_details(word)` → extract `example_sentence`
3. Cambridge hit → save with `source='cambridge'`; LLM fallback → `source='llm'`
4. On LLM error: log warning, skip card, continue batch (no crash)
5. Print progress: `[50/312] resilient → cambridge`

---

## Out of Scope

- Multiple example sentences per flashcard (1 is sufficient)
- User-facing "regenerate example" button (can be added later)
- Example sentences in quiz/input mode questions
