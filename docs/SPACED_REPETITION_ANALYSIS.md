# Spaced Repetition System Analysis

## Overview

Your Django vocabulary learning application implements a **sophisticated spaced repetition system** based on the **SM-2 algorithm** with several enhancements. Here's a complete analysis of how it determines when words reappear for study.

## 1. Database Model Fields (Flashcard Model)

### **Core SM-2 Fields**:
```python
# Spaced repetition scheduling fields
ease_factor = models.FloatField(default=2.5)           # SM-2 ease factor
repetitions = models.PositiveIntegerField(default=0)   # Successful reviews in a row
interval = models.PositiveIntegerField(default=0)      # Interval (days) until next review
next_review = models.DateField(default=timezone.now)   # When card should appear next
last_reviewed = models.DateTimeField(blank=True, null=True)  # Last review timestamp
```

### **Enhanced Tracking Fields**:
```python
# Enhanced spaced repetition fields
times_seen_today = models.PositiveIntegerField(default=0)    # Daily view counter
last_seen_date = models.DateField(blank=True, null=True)     # Last shown date
difficulty_score = models.FloatField(default=0.0)           # 0.0=easy, 1.0=very hard
total_reviews = models.PositiveIntegerField(default=0)       # Total review count
correct_reviews = models.PositiveIntegerField(default=0)     # Correct review count
```

## 2. SM-2 Algorithm Implementation (`_update_sm2` function)

### **Algorithm Flow**:

1. **For Incorrect Answers** (`correct=False`):
   ```python
   repetitions = 0                    # Reset streak
   interval = 1                       # Show again tomorrow
   difficulty_score += 0.1            # Increase difficulty
   next_review = today + 1 day
   ```

2. **For Correct Answers** (`correct=True`):
   ```python
   ease_factor = max(1.3, ease_factor + 0.1 - (5-4) * (0.08 + (5-4) * 0.02))
   repetitions += 1
   
   if repetitions == 1:
       interval = 1                   # 1 day
   elif repetitions == 2:
       interval = 6                   # 6 days
   else:
       interval = round(interval * ease_factor)  # Exponential growth
   ```

3. **Difficulty Adjustment**:
   ```python
   difficulty_multiplier = 1.0 - (difficulty_score * 0.3)
   interval = max(1, round(interval * difficulty_multiplier))
   ```

4. **Safety Constraints**:
   ```python
   MAX_INTERVAL_DAYS = 3650  # ~10 years maximum
   if interval > MAX_INTERVAL_DAYS:
       interval = MAX_INTERVAL_DAYS
   ```

## 3. Card Selection Algorithm (`_get_next_card_enhanced`)

The system uses a **3-tier priority system** to determine which cards to show:

### **Priority 1: Due Cards** (Highest Priority)
```python
due_cards = cards.filter(
    next_review__lte=today,                    # Due for review
    times_seen_today__lt=3                     # Not shown too much today
).annotate(
    priority_score=Case(
        When(next_review__lt=today - 7_days, then=10.0),  # Very overdue
        When(next_review__lt=today - 3_days, then=8.0),   # Overdue  
        When(next_review__lt=today - 1_day, then=6.0),    # Yesterday
        When(next_review=today, then=4.0),                # Due today
        default=2.0
    )
).order_by('-priority_score', 'next_review')
```

### **Priority 2: Neglected Cards** (Medium Priority)
```python
neglected_cards = cards.filter(
    last_reviewed__lt=today - 14_days,         # Not reviewed in 14+ days
    times_seen_today__lt=2                     # Less strict daily limit
).order_by('last_reviewed')                    # Oldest first
```

### **Priority 3: Practice Cards** (Low Priority)
```python
available_cards = cards.filter(
    times_seen_today__lt=1                     # Not shown today yet
).order_by(Random())                           # Random selection
```

### **Fallback**: Any available card (rare)

## 4. Configuration Constants

```python
SPACED_REPETITION_CONFIG = {
    'MAX_DAILY_REVIEWS': 3,          # Max times a card shown per day
    'NEGLECT_THRESHOLD_DAYS': 14,    # Days before card considered neglected
    'DIFFICULTY_ADJUSTMENT': 0.3,    # How much difficulty affects interval
}
```

## 5. Why Words Might Not Reappear

### **Time-Based Restrictions**:

1. **Future Review Date**: If `next_review > today`, the word won't appear until that date
2. **Daily Limit Reached**: If `times_seen_today >= 3`, the word won't appear again today
3. **Successful Learning**: Words with high `ease_factor` and `repetitions` have very long intervals

### **Example Scenarios**:

**Scenario A: Well-Learned Word**
```
repetitions: 5
ease_factor: 3.2
interval: 180 days (6 months)
next_review: 2025-12-15
→ Won't appear until December 2025
```

**Scenario B: Daily Limit Reached**
```
times_seen_today: 3
last_seen_date: 2025-07-24
→ Won't appear again today, resets tomorrow
```

**Scenario C: Recent Correct Answer**
```
last_reviewed: 2025-07-24 10:00 AM
interval: 30 days
next_review: 2025-08-23
→ Won't appear for 30 days
```

## 6. Interval Progression Examples

### **New Word Learning Path**:
```
Review 1: Correct → interval = 1 day    → next_review = tomorrow
Review 2: Correct → interval = 6 days   → next_review = +6 days
Review 3: Correct → interval = 15 days  → next_review = +15 days (6 * 2.5)
Review 4: Correct → interval = 37 days  → next_review = +37 days (15 * 2.5)
Review 5: Correct → interval = 93 days  → next_review = +93 days (37 * 2.5)
```

### **Difficult Word (Low Accuracy)**:
```
difficulty_score: 0.7 (70% error rate)
difficulty_multiplier: 1.0 - (0.7 * 0.3) = 0.79
interval = base_interval * 0.79  → Reduced by 21%
```

## 7. Study Mode Differences

### **Normal Study Mode**:
- Uses `_get_next_card_enhanced()` algorithm
- Respects `next_review` dates and daily limits
- Prioritizes due and neglected cards

### **Random Study Mode**:
- Ignores `next_review` dates
- Only excludes cards seen in current session
- Shows any available card randomly

### **Review Mode**:
- Shows only incorrect words from `IncorrectWordReview` table
- Ignores spaced repetition schedule
- Focuses on error correction

## 8. Debugging Your Issue

To understand why specific words aren't appearing, check these fields in your database:

```sql
SELECT 
    word,
    next_review,
    times_seen_today,
    last_seen_date,
    interval,
    repetitions,
    ease_factor,
    difficulty_score
FROM vocabulary_flashcard 
WHERE user_id = YOUR_USER_ID
ORDER BY next_review;
```

### **Common Reasons Words Don't Appear**:

1. **`next_review` is in the future** → Word scheduled for later
2. **`times_seen_today >= 3`** → Daily limit reached
3. **High `interval` value** → Long gap between reviews
4. **No cards match deck filter** → Wrong deck selected
5. **All cards exhausted** → Need more vocabulary

## 9. Recommendations

### **To See More Words**:
1. **Use Random Study Mode** → Bypasses spaced repetition schedule
2. **Study Different Decks** → Access different word pools  
3. **Wait for Tomorrow** → Daily counters reset at midnight
4. **Add More Vocabulary** → Expand your word collection

### **To Adjust Repetition**:
1. **Modify `MAX_DAILY_REVIEWS`** → Allow more daily repetitions
2. **Reduce `NEGLECT_THRESHOLD_DAYS`** → Show neglected words sooner
3. **Adjust `DIFFICULTY_ADJUSTMENT`** → Change difficulty impact on intervals

The system is designed to **optimize long-term retention** by showing words at scientifically-determined intervals, which means some words intentionally won't appear for days, weeks, or even months if you've mastered them well.
