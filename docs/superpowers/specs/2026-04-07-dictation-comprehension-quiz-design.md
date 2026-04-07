# Design: Dictation Comprehension Quiz

**Date:** 2026-04-07  
**Feature:** AI-generated TOEIC-style multiple-choice listening comprehension quiz for dictation videos  
**Model:** `qwen2.5-vl-72b-instruct` via LM Studio at `http://127.0.0.1:1234`

---

## Overview

After processing a YouTube video for dictation practice, users can open a "Comprehension Quiz" modal on the practice page. The system generates 10 TOEIC Part 4-style multiple-choice questions (A/B/C/D) from the full video transcript using the local LM Studio model. Questions are generated once and cached in the database; subsequent visits load from cache instantly.

---

## Architecture

### New Django Models (`dictation/models.py`)

**`VideoQuiz`**
- `video` — FK → `DictationVideo` (one-to-one effectively; use `unique=True`)
- `created_at` — DateTimeField (auto)

**`QuizQuestion`**
- `quiz` — FK → `VideoQuiz`, `related_name='questions'`
- `order` — IntegerField (1–10)
- `question_text` — TextField
- `choice_a` / `choice_b` / `choice_c` / `choice_d` — CharField(max_length=500)
- `correct_choice` — CharField(max_length=1, choices: a/b/c/d)
- `unique_together` = [`quiz`, `order`]

**`UserQuizAttempt`**
- `user` — FK → settings.AUTH_USER_MODEL
- `quiz` — FK → `VideoQuiz`
- `answers` — JSONField — `{"1": "b", "2": "a", ...}` (question order → chosen letter)
- `score` — FloatField (0.0–1.0, correct / total)
- `created_at` — DateTimeField (auto)

---

## API Endpoints

### `POST /api/dictation/quiz/generate/<video_id>/`
- If `VideoQuiz` already exists for this video → return cached questions immediately
- Otherwise: fetch all `DictationSegment.transcript` for video, concatenate, call LM Studio, parse response, bulk-create `QuizQuestion` objects, return questions
- Response:
  ```json
  {
    "quiz_id": 1,
    "from_cache": true,
    "questions": [
      {
        "order": 1,
        "question_text": "...",
        "choice_a": "...",
        "choice_b": "...",
        "choice_c": "...",
        "choice_d": "..."
      }
    ]
  }
  ```
- Note: correct answers are **not** sent to frontend until submission

### `POST /api/dictation/quiz/submit/<quiz_id>/`
- Body: `{"answers": {"1": "b", "2": "c", ...}}`
- Compares against correct answers, computes score
- Saves `UserQuizAttempt`
- Response:
  ```json
  {
    "score": 0.7,
    "correct_count": 7,
    "total": 10,
    "results": [
      {"order": 1, "correct_choice": "b", "user_choice": "b", "correct": true},
      ...
    ]
  }
  ```

---

## LM Studio Integration

### Service function: `dictation/quiz_service.py`

```
generate_quiz_questions(transcript: str) -> list[dict]
```

- Concatenates all segment transcripts into one string
- Sends prompt to `http://127.0.0.1:1234/v1/chat/completions`
- Model: `qwen2.5-vl-72b-instruct`
- Temperature: 0.3 (slight creativity for varied questions)
- Max tokens: 3000

**Prompt structure:**
```
You are an English test designer creating TOEIC Part 4 listening comprehension questions.

Below is the transcript of an audio recording:
<transcript>
{transcript}
</transcript>

Generate exactly 10 multiple-choice questions based on this transcript.
Each question must have 4 options (A, B, C, D) with exactly one correct answer.
Focus on: main ideas, specific details, speaker's purpose, inferences.

Respond ONLY with a valid JSON array:
[
  {
    "order": 1,
    "question": "...",
    "a": "...",
    "b": "...",
    "c": "...",
    "d": "...",
    "answer": "a"
  },
  ...
]
```

- Parse JSON from response (find `[` ... `]`)
- Validate: exactly 10 items, each has required fields, answer is one of a/b/c/d
- On parse failure or LM Studio unavailable → raise exception → API returns 503

---

## Frontend (practice.html + dictation.js)

### Quiz trigger
- Add "Quiz" button in the practice panel header (top-right area)
- Only visible when `segments.length > 0`

### Modal structure
Three screens managed by JS state:

**Screen 1 — Loading:**
- Spinner + "Generating comprehension questions…"
- Shows only on first load; cached loads skip straight to Screen 2

**Screen 2 — Questions:**
- Progress indicator: "Question 3 / 10"
- Question text
- 4 radio options (A/B/C/D) with keyboard shortcuts (press A/B/C/D to select)
- "Next" / "Submit" button
- User can navigate back to previous questions

**Screen 3 — Results:**
- Score display: "7 / 10 correct (70%)"
- Per-question review: green (correct) / red (wrong), showing correct answer for wrong ones
- "Retake Quiz" button (generates new attempt, same questions)
- "Close" button

### Data flow
```
User clicks "Quiz"
  → POST /api/dictation/quiz/generate/<video_id>/
  → Show questions (Screen 2)
User answers all 10, clicks "Submit"
  → POST /api/dictation/quiz/submit/<quiz_id>/
  → Show results (Screen 3)
```

---

## URL Registration

Add to `dictation/api_urls.py`:
```
path('api/dictation/quiz/generate/<str:video_id>/', views.api_generate_quiz)
path('api/dictation/quiz/submit/<int:quiz_id>/', views.api_submit_quiz)
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| LM Studio not running | API returns 503 with message "AI service unavailable, try again later" |
| LM Studio returns malformed JSON | Retry once; if still fails → 503 |
| Video has no segments | Button disabled / tooltip "Process video first" |
| Quiz already exists | Return cached, skip generation |

---

## Migrations

New migration file for `VideoQuiz`, `QuizQuestion`, `UserQuizAttempt` models.

---

## Out of Scope

- Open-ended / short-answer questions (VSTEP writing component)
- Leaderboard or comparison between users
- Question difficulty levels
- Regenerating questions with a different set (always same 10 per video)
