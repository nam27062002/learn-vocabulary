import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .checker import compare
from .models import DictationAttempt, DictationSegment, DictationVideo, VideoQuiz, QuizQuestion, UserQuizAttempt
from .quiz_service import generate_quiz_questions
from .youtube_service import build_segments, extract_video_id, fetch_subtitles

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Page views
# ---------------------------------------------------------------------------

@login_required
def video_list(request):
    videos = DictationVideo.objects.filter(is_processed=True).select_related('added_by')
    return render(request, 'dictation/video_list.html', {'videos': videos})


@login_required
def practice(request, video_id):
    video = get_object_or_404(DictationVideo, video_id=video_id, is_processed=True)
    segments = list(video.segments.values('id', 'order', 'start_time', 'end_time', 'word_count'))
    return render(request, 'dictation/practice.html', {
        'video': video,
        'segments_json': json.dumps(segments),
    })


# ---------------------------------------------------------------------------
# API: Process a YouTube video URL
# ---------------------------------------------------------------------------

@login_required
@require_POST
def api_process_video(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    url = data.get('url', '').strip()
    if not url:
        return JsonResponse({'error': 'URL is required'}, status=400)

    video_id = extract_video_id(url)
    if not video_id:
        return JsonResponse({'error': 'Could not parse YouTube video ID from URL'}, status=400)

    # Return existing video if already processed
    existing = DictationVideo.objects.filter(video_id=video_id, is_processed=True).first()
    if existing:
        return JsonResponse({
            'video_id': existing.video_id,
            'title': existing.title,
            'segment_count': existing.segment_count,
            'already_exists': True,
        })

    # Fetch subtitles
    try:
        transcript_entries, source = fetch_subtitles(video_id)
    except Exception as e:
        logger.warning('Subtitle fetch failed for %s: %s', video_id, e)
        return JsonResponse({'error': str(e)}, status=422)

    # Duration warning (>30 min)
    total_duration = sum(float(e.get('duration', 0)) for e in transcript_entries)
    if total_duration > 1800:
        if not data.get('confirm_long'):
            minutes = int(total_duration // 60)
            return JsonResponse({
                'warning': f'This video is {minutes} minutes long and will generate many segments. '
                           f'Re-submit with confirm_long=true to proceed.',
                'duration_seconds': int(total_duration),
            }, status=200)

    # Build segments
    segment_dicts = build_segments(transcript_entries)
    if not segment_dicts:
        return JsonResponse({'error': 'No segments could be extracted from subtitles'}, status=422)

    # Fetch video metadata via oembed (no API key needed)
    title, thumbnail, channel = _fetch_oembed_metadata(video_id)

    # Persist video
    video_obj, _ = DictationVideo.objects.get_or_create(
        video_id=video_id,
        defaults={
            'title': title,
            'thumbnail_url': thumbnail,
            'channel_name': channel,
            'duration_seconds': int(total_duration) if total_duration else None,
            'subtitle_source': source,
            'added_by': request.user,
            'segment_count': len(segment_dicts),
            'is_processed': True,
        },
    )

    # Persist segments (bulk create for speed)
    segment_objs = [
        DictationSegment(
            video=video_obj,
            order=s['order'],
            start_time=s['start_time'],
            end_time=s['end_time'],
            transcript=s['transcript'],
            word_count=s['word_count'],
        )
        for s in segment_dicts
    ]
    DictationSegment.objects.bulk_create(segment_objs, ignore_conflicts=True)

    # Update counts in case video already existed without segments
    video_obj.segment_count = len(segment_dicts)
    video_obj.is_processed = True
    video_obj.save(update_fields=['segment_count', 'is_processed'])

    return JsonResponse({
        'video_id': video_obj.video_id,
        'title': video_obj.title,
        'thumbnail_url': video_obj.thumbnail_url,
        'channel_name': video_obj.channel_name,
        'segment_count': len(segment_dicts),
        'subtitle_source': source,
        'already_exists': False,
    })


def _fetch_oembed_metadata(video_id: str) -> tuple[str, str, str]:
    """Fetch video title and thumbnail via YouTube oembed (no API key needed)."""
    import requests
    try:
        resp = requests.get(
            'https://www.youtube.com/oembed',
            params={'url': f'https://www.youtube.com/watch?v={video_id}', 'format': 'json'},
            timeout=5,
        )
        if resp.ok:
            data = resp.json()
            title = data.get('title', video_id)
            thumbnail = data.get('thumbnail_url', '')
            channel = data.get('author_name', '')
            return title, thumbnail, channel
    except Exception:
        pass
    return video_id, '', ''


# ---------------------------------------------------------------------------
# API: Get segments for a video
# ---------------------------------------------------------------------------

@login_required
@require_GET
def api_get_segments(request, video_id):
    video = get_object_or_404(DictationVideo, video_id=video_id, is_processed=True)
    segments = list(video.segments.values('id', 'order', 'start_time', 'end_time', 'word_count'))
    return JsonResponse({'segments': segments})


# ---------------------------------------------------------------------------
# API: Check answer
# ---------------------------------------------------------------------------

@login_required
@require_POST
def api_check_answer(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    segment_id = data.get('segment_id')
    user_input = data.get('user_input', '')

    if not segment_id:
        return JsonResponse({'error': 'segment_id is required'}, status=400)

    segment = get_object_or_404(DictationSegment, id=segment_id)
    result = compare(segment.transcript, user_input)
    result['transcript'] = segment.transcript  # for "show answer"
    return JsonResponse(result)


# ---------------------------------------------------------------------------
# API: Save attempt
# ---------------------------------------------------------------------------

@login_required
@require_POST
def api_save_attempt(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    segment_id = data.get('segment_id')
    user_input = data.get('user_input', '')
    score = data.get('score')
    revealed = bool(data.get('revealed_answer', False))

    if segment_id is None or score is None:
        return JsonResponse({'error': 'segment_id and score are required'}, status=400)

    segment = get_object_or_404(DictationSegment, id=segment_id)

    attempt = DictationAttempt.objects.create(
        user=request.user,
        segment=segment,
        user_input=user_input,
        score=float(score),
        revealed_answer=revealed,
    )

    return JsonResponse({'id': attempt.id, 'score': attempt.score})


# ---------------------------------------------------------------------------
# API: Get user progress for a video
# ---------------------------------------------------------------------------

@login_required
@require_GET
def api_get_progress(request, video_id):
    video = get_object_or_404(DictationVideo, video_id=video_id, is_processed=True)
    segment_ids = video.segments.values_list('id', flat=True)

    # Latest attempt per segment for this user (SQLite-compatible)
    from django.db.models import Max

    latest_times = (
        DictationAttempt.objects
        .filter(user=request.user, segment_id__in=segment_ids)
        .values('segment_id')
        .annotate(latest=Max('created_at'))
    )
    time_map = {row['segment_id']: row['latest'] for row in latest_times}

    progress = {}
    for seg_id, ts in time_map.items():
        attempt = (
            DictationAttempt.objects
            .filter(user=request.user, segment_id=seg_id, created_at=ts)
            .values('score', 'revealed_answer')
            .first()
        )
        if attempt:
            progress[seg_id] = {
                'score': attempt['score'],
                'revealed': attempt['revealed_answer'],
            }

    return JsonResponse({'progress': progress})


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
