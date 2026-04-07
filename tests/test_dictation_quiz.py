"""Tests for dictation comprehension quiz service and views."""
import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from dictation.quiz_service import _parse_questions

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
