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
