"""
YouTube subtitle extraction and smart segmentation service.
"""
import re
from urllib.parse import urlparse, parse_qs


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    url = url.strip()

    # youtu.be/VIDEO_ID
    match = re.match(r'(?:https?://)?youtu\.be/([A-Za-z0-9_-]{11})', url)
    if match:
        return match.group(1)

    # youtube.com/watch?v=VIDEO_ID
    match = re.match(r'(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=([A-Za-z0-9_-]{11})', url)
    if match:
        return match.group(1)

    # youtube.com/shorts/VIDEO_ID
    match = re.match(r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]{11})', url)
    if match:
        return match.group(1)

    # youtube.com/embed/VIDEO_ID
    match = re.match(r'(?:https?://)?(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]{11})', url)
    if match:
        return match.group(1)

    return None


def fetch_subtitles(video_id: str) -> tuple[list, str]:
    """
    Fetch subtitles for a YouTube video.
    Prioritises official CC over auto-generated captions.

    Returns:
        (entries, source) where entries is a list of dicts {text, start, duration}
        and source is 'cc' or 'auto'.

    Raises:
        Exception if no English subtitles available.
    """
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

    api = YouTubeTranscriptApi()
    transcript_list_obj = api.list(video_id)

    # Try manual/CC transcript first
    try:
        transcript = transcript_list_obj.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
        return _to_dicts(transcript.fetch()), 'cc'
    except NoTranscriptFound:
        pass

    # Fallback to auto-generated
    try:
        transcript = transcript_list_obj.find_generated_transcript(['en', 'en-US', 'en-GB'])
        return _to_dicts(transcript.fetch()), 'auto'
    except NoTranscriptFound:
        pass

    raise Exception('No English subtitles found for this video.')


def _to_dicts(fetched) -> list:
    """Normalise FetchedTranscript (v1.x objects) or list-of-dicts (v0.x) to list of dicts."""
    result = []
    for entry in fetched:
        if isinstance(entry, dict):
            result.append(entry)
        else:
            # v1.x FetchedTranscriptSnippet object
            result.append({
                'text': entry.text,
                'start': entry.start,
                'duration': entry.duration,
            })
    return result


def _ends_sentence(text: str) -> bool:
    """Return True if text ends with a sentence-ending punctuation mark."""
    stripped = text.rstrip()
    return bool(stripped) and stripped[-1] in '.?!'


def _clean_text(text: str) -> str:
    """Remove HTML tags and extra whitespace from transcript text."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def build_segments(
    transcript_entries: list,
    max_duration: float = 12.0,
    min_duration: float = 4.0,
) -> list[dict]:
    """
    Merge individual transcript entries into sensible dictation segments.

    Rules:
    - Flush a segment when accumulated duration >= max_duration
    - Flush early (>= min_duration) if the last entry ends a sentence (. ? !)
    - Never produce an empty segment

    Returns list of dicts: {order, start_time, end_time, transcript, word_count}
    """
    segments = []
    current_text_parts = []
    current_start = None
    current_end = None
    current_duration = 0.0

    def flush(order_idx):
        nonlocal current_text_parts, current_start, current_end, current_duration
        if not current_text_parts:
            return
        text = ' '.join(current_text_parts).strip()
        word_count = len(text.split())
        segments.append({
            'order': order_idx,
            'start_time': round(current_start, 3),
            'end_time': round(current_end, 3),
            'transcript': text,
            'word_count': word_count,
        })
        current_text_parts = []
        current_start = None
        current_end = None
        current_duration = 0.0

    order = 1
    for entry in transcript_entries:
        text = _clean_text(entry.get('text', ''))
        if not text:
            continue

        start = float(entry.get('start', 0))
        duration = float(entry.get('duration', 0))
        end = start + duration

        if current_start is None:
            current_start = start

        current_text_parts.append(text)
        current_end = end
        current_duration = current_end - current_start

        # Decide whether to flush
        if current_duration >= max_duration:
            flush(order)
            order += 1
        elif current_duration >= min_duration and _ends_sentence(text):
            flush(order)
            order += 1

    # Flush remainder
    flush(order)

    return segments
