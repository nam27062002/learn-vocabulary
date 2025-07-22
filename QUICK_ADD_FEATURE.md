# Quick Add Words Feature

## Overview
The Quick Add Words feature allows users to quickly create multiple flashcards at once by entering words separated by the pipe character (`|`). This feature significantly speeds up the process of adding multiple vocabulary words while maintaining all existing functionality and validation.

## How to Use

### 1. Access the Feature
- Navigate to the `/add` route (Add Flashcard page)
- You'll see a "Quick Add Multiple Words" section above the individual flashcard forms

### 2. Enter Words
- In the textarea, enter multiple words separated by the pipe character (`|`)
- Example: `assistant|cry|usual|file|ban|ice|column|currently|prepare|acceptable`
- Words will be automatically trimmed of whitespace
- Duplicate words in the input will be automatically removed

### 3. Generate Cards
- Click the "Generate Cards" button or use Ctrl+Enter (Cmd+Enter on Mac)
- **Important**: If you have existing cards with content, the system will ask for confirmation before clearing them
- The system will first clear all existing cards, then create new ones for your words
- A progress indicator will show the current processing status

### 4. Review Results
- After processing, you'll see a summary showing:
  - ✅ Successfully added words
  - ⚠️ Skipped duplicate words (already exist in your vocabulary)
  - ❌ Failed words (if any errors occurred)

## Features

### Replace Mode Operation
- **Clears existing cards**: When you use Quick Add, all current flashcards are cleared first
- **Fresh start**: Each Quick Add operation gives you a clean slate
- **Confirmation dialog**: If you have existing content, the system asks for confirmation before clearing

### Automatic Processing
For each word, the system automatically:
- Checks for duplicates against your existing vocabulary
- Performs spell checking
- Fetches word details (phonetics, definitions, part of speech)
- Fetches audio pronunciation
- Applies duplicate warning styling if needed

### Integration with Existing Features
- Works alongside the manual "Add Card" button
- Respects the current deck selection
- Maintains drag-and-drop functionality
- Preserves all existing card features (delete, image upload, etc.)
- Uses the same validation and styling as manual cards

### Error Handling
- Validates deck selection before processing
- Handles network errors gracefully
- Provides clear feedback for all scenarios
- Allows continued editing of generated cards

## Technical Details

### Input Validation
- Maximum word length: 255 characters (database limit)
- Case-insensitive duplicate detection
- Automatic whitespace trimming
- Empty word filtering

### Processing Flow
1. Parse input by pipe delimiter
2. Remove duplicates and invalid words
3. Check deck selection
4. Show confirmation dialog if existing cards have content
5. Clear all existing cards (keep one empty as template)
6. Reset form state and card numbering
7. For each word:
   - Check if already exists in user's vocabulary
   - Use first empty card for first word, create new cards for others
   - Trigger spell check and word details fetching
   - Initialize all card functionality

### Performance Considerations
- Sequential processing to avoid overwhelming APIs
- Progress feedback for user experience
- Caching of word details to improve performance
- Graceful handling of API rate limits

## Examples

### Basic Usage
```
Input: hello|world|vocabulary|learning
Result: 4 new flashcards created (assuming none are duplicates)
```

### With Duplicates
```
Input: hello|world|hello|vocabulary
Result: 3 new flashcards (hello appears twice, so one is filtered out)
```

### Mixed Case
```
Input: Hello|WORLD|hello|World
Result: 2 new flashcards (case-insensitive duplicate removal)
```

## Keyboard Shortcuts
- **Ctrl+Enter** (Windows/Linux) or **Cmd+Enter** (Mac): Generate cards from current input

## Error Messages
- **"No Words Found"**: Input is empty or contains no valid words
- **"No Deck Selected"**: User must select a deck before generating cards
- **"Replace Existing Cards?"**: Confirmation dialog when existing cards have content
- **"Processing Error"**: Network or system error during processing
- **Duplicate warnings**: Shown in results summary for existing words

## Tips for Best Results
1. Select your target deck before using Quick Add
2. **Save your work first**: Quick Add will replace all existing cards, so save any current work before using it
3. Use simple, single words rather than phrases
4. Check the results summary to see which words were processed
5. Review and edit the generated cards as needed
6. Use the existing spell-check suggestions if words are misspelled
7. **Start fresh**: Quick Add is designed for creating new sets of cards, not adding to existing ones
