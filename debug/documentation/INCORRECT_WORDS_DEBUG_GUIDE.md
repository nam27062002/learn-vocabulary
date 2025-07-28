# Incorrect Words Tracking Debug Guide

## Issues Identified and Fixed

### 🔍 **Root Causes Found**

1. **Custom User Model**: The app uses `accounts.CustomUser` instead of Django's default User model
   - `username = None` in the custom model (uses email as identifier)
   - This caused `request.user.username` to show as `None` in logs

2. **Enhanced Debug Logging**: Added comprehensive logging to track the entire flow
   - User authentication status
   - Question type mapping
   - IncorrectWordReview record creation
   - Database verification

3. **Question Type Mapping**: Added support for both 'input' and 'type' question types
   - JavaScript sends 'type' but mapping only handled 'input'

### ✅ **Fixes Applied**

1. **Enhanced Debug Logging in `api_submit_answer`**:
   ```python
   print(f"User authenticated: {request.user.is_authenticated}")
   print(f"User ID: {request.user.id}")
   print(f"User email: {request.user.email}")
   print(f"QUESTION TYPE MAPPING: {question_type} -> {mapped_question_type}")
   print(f"INCORRECT ANSWER DETECTED - Adding to tracking")
   print(f"SUCCESS: Added incorrect word: {card.word}")
   print(f"VERIFICATION: Record exists in DB: {verify_record is not None}")
   ```

2. **Enhanced Debug Logging in `api_get_incorrect_words_count`**:
   ```python
   print(f"Total IncorrectWordReview records for user: {total_records}")
   print(f"Unresolved IncorrectWordReview records for user: {unresolved_records}")
   print(f"Query result: {list(incorrect_words)}")
   print(f"Final counts: {counts}")
   ```

3. **Fixed Question Type Mapping**:
   ```python
   question_type_map = {
       'multiple_choice': 'mc',
       'input': 'type',
       'type': 'type',  # Handle both 'input' and 'type'
       'dictation': 'dictation'
   }
   ```

## Testing Instructions

### 📋 **Step 1: Verify Server is Running**
The Django development server should be running at `http://127.0.0.1:8000/` with enhanced debug logging enabled.

### 📋 **Step 2: Test Incorrect Answer Tracking**

1. **Navigate to Study Page**:
   - Go to `http://127.0.0.1:8000/en/study/`
   - Select a study mode (Random Words or by Decks)
   - Start a study session

2. **Answer Questions Incorrectly**:
   - **For Type Answer mode**: Enter wrong answers deliberately
   - **For Multiple Choice mode**: Select wrong options
   - **For Dictation mode**: Type wrong words

3. **Check Server Logs**:
   Look for these debug messages in the terminal:
   ```
   === INCORRECT WORD TRACKING DEBUG ===
   Answer tracking: card=WORD_NAME, correct=False, question_type=type, mapped=type
   User authenticated: True
   User ID: 1
   User email: your_email@example.com
   INCORRECT ANSWER DETECTED - Adding to tracking
   SUCCESS: Added incorrect word: WORD_NAME (type) - created: True, error_count: 1
   VERIFICATION: Record exists in DB: True
   ```

### 📋 **Step 3: Test Incorrect Words Count API**

1. **Return to Study Page**:
   - Go back to `http://127.0.0.1:8000/en/study/`
   - The page should load the incorrect words count

2. **Check Server Logs**:
   Look for these debug messages:
   ```
   === API_GET_INCORRECT_WORDS_COUNT CALLED ===
   User authenticated: True
   User ID: 1
   User email: your_email@example.com
   Total IncorrectWordReview records for user: X
   Unresolved IncorrectWordReview records for user: X
   Query result: [{'question_type': 'type', 'count': X}]
   Final counts: {'total': X, 'mc': 0, 'type': X, 'dictation': 0}
   ```

3. **Check Browser Network Tab**:
   - Open Developer Tools (F12)
   - Go to Network tab
   - Look for `/api/incorrect-words/count/` request
   - Should return 200 status with correct count data

### 📋 **Step 4: Test Review Functionality**

1. **Verify Review Option Appears**:
   - On the study page, you should see "Review Incorrect Words" option
   - It should show the correct count: "X incorrect words to review"

2. **Start Review Session**:
   - Click "Start Review"
   - Verify that only previously incorrect words appear
   - Answer them correctly to resolve them

3. **Check Resolution**:
   - After answering correctly, check server logs for:
   ```
   CORRECT ANSWER - checking if word was previously incorrect
   Resolved incorrect word: WORD_NAME (type)
   ```

## Expected Debug Output Examples

### ✅ **Successful Incorrect Answer Tracking**
```
================================================================================
=== API_SUBMIT_ANSWER CALLED ===
Request method: POST
Request body: b'{"card_id":96,"correct":false,"response_time":19.693,"question_type":"type"}'
================================================================================
Parsed data: card_id=96, correct=False, question_type=type
QUESTION TYPE MAPPING: type -> type
================================================================================
=== INCORRECT WORD TRACKING DEBUG ===
Answer tracking: card=mobile, correct=False, question_type=type, mapped=type
User authenticated: True
User ID: 1
User email: admin@test.com
Card ID: 96, Card User ID: 1
================================================================================
INCORRECT ANSWER DETECTED - Adding to tracking
SUCCESS: Added incorrect word: mobile (type) - created: True, error_count: 1
VERIFICATION: Record exists in DB: True
VERIFICATION: Record details - ID: 123, error_count: 1, is_resolved: False
```

### ✅ **Successful Count Retrieval**
```
================================================================================
=== API_GET_INCORRECT_WORDS_COUNT CALLED ===
User authenticated: True
User ID: 1
User email: admin@test.com
Total IncorrectWordReview records for user: 3
Unresolved IncorrectWordReview records for user: 2
Query result: [{'question_type': 'type', 'count': 2}]
Final counts: {'total': 2, 'mc': 0, 'type': 2, 'dictation': 0}
================================================================================
```

## Troubleshooting

### ❌ **If User Shows as Not Authenticated**
```
User authenticated: False
User ID: None
```
**Solution**: Make sure you're logged in to the application before testing.

### ❌ **If No Records Are Created**
```
INCORRECT ANSWER DETECTED - Adding to tracking
ERROR tracking incorrect word: [error message]
```
**Solution**: Check the error message for database issues or permission problems.

### ❌ **If Count is Always 0**
```
Total IncorrectWordReview records for user: 0
Unresolved IncorrectWordReview records for user: 0
```
**Solution**: 
1. Verify that incorrect answers are being submitted (`correct=false` in logs)
2. Check that IncorrectWordReview records are being created successfully
3. Ensure the user ID matches between creation and retrieval

## Success Criteria

✅ **All systems working correctly when:**

1. **Server logs show successful incorrect word tracking** for wrong answers
2. **API endpoint returns correct counts** (> 0 when there are incorrect words)
3. **Review mode displays and functions properly** with tracked words
4. **No 404 errors** in browser console or network tab
5. **Incorrect words are resolved** when answered correctly in review mode

## Next Steps After Testing

Once testing confirms the system is working:

1. **Remove debug logging** from production code
2. **Document the final solution** for future reference
3. **Consider adding unit tests** for the incorrect words tracking system
4. **Monitor performance** with the enhanced tracking in place
