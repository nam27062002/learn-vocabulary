"""Tests for dictation comprehension quiz service and views."""
import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from dictation.quiz_service import _parse_questions
from dictation.models import DictationVideo, DictationSegment, VideoQuiz, QuizQuestion, UserQuizAttempt

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
        self.assertNotIn('correct_choice', data['questions'][0])
        self.assertTrue(VideoQuiz.objects.filter(video=self.video).exists())

    @patch('dictation.views.generate_quiz_questions')
    def test_second_call_returns_from_cache(self, mock_gen):
        mock_gen.return_value = self._make_fake_questions()
        self.client.post(f'/api/dictation/quiz/generate/{self.video.video_id}/')
        self.client.post(f'/api/dictation/quiz/generate/{self.video.video_id}/')
        self.assertEqual(mock_gen.call_count, 1)

    @patch('dictation.views.generate_quiz_questions')
    def test_generate_returns_cached_on_second_request(self, mock_gen):
        mock_gen.return_value = self._make_fake_questions()
        self.client.post(f'/api/dictation/quiz/generate/{self.video.video_id}/')
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
