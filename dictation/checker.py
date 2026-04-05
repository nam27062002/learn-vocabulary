"""
LCS-based word-level answer checker for dictation practice.
Includes proper-noun leniency via fuzzy matching.
"""
import re
from difflib import SequenceMatcher


_STRIP_PUNCT = re.compile(r"[.,!?;:'\"\-\(\)\[\]]")


# ── Normalisation ──────────────────────────────────────────────────────────

def normalize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into words."""
    text = text.lower()
    text = _STRIP_PUNCT.sub('', text)
    return [w for w in text.split() if w]


# ── Proper-noun detection ──────────────────────────────────────────────────

def _get_proper_noun_set(reference_raw: str) -> set[str]:
    """
    Return the lowercased forms of words that are likely proper nouns.

    Heuristic: a word is a proper noun candidate when
      - it starts with an uppercase letter, AND
      - it is NOT the first word of a sentence (i.e. not preceded by . ? !), AND
      - it is not the word "I" (common exception).

    Returns a set of lowercased strings so we can do O(1) lookups on
    normalized tokens.
    """
    proper: set[str] = set()
    words = reference_raw.split()
    sentence_start = True  # first word of text is always a sentence starter

    for word in words:
        alpha_only = re.sub(r"[^a-zA-Z']", '', word)
        if not alpha_only:
            # Punctuation-only token — advance sentence boundary detection
            if re.search(r'[.?!]', word):
                sentence_start = True
            continue

        if (
            not sentence_start
            and alpha_only[0].isupper()
            and alpha_only.lower() != 'i'
        ):
            proper.add(alpha_only.lower())

        # Was this word a sentence-ender?
        sentence_start = bool(re.search(r'[.?!]["\']?$', word))

    return proper


def _similar(a: str, b: str, threshold: float = 0.72) -> bool:
    """True if two strings are sufficiently similar (for proper-noun leniency)."""
    if not a or not b:
        return False
    return SequenceMatcher(None, a, b).ratio() >= threshold


# ── LCS table + backtracking ───────────────────────────────────────────────

def _lcs_table(a: list, b: list) -> list[list[int]]:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp


def _backtrack(dp, ref, user):
    alignment = []
    i, j = len(ref), len(user)
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == user[j - 1]:
            alignment.append((ref[i - 1], user[j - 1]))
            i -= 1; j -= 1
        elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
            alignment.append((None, user[j - 1]))  # extra
            j -= 1
        else:
            alignment.append((ref[i - 1], None))   # missing
            i -= 1
    alignment.reverse()
    return alignment


# ── Main compare ───────────────────────────────────────────────────────────

def compare(reference: str, user_input: str) -> dict:
    """
    Compare user input against reference transcript.

    Statuses per token:
      'correct'  — exact match
      'proper'   — proper noun accepted via fuzzy match (counts as correct)
      'wrong'    — substitution (incorrect)
      'missing'  — word absent from user input
      'extra'    — word typed by user that has no match in reference

    Returns:
    {
        "score":         float,   # correct_count / total_ref_words
        "correct_count": int,
        "total_count":   int,
        "proper_count":  int,     # how many were accepted as proper nouns
        "tokens":        list[dict],
        "transcript":    str,     # reference (added by view)
    }
    """
    ref_words  = normalize(reference)
    user_words = normalize(user_input)
    proper_set = _get_proper_noun_set(reference)

    if not ref_words:
        return {"score": 1.0, "correct_count": 0, "total_count": 0,
                "proper_count": 0, "tokens": []}

    if not user_words:
        tokens = [{"word": w, "status": "missing", "user_word": None,
                   "is_proper": w in proper_set} for w in ref_words]
        return {"score": 0.0, "correct_count": 0, "total_count": len(ref_words),
                "proper_count": 0, "tokens": tokens}

    dp        = _lcs_table(ref_words, user_words)
    alignment = _backtrack(dp, ref_words, user_words)

    # Raw tokens before substitution merging
    raw: list[dict] = []
    correct_count = 0
    for ref_w, user_w in alignment:
        if ref_w is not None and user_w is not None:
            raw.append({"word": ref_w, "status": "correct",
                        "user_word": user_w, "is_proper": ref_w in proper_set})
            correct_count += 1
        elif ref_w is None:
            raw.append({"word": user_w, "status": "extra",
                        "user_word": user_w, "is_proper": False})
        else:
            raw.append({"word": ref_w, "status": "missing",
                        "user_word": None, "is_proper": ref_w in proper_set})

    # Merge adjacent missing+extra into substitutions
    merged: list[dict] = []
    i = 0
    while i < len(raw):
        t = raw[i]
        nxt = raw[i + 1] if i + 1 < len(raw) else None

        if t['status'] == 'missing' and nxt and nxt['status'] == 'extra':
            merged.append({"word": t['word'], "status": "wrong",
                           "user_word": nxt['user_word'], "is_proper": t['is_proper']})
            i += 2
        elif t['status'] == 'extra' and nxt and nxt['status'] == 'missing':
            merged.append({"word": nxt['word'], "status": "wrong",
                           "user_word": t['user_word'], "is_proper": nxt['is_proper']})
            i += 2
        else:
            merged.append(t)
            i += 1

    # Proper-noun leniency pass — only for 'wrong' tokens
    proper_count = 0
    for tok in merged:
        if (
            tok['status'] == 'wrong'
            and tok['is_proper']
            and tok['user_word'] is not None
            and _similar(tok['word'], tok['user_word'])
        ):
            tok['status'] = 'proper'
            correct_count += 1
            proper_count  += 1

    score = round(correct_count / len(ref_words), 4) if ref_words else 1.0

    return {
        "score":         score,
        "correct_count": correct_count,
        "total_count":   len(ref_words),
        "proper_count":  proper_count,
        "tokens":        merged,
    }
