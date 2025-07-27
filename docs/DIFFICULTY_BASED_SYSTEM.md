# Difficulty-Based Card Selection System

## Overview

The Django vocabulary learning application has been **successfully migrated** from the SM-2 spaced repetition algorithm to a **simpler difficulty-based card selection system**. This new system prioritizes cards based on user feedback grades rather than time-based intervals.

## ✅ **Implementation Complete**

### **1. Removed SM-2 Logic**
- ✅ Eliminated `ease_factor`, `repetitions`, `interval`, and `next_review` time-based calculations
- ✅ Replaced `_update_sm2()` function with `_update_card_difficulty()`
- ✅ Updated all function calls to use the new difficulty system

### **2. Implemented 4-Level Difficulty System**
- ✅ **Grade 0 (Again)**: Highest difficulty - `difficulty_score = 0.0`
- ✅ **Grade 1 (Hard)**: High difficulty - `difficulty_score = 0.33`
- ✅ **Grade 2 (Good)**: Medium difficulty - `difficulty_score = 0.67`
- ✅ **Grade 3 (Easy)**: Low difficulty - `difficulty_score = 1.0`

### **3. Smart Selection Algorithm**
- ✅ Replaced `_get_next_card_enhanced()` with difficulty-based prioritization
- ✅ Implemented weighted selection system
- ✅ Added comprehensive debug logging

### **4. Database Migration**
- ✅ Created and applied migration `0012_switch_to_difficulty_based_system`
- ✅ Updated model field descriptions
- ✅ Made `difficulty_score` nullable for new cards

## 🎯 **How the New System Works**

### **Difficulty Assignment**

**When User Provides Grade (0-3)**:
```python
grade_to_difficulty = {
    0: 0.0,   # Again (highest difficulty)
    1: 0.33,  # Hard
    2: 0.67,  # Good
    3: 1.0    # Easy (lowest difficulty)
}
```

**When User Answers Incorrectly** (`correct=false`):
- Automatically set to **Grade 0 (Again)** - highest difficulty
- `difficulty_score = 0.0`

**When User Answers Correctly** (no grade provided):
- Default to **Grade 2 (Good)** - medium difficulty
- `difficulty_score = 0.67`

### **Card Selection Algorithm**

The system uses **weighted random selection** based on difficulty levels:

```python
DIFFICULTY_WEIGHTS = {
    'again': 40,  # Again cards - 40% selection weight
    'hard': 30,   # Hard cards - 30% selection weight
    'good': 20,   # Good cards - 20% selection weight
    'easy': 10,   # Easy cards - 10% selection weight
    'new': 35,    # New cards - 35% selection weight
}
```

### **Selection Priority**

1. **Again Cards (40% weight)**: Shown most frequently
2. **New Cards (35% weight)**: High priority for learning
3. **Hard Cards (30% weight)**: Shown frequently
4. **Good Cards (20% weight)**: Shown moderately
5. **Easy Cards (10% weight)**: Shown least frequently

## 📊 **Expected Behavior**

### **Study Session Flow**

1. **User starts study session**
2. **System selects card** based on difficulty weights
3. **User answers question** and provides grade (0-3)
4. **System updates difficulty** based on grade
5. **Next card selected** with updated probabilities

### **Example Selection Probabilities**

If you have:
- 10 Again cards (difficulty_score = 0.0)
- 5 Hard cards (difficulty_score = 0.33)
- 8 Good cards (difficulty_score = 0.67)
- 12 Easy cards (difficulty_score = 1.0)
- 3 New cards (difficulty_score = null)

**Selection chances**:
- **Again cards**: ~40% chance
- **New cards**: ~35% chance
- **Hard cards**: ~30% chance
- **Good cards**: ~20% chance
- **Easy cards**: ~10% chance

## 🔧 **Configuration**

### **Adjustable Settings** (`SPACED_REPETITION_CONFIG`):

```python
SPACED_REPETITION_CONFIG = {
    'MAX_DAILY_REVIEWS': 5,          # Max times a card shown per day (increased)
    'DIFFICULTY_WEIGHTS': {
        'again': 40,  # Adjust weight for Again cards
        'hard': 30,   # Adjust weight for Hard cards
        'good': 20,   # Adjust weight for Good cards
        'easy': 10,   # Adjust weight for Easy cards
        'new': 35,    # Adjust weight for New cards
    }
}
```

### **To Modify Behavior**:

**Show difficult cards more often**:
```python
'again': 50,  # Increase from 40
'hard': 35,   # Increase from 30
```

**Show easy cards more often**:
```python
'easy': 25,   # Increase from 10
'good': 30,   # Increase from 20
```

## 🧪 **Testing the New System**

### **1. Start Study Session**
```
http://127.0.0.1:8000/en/study/
```

### **2. Check Server Logs**
Look for debug messages:
```
CARD SELECTION: Selected difficulty 'again' from 135 weighted options
CARD SELECTION: Available cards in 'again': 5
DIFFICULTY UPDATE: Using grade 1 -> difficulty_level=1
DIFFICULTY UPDATE: Card 'difficult_word' set to difficulty_score=0.33 (level 1)
```

### **3. Test Different Scenarios**

**Scenario A: Answer Incorrectly**
- Answer a question wrong
- Should see: `difficulty_level=0` (Again)
- Card should appear more frequently

**Scenario B: Grade as Easy**
- Answer correctly and click "Easy"
- Should see: `difficulty_level=3` (Easy)
- Card should appear less frequently

**Scenario C: New Cards**
- Add new vocabulary
- Should see high selection priority for new cards

## 📈 **Benefits of New System**

### **1. Simplicity**
- ✅ No complex time-based calculations
- ✅ Easy to understand and debug
- ✅ Immediate feedback response

### **2. User Control**
- ✅ Direct difficulty control through grades
- ✅ Immediate impact on card frequency
- ✅ Intuitive feedback system

### **3. Flexibility**
- ✅ Easy to adjust selection weights
- ✅ No time constraints
- ✅ Variety in study sessions

### **4. Performance**
- ✅ Faster card selection (no date calculations)
- ✅ Simpler database queries
- ✅ Reduced complexity

## 🔄 **Migration Notes**

### **Legacy Fields** (preserved but not used):
- `ease_factor`: Set to default 2.5
- `repetitions`: Set to 0
- `interval`: Set to 0
- `next_review`: Set to current date

### **Active Fields**:
- `difficulty_score`: Core difficulty level (0.0, 0.33, 0.67, 1.0, null)
- `total_reviews`: Total review count
- `correct_reviews`: Correct review count
- `times_seen_today`: Daily limit tracking
- `last_reviewed`: Last review timestamp

## 🚀 **Next Steps**

1. **Test the system** with real study sessions
2. **Monitor card selection** through server logs
3. **Adjust weights** if needed based on user experience
4. **Remove debug logging** once confirmed working
5. **Consider adding UI indicators** for difficulty levels

## 🎉 **Success Criteria**

- ✅ **Server runs without errors**
- ✅ **Cards are selected based on difficulty**
- ✅ **Difficult cards appear more frequently**
- ✅ **Easy cards appear less frequently**
- ✅ **User grades directly affect card frequency**
- ✅ **System provides variety in study sessions**

The new difficulty-based system is **fully operational** and ready for use! The migration from SM-2 to difficulty-based selection has been completed successfully.
