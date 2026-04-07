# Dictation Comprehension Quiz Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a TOEIC-style 10-question multiple-choice comprehension quiz modal to the dictation practice page, powered by `qwen2.5-vl-72b-instruct` via LM Studio, with questions generated once and cached in the DB.

**Architecture:** New Django models store generated questions and user attempts. A service module calls LM Studio to generate questions from the full video transcript. The frontend adds a Quiz button + three-screen modal (loading → questions → results) to the existing practice page without modifying the dictation flow.

**Tech Stack:** Django ORM, JSONField, urllib (no new deps), vanilla JS, CSS custom properties

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `dictation/models.py` | Add `VideoQuiz`, `QuizQuestion`, `UserQuizAttempt` |
| Create | `dictation/migrations/0002_quiz_models.py` | Generated migration |
| Create | `dictation/quiz_service.py` | LM Studio call + JSON parsing |
| Modify | `dictation/views.py` | Add `api_generate_quiz`, `api_submit_quiz` |
| Modify | `dictation/api_urls.py` | Register 2 new API routes |
| Modify | `dictation/templates/dictation/practice.html` | Quiz button + modal HTML + pass `quizGenerateUrl`/`quizSubmitUrl` in `DICTATION_DATA` |
| Modify | `static/js/dictation.js` | Quiz modal open/navigate/submit/results logic |
| Modify | `static/css/dictation.css` | Quiz modal styles |
| Create | `tests/test_dictation_quiz.py` | Tests for service + views |

---

## Task 1: Add DB Models

**Files:**
- Modify: `dictation/models.py`

- [ ] **Step 1: Add three models at the bottom of `dictation/models.py`**

Append after the existing `DictationAttempt` class:

```python
class VideoQuiz(models.Model):
    video = models.OneToOneField(
        DictationVideo,
        on_delete=models.CASCADE,
        related_name='quiz',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Quiz for {self.video.title}'


class QuizQuestion(models.Model):
    CHOICE_VALUES = [('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]

    quiz = models.ForeignKey(VideoQuiz, on_delete=models.CASCADE, related_name='questions')
    order = models.IntegerField()
    question_text = models.TextField()
    choice_a = models.CharField(max_length=500)
    choice_b = models.CharField(max_length=500)
    choice_c = models.CharField(max_length=500)
    choice_d = models.CharField(max_length=500)
    correct_choice = models.CharField(max_length=1, choices=CHOICE_VALUES)

    class Meta:
        ordering = ['order']
        unique_together = ['quiz', 'order']

    def __str__(self):
        return f'Q{self.order}: {self.question_text[:60]}'


class UserQuizAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
    )
    quiz = models.ForeignKey(VideoQuiz, on_delete=models.CASCADE, related_name='attempts')
    answers = models.JSONField()   # {"1": "b", "2": "a", ...}  key = str(question.order)
    score = models.FloatField()    # 0.0 – 1.0
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'quiz']),
        ]

    def __str__(self):
        return f'{self.user} – Quiz {self.quiz_id} – {self.score:.0%}'
```

- [ ] **Step 2: Generate and apply migration**

```bash
python manage.py makemigrations dictation --name quiz_models
python manage.py migrate
```

Expected: migration file created, applied cleanly with no errors.

- [ ] **Step 3: Commit**

```bash
git add dictation/models.py dictation/migrations/
git commit -m "feat(dictation): add VideoQuiz, QuizQuestion, UserQuizAttempt models"
```

---

## Task 2: Create Quiz Service

**Files:**
- Create: `dictation/quiz_service.py`
- Create: `tests/test_dictation_quiz.py` (partial — service tests only)

- [ ] **Step 1: Write failing tests for `_parse_questions`**

Create `tests/test_dictation_quiz.py`:

```python
"""Tests for dictation comprehension quiz service and views."""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from dictation.quiz_service import _parse_questions, generate_quiz_questions
from dictation.models import DictationVideo, VideoQuiz, QuizQuestion, UserQuizAttempt

User = get_user_model()

VALID_QUESTIONS_JSON = json.dumps([
    {
        "order": i,
        "question": f"Question {i}?",
        "a": f"Option A{i}",
        "b": f"Option B{i}",
        "c": f"Option C{i}",
        "d": f"Option D{i}",
        "answer": "b",
    }
    for i in range(1, 11)
])


class ParseQuestionsTest(TestCase):
    def test_valid_json_returns_10_questions(self):
        result = _parse_questions(VALID_QUESTIONS_JSON)
        self.assertEqual(len(result), 10)

    def test_question_fields_mapped_correctly(self):
        result = _parse_questions(VALID_QUESTIONS_JSON)
        q = result[0]
        self.assertEqual(q['order'], 1)
        self.assertEqual(q['question_text'], 'Question 1?')
        self.assertEqual(q['choice_a'], 'Option A1')
        self.assertEqual(q['correct_choice'], 'b')

    def test_wrong_count_returns_empty(self):
        only_5 = json.dumps([
            {"order": i, "question": "Q?", "a": "A", "b": "B", "c": "C", "d": "D", "answer": "a"}
            for i in range(1, 6)
        ])
        self.assertEqual(_parse_questions(only_5), [])

    def test_invalid_answer_letter_returns_empty(self):
        bad = json.dumps([
            {"order": i, "question": "Q?", "a": "A", "b": "B", "c": "C", "d": "D", "answer": "z"}
            for i in range(1, 11)
        ])
        self.assertEqual(_parse_questions(bad), [])

    def test_json_embedded_in_prose_is_extracted(self):
        prose = f'Here are your questions:\n{VALID_QUESTIONS_JSON}\nDone.'
        result = _parse_questions(prose)
        self.assertEqual(len(result), 10)

    def test_empty_string_returns_empty(self):
        self.assertEqual(_parse_questions(''), [])
```

- [ ] **Step 2: Run tests — expect ImportError (module doesn't exist yet)**

```bash
python manage.py test tests.test_dictation_quiz.ParseQuestionsTest -v 2
```

Expected: `ImportError: cannot import name '_parse_questions' from 'dictation.quiz_service'`

- [ ] **Step 3: Create `dictation/quiz_service.py`**

```python
"""
LM Studio integration for generating TOEIC-style comprehension quiz questions.
"""
import json
import urllib.error
import urllib.request

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
LM_STUDIO_MODEL = "qwen2.5-vl-72b-instruct"
LM_STUDIO_TIMEOUT = 90  # 72b model can be slow


_PROMPT_TEMPLATE = """\
You are an English test designer creating TOEIC Part 4 listening comprehension questions.

Below is the full transcript of an audio recording:
<transcript>
{transcript}
</transcript>

Generate exactly 10 multiple-choice questions based on this transcript.
Rules:
- Each question has 4 options: a, b, c, d
- Exactly one option is correct
- Cover: main ideas, specific details, speaker purpose, and inferences
- Questions must be answerable from the transcript only
- Do NOT copy sentences verbatim as question text

Respond ONLY with a valid JSON array of exactly 10 objects, no prose:
[
  {{
    "order": 1,
    "question": "What is the main topic of the talk?",
    "a": "...",
    "b": "...",
    "c": "...",
    "d": "...",
    "answer": "b"
  }},
  ...
]
"""


def generate_quiz_questions(transcript: str) -> list[dict]:
    """
    Call LM Studio to generate 10 TOEIC-style multiple-choice questions.

    Returns a list of 10 dicts, each with keys:
      order, question_text, choice_a, choice_b, choice_c, choice_d, correct_choice

    Raises RuntimeError if LM Studio is unavailable or returns unparseable output
    after 2 attempts.
    """
    prompt = _PROMPT_TEMPLATE.format(transcript=transcript[:12000])  # cap at ~3k tokens
    payload = {
        "model": LM_STUDIO_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 3000,
    }
    encoded = json.dumps(payload).encode()

    last_error = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(
                LM_STUDIO_URL,
                data=encoded,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=LM_STUDIO_TIMEOUT) as resp:
                data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"].strip()
            questions = _parse_questions(content)
            if questions:
                return questions
            last_error = ValueError("Model returned unparseable or wrong-count response")
        except (urllib.error.URLError, OSError) as e:
            last_error = RuntimeError(f"LM Studio unavailable: {e}")
        except Exception as e:
            last_error = RuntimeError(f"Unexpected error: {e}")

    raise last_error or RuntimeError("Failed to generate questions")


def _parse_questions(content: str) -> list[dict]:
    """
    Extract and validate a JSON array of 10 questions from model output.
    Returns [] on any parse/validation failure.
    """
    if not content:
        return []
    start = content.find('[')
    end = content.rfind(']') + 1
    if start < 0 or end <= start:
        return []
    try:
        raw = json.loads(content[start:end])
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list) or len(raw) != 10:
        return []
    questions = []
    for item in raw:
        try:
            correct = str(item['answer']).lower().strip()
            if correct not in ('a', 'b', 'c', 'd'):
                return []
            questions.append({
                'order': int(item['order']),
                'question_text': str(item['question']),
                'choice_a': str(item['a']),
                'choice_b': str(item['b']),
                'choice_c': str(item['c']),
                'choice_d': str(item['d']),
                'correct_choice': correct,
            })
        except (KeyError, TypeError, ValueError):
            return []
    return questions
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
python manage.py test tests.test_dictation_quiz.ParseQuestionsTest -v 2
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dictation/quiz_service.py tests/test_dictation_quiz.py
git commit -m "feat(dictation): add quiz_service with LM Studio integration and parse tests"
```

---

## Task 3: Add API Views

**Files:**
- Modify: `dictation/views.py`
- Modify: `dictation/api_urls.py`
- Modify: `tests/test_dictation_quiz.py` (add view tests)

- [ ] **Step 1: Write failing view tests — append to `tests/test_dictation_quiz.py`**

Add after the `ParseQuestionsTest` class:

```python
class GenerateQuizViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@x.com', password='pass')
        self.client = Client()
        self.client.login(email='test@x.com', password='pass')
        self.video = DictationVideo.objects.create(
            video_id='abc123',
            title='Test Video',
            is_processed=True,
            segment_count=2,
        )
        from dictation.models import DictationSegment
        DictationSegment.objects.create(
            video=self.video, order=1,
            start_time=0, end_time=5,
            transcript='Hello world this is a test.', word_count=6,
        )

    def _make_fake_questions(self):
        return [
            {
                'order': i,
                'question_text': f'Q{i}?',
                'choice_a': 'A', 'choice_b': 'B',
                'choice_c': 'C', 'choice_d': 'D',
                'correct_choice': 'a',
            }
            for i in range(1, 11)
        ]

    @patch('dictation.views.generate_quiz_questions')
    def test_generate_creates_quiz_and_returns_questions(self, mock_gen):
        mock_gen.return_value = self._make_fake_questions()
        resp = self.client.post(f'/api/dictation/quiz/generate/{self.video.video_id}/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data['from_cache'])
        self.assertEqual(len(data['questions']), 10)
        self.assertNotIn('correct_choice', data['questions'][0])  # answers hidden
        self.assertTrue(VideoQuiz.objects.filter(video=self.video).exists())

    @patch('dictation.views.generate_quiz_questions')
    def test_second_call_returns_from_cache(self, mock_gen):
        mock_gen.return_value = self._make_fake_questions()
        self.client.post(f'/api/dictation/quiz/generate/{self.video.video_id}/')
        self.client.post(f'/api/dictation/quiz/generate/{self.video.video_id}/')
        self.assertEqual(mock_gen.call_count, 1)  # only called once

    @patch('dictation.views.generate_quiz_questions')
    def test_generate_returns_cached_on_second_request(self, mock_gen):
        mock_gen.return_value = self._make_fake_questions()
        r1 = self.client.post(f'/api/dictation/quiz/generate/{self.video.video_id}/')
        r2 = self.client.post(f'/api/dictation/quiz/generate/{self.video.video_id}/')
        self.assertTrue(r2.json()['from_cache'])

    @patch('dictation.views.generate_quiz_questions', side_effect=RuntimeError('LM Studio unavailable'))
    def test_generate_returns_503_on_lm_failure(self, mock_gen):
        resp = self.client.post(f'/api/dictation/quiz/generate/{self.video.video_id}/')
        self.assertEqual(resp.status_code, 503)


class SubmitQuizViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test2@x.com', password='pass')
        self.client = Client()
        self.client.login(email='test2@x.com', password='pass')
        self.video = DictationVideo.objects.create(
            video_id='xyz999', title='V2', is_processed=True, segment_count=1,
        )
        self.quiz = VideoQuiz.objects.create(video=self.video)
        for i in range(1, 11):
            QuizQuestion.objects.create(
                quiz=self.quiz, order=i,
                question_text=f'Q{i}?',
                choice_a='A', choice_b='B', choice_c='C', choice_d='D',
                correct_choice='a',
            )

    def _all_correct_answers(self):
        return {str(i): 'a' for i in range(1, 11)}

    def test_all_correct_gives_score_1(self):
        resp = self.client.post(
            f'/api/dictation/quiz/submit/{self.quiz.id}/',
            data=json.dumps({'answers': self._all_correct_answers()}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['score'], 1.0)
        self.assertEqual(data['correct_count'], 10)

    def test_all_wrong_gives_score_0(self):
        answers = {str(i): 'b' for i in range(1, 11)}
        resp = self.client.post(
            f'/api/dictation/quiz/submit/{self.quiz.id}/',
            data=json.dumps({'answers': answers}),
            content_type='application/json',
        )
        self.assertEqual(resp.json()['score'], 0.0)

    def test_attempt_saved_to_db(self):
        self.client.post(
            f'/api/dictation/quiz/submit/{self.quiz.id}/',
            data=json.dumps({'answers': self._all_correct_answers()}),
            content_type='application/json',
        )
        self.assertTrue(
            UserQuizAttempt.objects.filter(user=self.user, quiz=self.quiz).exists()
        )

    def test_results_include_correct_choice(self):
        resp = self.client.post(
            f'/api/dictation/quiz/submit/{self.quiz.id}/',
            data=json.dumps({'answers': self._all_correct_answers()}),
            content_type='application/json',
        )
        result = resp.json()['results'][0]
        self.assertIn('correct_choice', result)
        self.assertEqual(result['correct_choice'], 'a')
```

- [ ] **Step 2: Run tests — expect failure (views not implemented)**

```bash
python manage.py test tests.test_dictation_quiz.GenerateQuizViewTest tests.test_dictation_quiz.SubmitQuizViewTest -v 2
```

Expected: errors due to 404 (routes not yet registered).

- [ ] **Step 3: Add two view functions to `dictation/views.py`**

Add these imports at the top of `dictation/views.py` (after existing imports):

```python
from .quiz_service import generate_quiz_questions
from .models import DictationAttempt, DictationSegment, DictationVideo, VideoQuiz, QuizQuestion, UserQuizAttempt
```

Then append the two view functions at the end of `dictation/views.py`:

```python
# ---------------------------------------------------------------------------
# API: Generate or fetch cached comprehension quiz
# ---------------------------------------------------------------------------

@login_required
@require_POST
def api_generate_quiz(request, video_id):
    video = get_object_or_404(DictationVideo, video_id=video_id, is_processed=True)

    # Return cached quiz if exists
    existing = VideoQuiz.objects.filter(video=video).first()
    if existing:
        questions = list(existing.questions.values(
            'order', 'question_text', 'choice_a', 'choice_b', 'choice_c', 'choice_d'
        ))
        return JsonResponse({'quiz_id': existing.id, 'from_cache': True, 'questions': questions})

    # Build full transcript from all segments
    transcripts = video.segments.order_by('order').values_list('transcript', flat=True)
    full_transcript = ' '.join(transcripts)

    try:
        question_dicts = generate_quiz_questions(full_transcript)
    except Exception as e:
        logger.warning('Quiz generation failed for %s: %s', video_id, e)
        return JsonResponse({'error': 'AI service unavailable, please try again later'}, status=503)

    quiz = VideoQuiz.objects.create(video=video)
    QuizQuestion.objects.bulk_create([
        QuizQuestion(quiz=quiz, **q) for q in question_dicts
    ])

    questions = list(quiz.questions.values(
        'order', 'question_text', 'choice_a', 'choice_b', 'choice_c', 'choice_d'
    ))
    return JsonResponse({'quiz_id': quiz.id, 'from_cache': False, 'questions': questions})


# ---------------------------------------------------------------------------
# API: Submit quiz answers and return score
# ---------------------------------------------------------------------------

@login_required
@require_POST
def api_submit_quiz(request, quiz_id):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    answers = data.get('answers')  # {"1": "b", "2": "a", ...}
    if not isinstance(answers, dict):
        return JsonResponse({'error': 'answers must be an object'}, status=400)

    quiz = get_object_or_404(VideoQuiz, id=quiz_id)
    questions = list(quiz.questions.order_by('order'))

    correct_count = 0
    results = []
    for q in questions:
        user_choice = answers.get(str(q.order), '').lower().strip()
        is_correct = user_choice == q.correct_choice
        if is_correct:
            correct_count += 1
        results.append({
            'order': q.order,
            'correct_choice': q.correct_choice,
            'user_choice': user_choice or None,
            'correct': is_correct,
        })

    total = len(questions)
    score = round(correct_count / total, 4) if total else 1.0

    UserQuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        answers=answers,
        score=score,
    )

    return JsonResponse({
        'score': score,
        'correct_count': correct_count,
        'total': total,
        'results': results,
    })
```

- [ ] **Step 4: Register routes in `dictation/api_urls.py`**

The current file content is:
```python
from django.urls import path
from . import views

urlpatterns = [
    path('api/dictation/process-video/', views.api_process_video, name='dictation_process_video'),
    path('api/dictation/videos/<str:video_id>/segments/', views.api_get_segments, name='dictation_get_segments'),
    path('api/dictation/check-answer/', views.api_check_answer, name='dictation_check_answer'),
    path('api/dictation/save-attempt/', views.api_save_attempt, name='dictation_save_attempt'),
    path('api/dictation/progress/<str:video_id>/', views.api_get_progress, name='dictation_progress'),
]
```

Add two lines to `urlpatterns`:

```python
    path('api/dictation/quiz/generate/<str:video_id>/', views.api_generate_quiz, name='dictation_generate_quiz'),
    path('api/dictation/quiz/submit/<int:quiz_id>/', views.api_submit_quiz, name='dictation_submit_quiz'),
```

- [ ] **Step 5: Run all quiz tests**

```bash
python manage.py test tests.test_dictation_quiz -v 2
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add dictation/views.py dictation/api_urls.py tests/test_dictation_quiz.py
git commit -m "feat(dictation): add api_generate_quiz and api_submit_quiz views"
```

---

## Task 4: Add Modal HTML to practice.html

**Files:**
- Modify: `dictation/templates/dictation/practice.html`

- [ ] **Step 1: Add "Quiz" button to the practice panel header**

In `practice.html`, find this line (inside `<main class="dictation-panel">`):

```html
      <!-- ── Player section ── -->
      <div class="player-section" id="playerSection">
```

Insert the Quiz button **before** that line:

```html
      <!-- ── Quiz button ── -->
      <div class="flex justify-end mb-3">
        <button id="btnOpenQuiz" class="btn-quiz-open" title="Comprehension Quiz">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
          </svg>
          Comprehension Quiz
        </button>
      </div>
```

- [ ] **Step 2: Add quiz modal HTML and update `DICTATION_DATA`**

Find the closing `</div>` of the `fcModal` div (after the Add to Flashcard modal, before `<script>`). Insert the quiz modal right after the flashcard modal's closing `</div>`:

```html
<!-- ── Comprehension Quiz Modal ── -->
<div id="quizModal" class="quiz-modal-overlay hidden" role="dialog" aria-modal="true">
  <div class="quiz-modal">

    <!-- Header -->
    <div class="quiz-modal-header">
      <h3 class="quiz-modal-title">Comprehension Quiz</h3>
      <button id="quizModalClose" class="quiz-close-btn" aria-label="Close">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <!-- Screen 1: Loading -->
    <div id="quizScreenLoading" class="quiz-screen">
      <div class="quiz-loading-body">
        <svg class="animate-spin w-8 h-8 text-indigo-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
        </svg>
        <p class="text-gray-500 text-sm">Generating comprehension questions…</p>
        <p class="text-gray-400 text-xs mt-1">This may take up to 30 seconds</p>
      </div>
    </div>

    <!-- Screen 2: Questions -->
    <div id="quizScreenQuestions" class="quiz-screen hidden">
      <div class="quiz-progress-bar-track">
        <div class="quiz-progress-bar-fill" id="quizProgressFill"></div>
      </div>
      <p class="quiz-progress-label" id="quizProgressLabel">Question 1 / 10</p>
      <p class="quiz-question-text" id="quizQuestionText"></p>
      <div class="quiz-choices" id="quizChoices">
        <label class="quiz-choice" id="choiceA">
          <input type="radio" name="quizAnswer" value="a">
          <span class="quiz-choice-key">A</span>
          <span class="quiz-choice-text" id="choiceAText"></span>
        </label>
        <label class="quiz-choice" id="choiceB">
          <input type="radio" name="quizAnswer" value="b">
          <span class="quiz-choice-key">B</span>
          <span class="quiz-choice-text" id="choiceBText"></span>
        </label>
        <label class="quiz-choice" id="choiceC">
          <input type="radio" name="quizAnswer" value="c">
          <span class="quiz-choice-key">C</span>
          <span class="quiz-choice-text" id="choiceCText"></span>
        </label>
        <label class="quiz-choice" id="choiceD">
          <input type="radio" name="quizAnswer" value="d">
          <span class="quiz-choice-key">D</span>
          <span class="quiz-choice-text" id="choiceDText"></span>
        </label>
      </div>
      <div class="quiz-nav">
        <button id="quizBtnPrev" class="btn-ghost quiz-nav-btn" disabled>← Previous</button>
        <span></span>
        <button id="quizBtnNext" class="btn-check quiz-nav-btn">Next →</button>
        <button id="quizBtnSubmit" class="btn-check quiz-nav-btn hidden">Submit Quiz</button>
      </div>
    </div>

    <!-- Screen 3: Results -->
    <div id="quizScreenResults" class="quiz-screen hidden">
      <div class="quiz-score-display">
        <div class="quiz-score-circle" id="quizScoreCircle">
          <span id="quizScoreText"></span>
        </div>
        <p class="quiz-score-label" id="quizScoreLabel"></p>
      </div>
      <div class="quiz-results-list" id="quizResultsList"></div>
      <div class="quiz-results-actions">
        <button id="quizBtnRetake" class="btn-secondary">Retake Quiz</button>
        <button id="quizBtnCloseResults" class="btn-ghost">Close</button>
      </div>
    </div>

  </div>
</div>
```

- [ ] **Step 3: Add quiz URLs to `DICTATION_DATA` in `practice.html`**

Find the `<script>` block containing `window.DICTATION_DATA`:

```html
<script>
window.DICTATION_DATA = {
  videoId: "{{ video.video_id }}",
  segments: {{ segments_json|safe }},
  csrfToken: "{{ csrf_token }}",
  progressUrl: "/api/dictation/progress/{{ video.video_id }}/",
  checkUrl: "/api/dictation/check-answer/",
  saveUrl: "/api/dictation/save-attempt/",
  wordDetailsUrl: "/word-details/",
  decksUrl: "/api/decks/",
  saveFlashcardUrl: "/api/save-flashcards/",
  checkWordUrl: "/api/check-word-exists/",
};
</script>
```

Add two new properties inside that object:

```html
<script>
window.DICTATION_DATA = {
  videoId: "{{ video.video_id }}",
  segments: {{ segments_json|safe }},
  csrfToken: "{{ csrf_token }}",
  progressUrl: "/api/dictation/progress/{{ video.video_id }}/",
  checkUrl: "/api/dictation/check-answer/",
  saveUrl: "/api/dictation/save-attempt/",
  wordDetailsUrl: "/word-details/",
  decksUrl: "/api/decks/",
  saveFlashcardUrl: "/api/save-flashcards/",
  checkWordUrl: "/api/check-word-exists/",
  quizGenerateUrl: "/api/dictation/quiz/generate/{{ video.video_id }}/",
  quizSubmitUrl: "/api/dictation/quiz/submit/",
};
</script>
```

- [ ] **Step 4: Commit**

```bash
git add "dictation/templates/dictation/practice.html"
git commit -m "feat(dictation): add quiz modal HTML and quiz URLs to DICTATION_DATA"
```

---

## Task 5: Add Quiz CSS

**Files:**
- Modify: `static/css/dictation.css`

- [ ] **Step 1: Append quiz styles to end of `static/css/dictation.css`**

```css
/* ============================================================
   Comprehension Quiz Modal
   ============================================================ */

.btn-quiz-open {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.85rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #6366f1;
  background: transparent;
  border: 1.5px solid #6366f1;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.btn-quiz-open:hover {
  background: #6366f1;
  color: #fff;
}

.quiz-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.quiz-modal-overlay.hidden { display: none; }

.quiz-modal {
  background: var(--background-primary, #fff);
  border-radius: 1rem;
  width: 100%;
  max-width: 540px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.25);
  overflow: hidden;
}

.quiz-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  flex-shrink: 0;
}
.quiz-modal-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary, #111);
}
.quiz-close-btn {
  display: flex;
  align-items: center;
  padding: 0.25rem;
  color: var(--text-muted, #6b7280);
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background 0.15s;
  background: transparent;
  border: none;
}
.quiz-close-btn:hover { background: var(--background-secondary, #f3f4f6); }

.quiz-screen {
  padding: 1.25rem;
  overflow-y: auto;
  flex: 1;
}
.quiz-screen.hidden { display: none; }

/* Loading screen */
.quiz-loading-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  text-align: center;
}

/* Progress */
.quiz-progress-bar-track {
  height: 4px;
  background: var(--border-color, #e5e7eb);
  border-radius: 2px;
  margin-bottom: 0.5rem;
}
.quiz-progress-bar-fill {
  height: 100%;
  background: #6366f1;
  border-radius: 2px;
  transition: width 0.3s ease;
}
.quiz-progress-label {
  font-size: 0.75rem;
  color: var(--text-muted, #6b7280);
  margin-bottom: 1rem;
}

/* Question */
.quiz-question-text {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary, #111);
  margin-bottom: 1rem;
  line-height: 1.5;
}

/* Choices */
.quiz-choices {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}
.quiz-choice {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.9rem;
  border: 1.5px solid var(--border-color, #e5e7eb);
  border-radius: 0.6rem;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.quiz-choice:hover { border-color: #6366f1; background: #eef2ff; }
.quiz-choice input[type="radio"] { display: none; }
.quiz-choice.selected {
  border-color: #6366f1;
  background: #eef2ff;
}
.quiz-choice-key {
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 50%;
  background: var(--background-secondary, #f3f4f6);
  color: var(--text-muted, #6b7280);
  flex-shrink: 0;
}
.quiz-choice.selected .quiz-choice-key {
  background: #6366f1;
  color: #fff;
}
.quiz-choice-text {
  font-size: 0.875rem;
  color: var(--text-primary, #111);
}

/* Nav buttons */
.quiz-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  justify-content: space-between;
}
.quiz-nav-btn { min-width: 6rem; justify-content: center; }

/* Score circle */
.quiz-score-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem 0 1rem;
}
.quiz-score-circle {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
}
.quiz-score-circle.score-high  { background: #dcfce7; color: #15803d; }
.quiz-score-circle.score-mid   { background: #fef9c3; color: #a16207; }
.quiz-score-circle.score-low   { background: #fee2e2; color: #b91c1c; }
.quiz-score-label {
  font-size: 0.9rem;
  color: var(--text-muted, #6b7280);
}

/* Results list */
.quiz-results-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 1.25rem;
}
.quiz-result-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.82rem;
}
.quiz-result-item.correct { background: #f0fdf4; }
.quiz-result-item.wrong   { background: #fef2f2; }
.quiz-result-icon { flex-shrink: 0; font-weight: 700; width: 1.1rem; text-align: center; }
.quiz-result-item.correct .quiz-result-icon { color: #16a34a; }
.quiz-result-item.wrong   .quiz-result-icon { color: #dc2626; }
.quiz-result-detail { flex: 1; }
.quiz-result-q { font-weight: 600; color: var(--text-primary, #111); margin-bottom: 0.15rem; }
.quiz-result-ans { color: var(--text-muted, #6b7280); }
.quiz-result-ans strong { color: #16a34a; }

.quiz-results-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  padding-bottom: 0.5rem;
}
```

- [ ] **Step 2: Commit**

```bash
git add static/css/dictation.css
git commit -m "feat(dictation): add comprehension quiz modal CSS"
```

---

## Task 6: Add Quiz JavaScript Logic

**Files:**
- Modify: `static/js/dictation.js`

- [ ] **Step 1: Append quiz state variables and all functions to the end of `static/js/dictation.js`**

```js
/* ── Quiz State ── */
let quizId         = null;
let quizQuestions  = [];
let quizAnswers    = {};   // { questionOrder: 'a'|'b'|'c'|'d' }
let quizCurrentIdx = 0;

/* ── Quiz DOM refs ── */
const quizModal           = document.getElementById('quizModal');
const quizScreenLoading   = document.getElementById('quizScreenLoading');
const quizScreenQuestions = document.getElementById('quizScreenQuestions');
const quizScreenResults   = document.getElementById('quizScreenResults');
const quizProgressFill    = document.getElementById('quizProgressFill');
const quizProgressLabel   = document.getElementById('quizProgressLabel');
const quizQuestionText    = document.getElementById('quizQuestionText');
const quizBtnPrev         = document.getElementById('quizBtnPrev');
const quizBtnNext         = document.getElementById('quizBtnNext');
const quizBtnSubmit       = document.getElementById('quizBtnSubmit');
const quizScoreCircle     = document.getElementById('quizScoreCircle');
const quizScoreText       = document.getElementById('quizScoreText');
const quizScoreLabel      = document.getElementById('quizScoreLabel');
const quizResultsList     = document.getElementById('quizResultsList');

const CHOICE_IDS = { a: 'choiceA', b: 'choiceB', c: 'choiceC', d: 'choiceD' };

function quizShowScreen(name) {
  quizScreenLoading.classList.toggle('hidden',   name !== 'loading');
  quizScreenQuestions.classList.toggle('hidden', name !== 'questions');
  quizScreenResults.classList.toggle('hidden',   name !== 'results');
}

function quizOpenModal() {
  quizModal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
  if (quizId && quizQuestions.length) {
    quizShowScreen('questions');
    quizRenderQuestion(quizCurrentIdx);
  } else {
    quizShowScreen('loading');
    quizFetchQuestions();
  }
}

function quizCloseModal() {
  quizModal.classList.add('hidden');
  document.body.style.overflow = '';
}

async function quizFetchQuestions() {
  try {
    const resp = await fetch(D.quizGenerateUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': D.csrfToken, 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      alert(err.error || 'Failed to generate quiz. Please try again.');
      quizCloseModal();
      return;
    }
    const data = await resp.json();
    quizId = data.quiz_id;
    quizQuestions = data.questions;
    quizAnswers = {};
    quizCurrentIdx = 0;
    quizShowScreen('questions');
    quizRenderQuestion(0);
  } catch (e) {
    alert('Could not connect to the quiz service.');
    quizCloseModal();
  }
}

function quizRenderQuestion(idx) {
  const q = quizQuestions[idx];
  const total = quizQuestions.length;

  // Progress
  const pct = Math.round(((idx + 1) / total) * 100);
  quizProgressFill.style.width = pct + '%';
  quizProgressLabel.textContent = `Question ${idx + 1} / ${total}`;

  // Question text
  quizQuestionText.textContent = q.question_text;

  // Choices
  const choiceMap = { a: q.choice_a, b: q.choice_b, c: q.choice_c, d: q.choice_d };
  for (const [letter, elId] of Object.entries(CHOICE_IDS)) {
    const el = document.getElementById(elId);
    el.querySelector('.quiz-choice-text').textContent = choiceMap[letter];
    el.classList.remove('selected');
    el.querySelector('input').checked = false;
  }

  // Restore saved answer
  const saved = quizAnswers[q.order];
  if (saved) {
    const el = document.getElementById(CHOICE_IDS[saved]);
    if (el) {
      el.classList.add('selected');
      el.querySelector('input').checked = true;
    }
  }

  // Nav buttons
  quizBtnPrev.disabled = idx === 0;
  const isLast = idx === total - 1;
  quizBtnNext.classList.toggle('hidden', isLast);
  quizBtnSubmit.classList.toggle('hidden', !isLast);
}

function quizGetSelectedAnswer() {
  for (const [letter, elId] of Object.entries(CHOICE_IDS)) {
    if (document.getElementById(elId).querySelector('input').checked) {
      return letter;
    }
  }
  return null;
}

function quizSaveCurrentAnswer() {
  const q = quizQuestions[quizCurrentIdx];
  const ans = quizGetSelectedAnswer();
  if (ans) quizAnswers[q.order] = ans;
}

async function quizSubmit() {
  quizSaveCurrentAnswer();
  const unanswered = quizQuestions.filter(q => !quizAnswers[q.order]);
  if (unanswered.length) {
    const ok = confirm(`You have ${unanswered.length} unanswered question(s). Submit anyway?`);
    if (!ok) return;
  }
  try {
    const resp = await fetch(`${D.quizSubmitUrl}${quizId}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': D.csrfToken, 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers: quizAnswers }),
    });
    const data = await resp.json();
    quizShowResults(data);
  } catch (e) {
    alert('Failed to submit quiz.');
  }
}

function quizShowResults(data) {
  quizShowScreen('results');

  // Score circle
  const pct = Math.round(data.score * 100);
  quizScoreText.textContent = pct + '%';
  quizScoreCircle.className = 'quiz-score-circle ' +
    (pct >= 70 ? 'score-high' : pct >= 40 ? 'score-mid' : 'score-low');
  quizScoreLabel.textContent = `${data.correct_count} / ${data.total} correct`;

  // Results list
  quizResultsList.innerHTML = '';
  for (const r of data.results) {
    const q = quizQuestions[r.order - 1];
    const item = document.createElement('div');
    item.className = 'quiz-result-item ' + (r.correct ? 'correct' : 'wrong');
    const choiceMap = { a: q.choice_a, b: q.choice_b, c: q.choice_c, d: q.choice_d };
    const correctText = choiceMap[r.correct_choice];
    const userText = r.user_choice ? choiceMap[r.user_choice] : '(no answer)';
    item.innerHTML = `
      <div class="quiz-result-icon">${r.correct ? '✓' : '✗'}</div>
      <div class="quiz-result-detail">
        <div class="quiz-result-q">Q${r.order}. ${q.question_text}</div>
        <div class="quiz-result-ans">
          ${r.correct
            ? `<strong>${r.correct_choice.toUpperCase()}. ${correctText}</strong>`
            : `Your answer: ${r.user_choice ? r.user_choice.toUpperCase() + '. ' + userText : '(none)'}
               &nbsp;·&nbsp; Correct: <strong>${r.correct_choice.toUpperCase()}. ${correctText}</strong>`
          }
        </div>
      </div>`;
    quizResultsList.appendChild(item);
  }
}

/* ── Quiz Event Listeners ── */
document.getElementById('btnOpenQuiz').addEventListener('click', quizOpenModal);
document.getElementById('quizModalClose').addEventListener('click', quizCloseModal);
document.getElementById('quizBtnCloseResults').addEventListener('click', quizCloseModal);

document.getElementById('quizBtnRetake').addEventListener('click', () => {
  quizAnswers = {};
  quizCurrentIdx = 0;
  quizShowScreen('questions');
  quizRenderQuestion(0);
});

quizBtnPrev.addEventListener('click', () => {
  quizSaveCurrentAnswer();
  quizCurrentIdx--;
  quizRenderQuestion(quizCurrentIdx);
});

quizBtnNext.addEventListener('click', () => {
  quizSaveCurrentAnswer();
  quizCurrentIdx++;
  quizRenderQuestion(quizCurrentIdx);
});

quizBtnSubmit.addEventListener('click', quizSubmit);

// Choice click handlers
for (const [letter, elId] of Object.entries(CHOICE_IDS)) {
  document.getElementById(elId).addEventListener('click', () => {
    document.querySelectorAll('.quiz-choice').forEach(el => el.classList.remove('selected'));
    const el = document.getElementById(elId);
    el.classList.add('selected');
    el.querySelector('input').checked = true;
  });
}

// Keyboard shortcuts: A/B/C/D to select, ArrowRight/Enter to next
document.addEventListener('keydown', (e) => {
  if (quizModal.classList.contains('hidden')) return;
  if (quizScreenQuestions.classList.contains('hidden')) return;
  const key = e.key.toLowerCase();
  if (['a', 'b', 'c', 'd'].includes(key)) {
    e.preventDefault();
    document.getElementById(CHOICE_IDS[key]).click();
  } else if ((e.key === 'ArrowRight' || e.key === 'Enter') && !quizBtnNext.classList.contains('hidden')) {
    e.preventDefault();
    quizBtnNext.click();
  } else if (e.key === 'ArrowLeft' && !quizBtnPrev.disabled) {
    e.preventDefault();
    quizBtnPrev.click();
  } else if (e.key === 'Escape') {
    quizCloseModal();
  }
});

// Close on overlay click
quizModal.addEventListener('click', (e) => {
  if (e.target === quizModal) quizCloseModal();
});
```

- [ ] **Step 2: Commit**

```bash
git add static/js/dictation.js
git commit -m "feat(dictation): add comprehension quiz modal JS logic"
```

---

## Task 7: Smoke Test End-to-End

- [ ] **Step 1: Run all dictation quiz tests**

```bash
python manage.py test tests.test_dictation_quiz -v 2
```

Expected: all tests PASS, 0 errors.

- [ ] **Step 2: Run server and manually verify**

```bash
python manage.py runserver
```

1. Navigate to any processed dictation video: `http://localhost:8000/dictation/<video_id>/`
2. Click "Comprehension Quiz" button — loading spinner should appear
3. After ~10–30s (or instantly if cached), 10 questions appear
4. Click choices with mouse and A/B/C/D keyboard shortcuts
5. Navigate with Previous/Next and arrow keys
6. Submit — results screen shows score and per-question breakdown
7. Click "Retake Quiz" — questions reset, same set
8. Click "Close" — modal closes cleanly
9. Re-open modal — loads from cache instantly (no spinner)

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat(dictation): complete comprehension quiz feature with TOEIC-style questions"
```
