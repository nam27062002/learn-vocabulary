# Incorrect Answer Tracking Bug Fix

## 🐛 **Problem Identified**

**Issue**: When users answered questions incorrectly in the study interface, the server logs showed `correct=True` instead of `correct=False`, preventing incorrect words from being tracked properly.

**Root Cause**: The JavaScript code had two different submission flows:
1. **Answer Evaluation**: Correctly determined if the user's answer was right or wrong
2. **Grade Submission**: Used spaced repetition grades (Again=0, Hard=1, Good=2, Easy=3) to determine correctness

The bug was in the **grade submission logic**:
```javascript
// BUGGY CODE (line 630 in study.js)
correct: grade >= 2, // Grade 2+ is considered correct
```

This meant:
- ❌ **Wrong answer + "Good" grade** → Recorded as `correct=true`
- ❌ **Correct answer + "Again" grade** → Recorded as `correct=false`

## ✅ **Solution Implemented**

### **1. Fixed JavaScript Logic**

**File**: `static/js/study.js`

**Changes Made**:

1. **Store actual correctness** in `submitAnswer()` function:
```javascript
function submitAnswer(correct) {
    // Store the actual correctness for later use in submitGrade
    window.currentAnswerCorrectness = correct;
    // ... rest of function
}
```

2. **Use actual correctness** in `submitGrade()` function:
```javascript
function submitGrade(grade) {
    // Use the actual answer correctness, not the grade
    const actualCorrectness = window.currentAnswerCorrectness !== undefined 
        ? window.currentAnswerCorrectness 
        : (grade >= 2);

    fetch(STUDY_CFG.submitUrl, {
        // ...
        body: JSON.stringify({
            card_id: currentQuestion.id,
            correct: actualCorrectness, // Use actual answer correctness
            response_time: responseTime,
            question_type: currentQuestion.type || 'multiple_choice',
            grade: grade // Also send the grade for spaced repetition
        })
    })
}
```

### **2. Updated Server-Side Logic**

**File**: `vocabulary/views.py`

**Changes Made**:

1. **Parse both parameters**:
```python
correct = data.get('correct')  # bool - actual answer correctness
grade = data.get('grade')      # int - spaced repetition grade (0-3)
```

2. **Use correct parameter for incorrect words tracking**:
```python
if not correct:  # Uses actual answer correctness
    # Add to incorrect words list
    incorrect_review, created = IncorrectWordReview.objects.get_or_create(...)
```

3. **Use grade for SM-2 algorithm**:
```python
# Use grade for SM-2 if available, otherwise use correct parameter
if grade is not None:
    sm2_correct = grade >= 2  # Grade 2+ (Good/Easy) = correct for SM-2
else:
    sm2_correct = correct     # Fallback for backward compatibility

_update_sm2(card, sm2_correct)
```

## 🎯 **How It Works Now**

### **Study Flow**:
1. **User answers question** → JavaScript determines actual correctness
2. **Feedback shown** → User sees if they got it right/wrong
3. **Grade buttons appear** → User rates difficulty (Again/Hard/Good/Easy)
4. **Data sent to server**:
   - `correct`: Based on actual answer (for incorrect words tracking)
   - `grade`: Based on user's difficulty rating (for spaced repetition)

### **Server Processing**:
1. **Incorrect Words Tracking**: Uses `correct` parameter
   - `correct=false` → Adds to IncorrectWordReview
   - `correct=true` → Marks as resolved if previously incorrect

2. **Spaced Repetition (SM-2)**: Uses `grade` parameter
   - `grade >= 2` (Good/Easy) → Increases interval
   - `grade < 2` (Again/Hard) → Resets/reduces interval

## 🧪 **Testing Instructions**

### **Test Case 1: Incorrect Answer with Good Grade**
1. **Answer a question wrong** (e.g., type "wrong" when answer is "correct")
2. **Click "Good" grade button**
3. **Expected server logs**:
```
Parsed data: card_id=123, correct=False, question_type=type, grade=2
INCORRECT ANSWER DETECTED - Adding to tracking
SUCCESS: Added incorrect word: correct (type) - created: True
SM-2 update: Using grade 2 -> sm2_correct=True
```

### **Test Case 2: Correct Answer with Again Grade**
1. **Answer a question correctly**
2. **Click "Again" grade button** (because it was hard to remember)
3. **Expected server logs**:
```
Parsed data: card_id=123, correct=True, question_type=type, grade=0
CORRECT ANSWER - checking if word was previously incorrect
SM-2 update: Using grade 0 -> sm2_correct=False
```

### **Test Case 3: Verify Incorrect Words Count**
1. **Answer several questions incorrectly**
2. **Return to study page**
3. **Check that "Review Incorrect Words" shows count > 0**

## 📊 **Expected Results**

### ✅ **Fixed Behavior**:
- **Incorrect answers are properly tracked** regardless of grade given
- **Correct answers don't get added to incorrect words** regardless of grade
- **Spaced repetition works correctly** based on difficulty grades
- **Review mode shows actual incorrect words** for practice

### ✅ **Server Logs Should Show**:
```
=== INCORRECT WORD TRACKING DEBUG ===
Answer tracking: card=surprising, correct=False, question_type=type, mapped=type
User authenticated: True
User ID: 3
User email: nam27062002@gmail.com
INCORRECT ANSWER DETECTED - Adding to tracking
SUCCESS: Added incorrect word: surprising (type) - created: True
SM-2 update: Using grade 2 -> sm2_correct=True
```

## 🔧 **Files Modified**

1. **`static/js/study.js`**:
   - Line 472: Added `window.currentAnswerCorrectness = correct;`
   - Line 625: Changed to use `actualCorrectness` instead of `grade >= 2`
   - Line 637: Added `grade: grade` to request body

2. **`vocabulary/views.py`**:
   - Line 412: Added `grade = data.get('grade')`
   - Line 414: Added grade to debug output
   - Lines 504-516: Updated SM-2 logic to use grade parameter

## 🎉 **Benefits of This Fix**

1. **Accurate Tracking**: Incorrect words are tracked based on actual answer correctness
2. **Better Spaced Repetition**: SM-2 algorithm uses difficulty grades appropriately
3. **Separation of Concerns**: Answer correctness and difficulty rating are handled separately
4. **Backward Compatibility**: Still works if grade parameter is not provided
5. **Enhanced Debugging**: Clear logs show both correctness and grade values

## 🚀 **Next Steps**

1. **Test the fix** using the provided test cases
2. **Verify incorrect words count** updates correctly
3. **Test review functionality** with tracked incorrect words
4. **Remove debug logging** once confirmed working (for production)

The fix ensures that the incorrect words tracking system works correctly while maintaining the spaced repetition functionality, providing users with accurate review sessions for words they actually answered incorrectly.
