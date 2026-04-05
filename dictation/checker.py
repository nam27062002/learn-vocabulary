"""
LCS-based word-level answer checker for dictation practice.
"""
import re


_STRIP_PUNCT = re.compile(r"[.,!?;:'\"\-\(\)\[\]]")


def normalize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into words."""
    text = text.lower()
    text = _STRIP_PUNCT.sub('', text)
    return [w for w in text.split() if w]


def _lcs_table(a: list, b: list) -> list[list[int]]:
    """Build LCS dynamic programming table."""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp


def _backtrack(dp: list[list[int]], ref: list, user: list) -> list[tuple]:
    """
    Backtrack through LCS table to produce alignment.
    Returns list of (ref_word_or_None, user_word_or_None).
    """
    alignment = []
    i, j = len(ref), len(user)
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == user[j - 1]:
            alignment.append((ref[i - 1], user[j - 1]))
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
            alignment.append((None, user[j - 1]))  # extra word
            j -= 1
        else:
            alignment.append((ref[i - 1], None))   # missing word
            i -= 1
    alignment.reverse()
    return alignment


def compare(reference: str, user_input: str) -> dict:
    """
    Compare user input against reference transcript using LCS alignment.

    Returns:
    {
        "score": float,          # correct_count / len(ref_words)
        "correct_count": int,
        "total_count": int,      # len(ref_words)
        "tokens": [
            {
                "word": str,         # reference word (or user word if extra)
                "status": str,       # 'correct' | 'wrong' | 'missing' | 'extra'
                "user_word": str|None
            },
            ...
        ]
    }
    """
    ref_words = normalize(reference)
    user_words = normalize(user_input)

    if not ref_words:
        return {"score": 1.0, "correct_count": 0, "total_count": 0, "tokens": []}

    if not user_words:
        tokens = [{"word": w, "status": "missing", "user_word": None} for w in ref_words]
        return {"score": 0.0, "correct_count": 0, "total_count": len(ref_words), "tokens": tokens}

    dp = _lcs_table(ref_words, user_words)
    alignment = _backtrack(dp, ref_words, user_words)

    tokens = []
    correct_count = 0

    for ref_w, user_w in alignment:
        if ref_w is not None and user_w is not None:
            # Both present and equal (LCS match)
            tokens.append({"word": ref_w, "status": "correct", "user_word": user_w})
            correct_count += 1
        elif ref_w is None:
            # Extra word typed by user
            tokens.append({"word": user_w, "status": "extra", "user_word": user_w})
        else:
            # ref_w present, user_w missing
            tokens.append({"word": ref_w, "status": "missing", "user_word": None})

    # Post-process: pair adjacent missing+extra as substitutions
    # so "talk" vs "look" shows as 'wrong' rather than missing + extra
    merged = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t['status'] == 'missing' and i + 1 < len(tokens) and tokens[i + 1]['status'] == 'extra':
            merged.append({
                "word": t['word'],
                "status": "wrong",
                "user_word": tokens[i + 1]['user_word'],
            })
            i += 2
        elif t['status'] == 'extra' and i + 1 < len(tokens) and tokens[i + 1]['status'] == 'missing':
            merged.append({
                "word": tokens[i + 1]['word'],
                "status": "wrong",
                "user_word": t['user_word'],
            })
            i += 2
        else:
            merged.append(t)
            i += 1

    score = correct_count / len(ref_words) if ref_words else 1.0

    return {
        "score": round(score, 4),
        "correct_count": correct_count,
        "total_count": len(ref_words),
        "tokens": merged,
    }
