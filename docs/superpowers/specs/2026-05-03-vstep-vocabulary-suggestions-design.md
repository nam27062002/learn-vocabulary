# VSTEP Vocabulary Suggestions Feature

## Summary

Add a one-click "VSTEP Suggestions" button to the `/add` flashcard page that uses the LLM proxy to generate 20 high-frequency VSTEP exam words the user doesn't already know, then auto-populates flashcard cards for review and saving.

## Backend

### New endpoint: `POST /api/ai/vstep-suggestions/`

**Handler:** `api_vstep_suggestions` in `vocabulary/views.py`

**Logic:**
1. Query all words the current user already has: `Flashcard.objects.filter(user=request.user).values_list('word', flat=True)`
2. Build LLM prompt requesting 20 VSTEP words (B1-C1), prioritized by exam frequency, excluding the user's existing words
3. Call LLM proxy at `settings.LLM_URL` with `settings.LLM_MODEL`
4. Parse the JSON array response; validate each entry is a string
5. Double-check: filter out any words that exist in the user's database (case-insensitive)
6. Return `{"success": true, "words": [...]}`

**LLM Prompt:**
```
You are a VSTEP exam preparation expert. Give me exactly 20 English vocabulary words that are most commonly tested in VSTEP exams (levels B1 to C1).

Rules:
- Prioritize words by frequency of appearance in VSTEP exams (most common first)
- Focus on academic and general English words used across Reading, Listening, Writing sections
- Do NOT include any of these words the user already knows: [comma-separated list]
- Return ONLY a JSON array of 20 strings, no explanation
- Example: ["phenomenon", "substantial", "prevalent"]
```

**Error handling:**
- LLM timeout/failure: return `{"success": false, "error": "..."}`
- JSON parse failure: fallback regex extraction like `ai_service.py`
- Cache results for 1 hour per user to avoid redundant LLM calls

**URL registration:** Add to `vocabulary/api_urls.py`

### Decorator stack
- `@login_required`
- `@require_POST`

## Frontend

### UI: New section on `/add` page

Place a new section **below Quick Add** and **above the flashcard cards container**:

```html
<div class="vstep-suggestion-section">
  <div class="vstep-header">
    <span class="vstep-icon"><!-- graduation cap SVG --></span>
    <h3>VSTEP Vocabulary Suggestions</h3>
  </div>
  <p class="vstep-description">Auto-generate 20 common VSTEP exam words you haven't learned yet</p>
  <button id="vstep-suggest-btn" class="vstep-suggest-btn">
    Suggest 20 VSTEP Words
  </button>
  <div id="vstep-processing" class="processing-indicator">
    <div class="spinner"></div>
    <span>Generating VSTEP suggestions...</span>
  </div>
</div>
```

Styling: consistent with existing `.quick-add-section` design (dark theme, purple gradient button).

### JS Logic

```javascript
vstepSuggestBtn.addEventListener('click', async () => {
  // 1. Validate deck selection
  // 2. Show loading spinner
  // 3. POST to /api/ai/vstep-suggestions/
  // 4. On success: call generateCardsFromWords(response.words)
  // 5. On error: show notification
  // 6. Hide loading spinner
});
```

Reuses the existing `generateCardsFromWords()` function which already handles:
- Creating card DOM elements
- Checking duplicates
- Triggering spell check / word details fetch

### i18n texts

Add entries to the manual translations context processor for both English and Vietnamese:
- `vstep_suggestion_title`
- `vstep_suggestion_description`
- `vstep_suggest_button`
- `vstep_processing_text`
- `vstep_error_message`

## Data Flow

```
User clicks "Suggest 20 VSTEP Words"
  -> POST /api/ai/vstep-suggestions/
  -> Backend queries user's existing words
  -> Backend calls LLM with exclusion list
  -> LLM returns 20 new words as JSON array
  -> Backend validates + filters duplicates
  -> Returns {"success": true, "words": [...]}
  -> Frontend calls generateCardsFromWords(words)
  -> 20 flashcard cards auto-populated on page
  -> User reviews, edits if needed
  -> User clicks "Save All" (existing flow)
```

## Files to modify

1. `vocabulary/views.py` - add `api_vstep_suggestions` view
2. `vocabulary/api_urls.py` - add URL route
3. `vocabulary/templates/vocabulary/add_flashcard.html` - add VSTEP section UI + JS
4. `vocabulary/context_processors.py` - add i18n text entries

## Out of scope

- Topic filtering (user chose "AI tự chọn")
- Static word lists
- Auto-save without review
