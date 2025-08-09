from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import Flashcard, Definition, Deck, StudySession, StudySessionAnswer, IncorrectWordReview, FavoriteFlashcard # Import Deck model
from django.conf import settings # Import settings
from .api_services import get_word_suggestions_from_datamuse, check_word_spelling_with_languagetool # Import new service functions
from .word_details_service import get_word_details # Import the new service function
from googletrans import Translator
import requests
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone
import os
import json
import sys
from django.contrib.auth.decorators import login_required
from deep_translator import GoogleTranslator
from django.db.models.functions import Random

# Difficulty-Based Card Selection Configuration
SPACED_REPETITION_CONFIG = {
    'MAX_DAILY_REVIEWS': 5,          # Maximum times a card can be shown per day (increased for difficulty-based)
    'SIMILARITY_THRESHOLD': 0.6,     # Threshold for semantic similarity filtering
    'MIN_DISTRACTORS': 10,          # Minimum distractors to collect for filtering
    # Difficulty selection weights (used in _get_next_card_enhanced)
    'DIFFICULTY_WEIGHTS': {
        'again': 40,  # Again cards (highest difficulty) - 40% selection weight
        'hard': 30,   # Hard cards - 30% selection weight
        'good': 20,   # Good cards - 20% selection weight
        'easy': 10,   # Easy cards (lowest difficulty) - 10% selection weight
        'new': 35,    # New cards (never reviewed) - 35% selection weight
    }
}
import random
from .statistics_utils import create_study_session, record_answer, end_study_session

# Helper function to filter semantically similar distractors
def _filter_semantic_distractors(correct_word, candidates):
    """
    Filter out distractors that are too similar to the correct word.
    This improves multiple choice question quality by avoiding confusing options.
    """
    import difflib

    correct_word_lower = correct_word.lower()
    filtered = []

    for candidate in candidates:
        candidate_lower = candidate.lower()

        # Skip if words are too similar (edit distance)
        similarity = difflib.SequenceMatcher(None, correct_word_lower, candidate_lower).ratio()
        if similarity > SPACED_REPETITION_CONFIG['SIMILARITY_THRESHOLD']:
            continue

        # Skip if one word is contained in another
        if (correct_word_lower in candidate_lower or
            candidate_lower in correct_word_lower):
            continue

        # Skip if words start with the same 3+ characters (too similar)
        if (len(correct_word_lower) >= 3 and len(candidate_lower) >= 3 and
            correct_word_lower[:3] == candidate_lower[:3]):
            continue

        filtered.append(candidate)

        # Stop when we have enough good distractors
        if len(filtered) >= SPACED_REPETITION_CONFIG['MIN_DISTRACTORS']:
            break

    return filtered

# Difficulty-based card selection algorithm (replaces SM-2)
def _get_next_card_enhanced(user, deck_ids=None):
    """
    Difficulty-based card selection algorithm that prioritizes cards based on their difficulty levels.
    Shows harder cards more frequently than easier ones while maintaining variety.

    Difficulty Levels (stored in difficulty_score field):
    - 0.0 (Again): Highest difficulty - 40% selection weight
    - 0.33 (Hard): High difficulty - 30% selection weight
    - 0.67 (Good): Medium difficulty - 20% selection weight
    - 1.0 (Easy): Low difficulty - 10% selection weight
    """
    from django.db.models import Case, When, FloatField, Q
    from django.db.models.functions import Random
    from datetime import datetime
    import random

    today = datetime.now().date()

    # Base queryset
    qs = Flashcard.objects.filter(user=user)
    if deck_ids:
        qs = qs.filter(deck_id__in=deck_ids)

    # Reset daily counters if needed
    qs.filter(last_seen_date__lt=today).update(times_seen_today=0)

    # Apply daily limit filter
    available_cards = qs.filter(times_seen_today__lt=SPACED_REPETITION_CONFIG['MAX_DAILY_REVIEWS'])

    if not available_cards.exists():
        # If all cards hit daily limit, relax the constraint
        available_cards = qs.filter(times_seen_today__lt=SPACED_REPETITION_CONFIG['MAX_DAILY_REVIEWS'] + 2)
        if not available_cards.exists():
            return qs.order_by(Random()).first()  # Last resort

    # Create difficulty-based priority groups
    difficulty_groups = {
        'again': available_cards.filter(difficulty_score=0.0),      # Again (highest priority)
        'hard': available_cards.filter(difficulty_score=0.33),      # Hard
        'good': available_cards.filter(difficulty_score=0.67),      # Good
        'easy': available_cards.filter(difficulty_score=1.0),       # Easy (lowest priority)
        'new': available_cards.filter(difficulty_score__isnull=True)  # New cards (never reviewed)
    }

    # Define selection weights (higher = more likely to be selected)
    selection_weights = [
        ('again', 40),  # 40% chance for Again cards
        ('hard', 30),   # 30% chance for Hard cards
        ('good', 20),   # 20% chance for Good cards
        ('easy', 10),   # 10% chance for Easy cards
        ('new', 35),    # 35% chance for new cards (high priority for learning)
    ]

    # Build weighted selection pool
    weighted_pool = []
    for difficulty_level, weight in selection_weights:
        cards = difficulty_groups[difficulty_level]
        if cards.exists():
            # Add this difficulty level to the pool with its weight
            for _ in range(weight):
                weighted_pool.append(difficulty_level)

    if not weighted_pool:
        # No cards available, return any card
        return available_cards.order_by(Random()).first()

    # Randomly select a difficulty level based on weights
    selected_difficulty = random.choice(weighted_pool)
    selected_group = difficulty_groups[selected_difficulty]

    print(f"CARD SELECTION: Selected difficulty '{selected_difficulty}' from {len(weighted_pool)} weighted options", file=sys.stderr)
    print(f"CARD SELECTION: Available cards in '{selected_difficulty}': {selected_group.count()}", file=sys.stderr)

    # Return a random card from the selected difficulty group
    return selected_group.order_by(Random()).first()

# Helper to update tracking when card is shown
def _update_card_shown_tracking(card):
    """Update tracking fields when a card is shown to the user."""
    from datetime import datetime

    today = datetime.now().date()

    # Update daily tracking
    if card.last_seen_date != today:
        card.times_seen_today = 1
        card.last_seen_date = today
    else:
        card.times_seen_today += 1

    card.save(update_fields=['times_seen_today', 'last_seen_date'])

# Helper for difficulty-based card update (replaces SM-2)
def _update_card_difficulty(card, correct: bool, grade: int = None):
    """
    Update card difficulty based on user performance and feedback.
    Uses a 4-level difficulty system instead of SM-2 spaced repetition.

    Difficulty Levels:
    - 0 (Again): Highest difficulty - show most frequently
    - 1 (Hard): High difficulty - show frequently
    - 2 (Good): Medium difficulty - show moderately
    - 3 (Easy): Low difficulty - show least frequently
    """
    from datetime import datetime

    # Update review tracking fields
    card.total_reviews += 1
    if correct:
        card.correct_reviews += 1

    # Determine difficulty level based on grade or correctness
    if grade is not None:
        # Use explicit grade from user feedback (0-3)
        difficulty_level = grade
        print(f"DIFFICULTY UPDATE: Using grade {grade} -> difficulty_level={difficulty_level}", file=sys.stderr)
    else:
        # Default mapping for correct/incorrect answers
        if correct:
            difficulty_level = 2  # Good (medium difficulty)
        else:
            difficulty_level = 0  # Again (highest difficulty)
        print(f"DIFFICULTY UPDATE: Using correct={correct} -> difficulty_level={difficulty_level}", file=sys.stderr)

    # Store the difficulty level (0-3) in the difficulty_score field
    # We'll repurpose this field: 0.0=Again, 0.33=Hard, 0.67=Good, 1.0=Easy
    difficulty_score_mapping = {
        0: 0.0,   # Again (highest difficulty)
        1: 0.33,  # Hard
        2: 0.67,  # Good
        3: 1.0    # Easy (lowest difficulty)
    }

    card.difficulty_score = difficulty_score_mapping.get(difficulty_level, 0.0)

    # Update timestamp
    card.last_reviewed = datetime.now()

    # Clear SM-2 fields (no longer used)
    card.ease_factor = 2.5  # Reset to default
    card.repetitions = 0    # Not used
    card.interval = 0       # Not used
    card.next_review = datetime.now().date()  # Always available

    print(f"DIFFICULTY UPDATE: Card '{card.word}' set to difficulty_score={card.difficulty_score} (level {difficulty_level})", file=sys.stderr)

    card.save()


@login_required
@require_GET
def api_next_question(request):
    import random as _rnd
    MODES = ['mc', 'type', 'dictation']
    deck_ids = request.GET.getlist('deck_ids[]')
    study_mode = request.GET.get('study_mode', 'decks')
    word_count = int(request.GET.get('word_count', 10))
    seen_card_ids = request.GET.getlist('seen_card_ids[]')

    # Convert seen_card_ids to integers
    seen_card_ids = [int(cid) for cid in seen_card_ids if cid.isdigit()]

    # Get or create current study session
    current_session = request.session.get('current_study_session_id')
    if not current_session:
        # Create new study session
        if study_mode == 'random':
            session_mode = 'random'
        elif study_mode == 'favorites':
            session_mode = 'favorites'
        else:
            session_mode = 'deck'
        session = create_study_session(request.user, session_mode, deck_ids if session_mode == 'deck' else None)
        request.session['current_study_session_id'] = session.id
        request.session['session_start_time'] = timezone.now().timestamp()
    else:
        try:
            session = StudySession.objects.get(id=current_session, user=request.user)
        except StudySession.DoesNotExist:
            # Session doesn't exist, create new one
            if study_mode == 'random':
                session_mode = 'random'
            elif study_mode == 'favorites':
                session_mode = 'favorites'
            else:
                session_mode = 'deck'
            session = create_study_session(request.user, session_mode, deck_ids if session_mode == 'deck' else None)
            request.session['current_study_session_id'] = session.id
            request.session['session_start_time'] = timezone.now().timestamp()

    if study_mode == 'random':
        # Random study mode: select random words from entire vocabulary
        available_cards = Flashcard.objects.filter(user=request.user).exclude(id__in=seen_card_ids)

        if not available_cards.exists():
            return JsonResponse({'done': True})

        # Get random card
        card = available_cards.order_by('?').first()

        # Update tracking fields when card is shown
        _update_card_shown_tracking(card)
    elif study_mode == 'favorites':
        # Favorites study mode: select from user's favorite flashcards
        favorite_cards = FavoriteFlashcard.objects.filter(
            user=request.user
        ).select_related('flashcard').exclude(flashcard_id__in=seen_card_ids)

        if not favorite_cards.exists():
            return JsonResponse({'done': True, 'message': 'No favorite cards available'})

        # Get random favorite card
        favorite_card = favorite_cards.order_by('?').first()
        card = favorite_card.flashcard

        # Update tracking fields when card is shown
        _update_card_shown_tracking(card)
    elif study_mode == 'review':
        # Review incorrect words mode: select from incorrect words list
        # First, check if there are any unresolved incorrect words at all
        total_incorrect_words = IncorrectWordReview.objects.filter(
            user=request.user,
            is_resolved=False
        ).count()

        print(f"Total unresolved incorrect words: {total_incorrect_words}", file=sys.stderr)

        if total_incorrect_words == 0:
            # All incorrect words have been resolved - session complete!
            print("Review session completed - all words resolved!", file=sys.stderr)
            return JsonResponse({
                'done': True,
                'session_completed': True,
                'message': 'All incorrect words have been successfully reviewed!'
            })

        # Get incorrect words excluding those already seen in this session
        incorrect_words = IncorrectWordReview.objects.filter(
            user=request.user,
            is_resolved=False
        ).exclude(flashcard_id__in=seen_card_ids).select_related('flashcard')

        if not incorrect_words.exists():
            # If no more unseen incorrect words, loop back to all incorrect words
            print("Looping back to start of review session", file=sys.stderr)
            incorrect_words = IncorrectWordReview.objects.filter(
                user=request.user,
                is_resolved=False
            ).select_related('flashcard')

            # Double-check that we still have words (this should not happen due to check above)
            if not incorrect_words.exists():
                print("No incorrect words found in loop-back - session complete!", file=sys.stderr)
                return JsonResponse({
                    'done': True,
                    'session_completed': True,
                    'message': 'All incorrect words have been successfully reviewed!'
                })

        # Get a random incorrect word
        incorrect_word = incorrect_words.order_by('?').first()

        if not incorrect_word:
            print("No incorrect word found - this should not happen!", file=sys.stderr)
            return JsonResponse({
                'done': True,
                'session_completed': True,
                'message': 'No incorrect words found!'
            })

        card = incorrect_word.flashcard

        # Store the original question type for this review session
        original_question_type = incorrect_word.question_type

        print(f"Selected word for review: {card.word} (type: {original_question_type})", file=sys.stderr)

        # Update tracking fields when card is shown
        _update_card_shown_tracking(card)
    else:
        # Normal study mode: use enhanced card selection algorithm
        card = _get_next_card_enhanced(request.user, deck_ids)
        if not card:
            return JsonResponse({'done': True})

    # Check if card has audio for dictation mode
    has_audio = card.audio_url and card.audio_url.strip()

    # Determine question type based on study mode
    if study_mode == 'review':
        # For review mode, use the original question type where the error occurred
        mode = original_question_type

        # Fallback if dictation mode but no audio available
        if mode == 'dictation' and not has_audio:
            mode = 'type'  # Fallback to input mode
    else:
        # For other modes, determine available modes based on audio availability
        available_modes = ['mc', 'type']
        if has_audio:
            available_modes.append('dictation')

        # Select random mode from available options
        mode = _rnd.choice(available_modes)

        # For dictation mode, ensure we have audio
        if mode == 'dictation' and not has_audio:
            mode = _rnd.choice(['mc', 'type'])

    defs = list(card.definitions.values('english_definition', 'vietnamese_definition'))

    payload = {
        'done': False,
        'question': {
            'id': card.id,
            'word': card.word,
            'phonetic': card.phonetic,
            'part_of_speech': card.part_of_speech,
            'image_url': card.image.url if card.image else card.related_image_url,
            'audio_url': card.audio_url,
            'definitions': defs,
        }
    }

    if mode == 'mc':
        # Build 3 distractors from ALL user's words (not just selected decks)
        distractors = Flashcard.objects.filter(user=request.user).exclude(id=card.id)

        # Get more candidates to improve semantic filtering
        distractor_candidates = list(distractors.values_list('word', flat=True)[:50])
        random.shuffle(distractor_candidates)

        # Filter out semantically similar words to improve question quality
        filtered_distractors = _filter_semantic_distractors(card.word, distractor_candidates)

        # Take the first 3 filtered distractors, or fall back to random if not enough
        final_distractors = filtered_distractors[:3]
        if len(final_distractors) < 3:
            # Fill remaining slots with random words if semantic filtering didn't provide enough
            remaining_candidates = [w for w in distractor_candidates if w not in final_distractors]
            final_distractors.extend(remaining_candidates[:3-len(final_distractors)])

        options = [card.word] + final_distractors[:3]
        random.shuffle(options)
        payload['question']['options'] = options
        payload['question']['type'] = 'mc'
    elif mode == 'dictation':
        payload['question']['type'] = 'dictation'
        payload['question']['answer'] = card.word
    else:
        payload['question']['type'] = 'type'
        payload['question']['answer'] = card.word

    return JsonResponse(payload)


@login_required
@require_POST
def api_submit_answer(request):
    import sys
    print("=" * 80, file=sys.stderr)
    print("=== API_SUBMIT_ANSWER CALLED ===", file=sys.stderr)
    print(f"Request method: {request.method}", file=sys.stderr)
    print(f"Request body: {request.body}", file=sys.stderr)
    print("=" * 80, file=sys.stderr)

    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        correct = data.get('correct')  # bool - actual answer correctness
        response_time = data.get('response_time', 0)  # Time in seconds
        question_type = data.get('question_type', 'multiple_choice')
        grade = data.get('grade')  # int - spaced repetition grade (0-3)

        print(f"Parsed data: card_id={card_id}, correct={correct}, question_type={question_type}, grade={grade}", file=sys.stderr)

        try:
            card = Flashcard.objects.get(id=card_id, user=request.user)
        except Flashcard.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Card not found'}, status=404)

        # Get current study session
        current_session_id = request.session.get('current_study_session_id')
        if current_session_id:
            try:
                session = StudySession.objects.get(id=current_session_id, user=request.user)

                # Check for recent duplicate submissions (within last 5 seconds)
                from django.utils import timezone
                recent_cutoff = timezone.now() - timedelta(seconds=5)
                recent_answer = StudySessionAnswer.objects.filter(
                    session=session,
                    flashcard=card,
                    answered_at__gte=recent_cutoff
                ).first()

                if recent_answer:
                    print(f"DUPLICATE SUBMISSION DETECTED: Card {card.id} already answered recently", file=sys.stderr)
                    # Return success but don't record duplicate
                    return JsonResponse({'success': True, 'duplicate_prevented': True})

                # Record the answer in the session
                record_answer(session, card, correct, response_time, question_type)
            except StudySession.DoesNotExist:
                pass  # Session doesn't exist, continue without recording
            except Exception as e:
                # Log the error but continue with SM-2 update
                print(f"Error recording answer in session: {e}")

        # Handle incorrect word tracking
        # Map question_type to our model's format
        question_type_map = {
            'multiple_choice': 'mc',
            'input': 'type',
            'type': 'type',  # Handle both 'input' and 'type'
            'dictation': 'dictation'
        }
        mapped_question_type = question_type_map.get(question_type, question_type)
        print(f"QUESTION TYPE MAPPING: {question_type} -> {mapped_question_type}", file=sys.stderr)

        print("=" * 80, file=sys.stderr)
        print("=== INCORRECT WORD TRACKING DEBUG ===", file=sys.stderr)
        print(f"Answer tracking: card={card.word}, correct={correct}, question_type={question_type}, mapped={mapped_question_type}", file=sys.stderr)
        print(f"User authenticated: {request.user.is_authenticated}", file=sys.stderr)
        print(f"User ID: {request.user.id if request.user.is_authenticated else 'None'}", file=sys.stderr)
        print(f"User email: {getattr(request.user, 'email', 'No email')}", file=sys.stderr)
        print(f"User email: {getattr(request.user, 'email', 'No email')}", file=sys.stderr)
        print(f"Card ID: {card.id}, Card User ID: {card.user.id}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)

        if not correct:
            # Add to incorrect words list
            print(f"INCORRECT ANSWER DETECTED - Adding to tracking", file=sys.stderr)
            try:
                incorrect_review, created = IncorrectWordReview.objects.get_or_create(
                    user=request.user,
                    flashcard=card,
                    question_type=mapped_question_type,
                    defaults={'error_count': 1}
                )
                if not created:
                    incorrect_review.add_error()
                print(f"SUCCESS: Added incorrect word: {card.word} ({mapped_question_type}) - created: {created}, error_count: {incorrect_review.error_count}", file=sys.stderr)

                # Verify the record was saved
                verify_record = IncorrectWordReview.objects.filter(
                    user=request.user,
                    flashcard=card,
                    question_type=mapped_question_type,
                    is_resolved=False
                ).first()
                print(f"VERIFICATION: Record exists in DB: {verify_record is not None}", file=sys.stderr)
                if verify_record:
                    print(f"VERIFICATION: Record details - ID: {verify_record.id}, error_count: {verify_record.error_count}, is_resolved: {verify_record.is_resolved}", file=sys.stderr)

            except Exception as e:
                print(f"ERROR tracking incorrect word: {e}", file=sys.stderr)
                import traceback
                print(f"TRACEBACK: {traceback.format_exc()}", file=sys.stderr)
        else:
            print(f"CORRECT ANSWER - checking if word was previously incorrect", file=sys.stderr)
            # Mark as resolved if it was in the incorrect list
            try:
                incorrect_review = IncorrectWordReview.objects.get(
                    user=request.user,
                    flashcard=card,
                    question_type=mapped_question_type,
                    is_resolved=False
                )
                incorrect_review.mark_resolved()
                print(f"Resolved incorrect word: {card.word} ({mapped_question_type})", file=sys.stderr)
            except IncorrectWordReview.DoesNotExist:
                pass  # Word wasn't in incorrect list, which is fine
            except Exception as e:
                print(f"Error resolving incorrect word: {e}", file=sys.stderr)

        # Update difficulty-based system (replaces SM-2)
        try:
            # Use grade for difficulty if available, otherwise use correct parameter
            _update_card_difficulty(card, correct, grade)
        except Exception as e:
            print(f"Error in difficulty update: {e}")
            # Continue anyway - the incorrect word tracking is more important

        return JsonResponse({'success': True})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        # Log the error for debugging
        print(f"Error in api_submit_answer: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)


@login_required
@require_POST
def api_end_study_session(request):
    """End the current study session."""
    current_session_id = request.session.get('current_study_session_id')
    if current_session_id:
        try:
            session = StudySession.objects.get(id=current_session_id, user=request.user)
            end_study_session(session)

            # Clear session data
            del request.session['current_study_session_id']
            if 'session_start_time' in request.session:
                del request.session['session_start_time']

            return JsonResponse({
                'success': True,
                'session_summary': {
                    'total_questions': session.total_questions,
                    'correct_answers': session.correct_answers,
                    'incorrect_answers': session.incorrect_answers,
                    'accuracy_percentage': session.accuracy_percentage,
                    'duration_formatted': session.duration_formatted,
                    'words_studied': session.words_studied,
                }
            })
        except StudySession.DoesNotExist:
            pass

    return JsonResponse({'success': False, 'error': 'No active session found'})


@login_required
@require_GET
def api_statistics_data(request):
    """API endpoint to get statistics data for charts."""
    from .statistics_utils import get_user_statistics_summary
    from .models import DailyStatistics
    import json as _json

    period = request.GET.get('period', '30')
    try:
        period_days = int(period)
    except ValueError:
        period_days = 30

    # Get comprehensive statistics summary
    stats_summary = get_user_statistics_summary(request.user, period_days)

    # Get daily statistics for charts
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=period_days-1)

    daily_stats = DailyStatistics.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('date')

    # Prepare chart data
    chart_data = {
        'dates': [],
        'study_times': [],
        'questions_answered': [],
        'accuracy_rates': [],
    }

    # Fill in missing dates with zeros
    current_date = start_date
    daily_stats_dict = {stat.date: stat for stat in daily_stats}

    while current_date <= end_date:
        chart_data['dates'].append(current_date.strftime('%m/%d'))

        if current_date in daily_stats_dict:
            stat = daily_stats_dict[current_date]
            chart_data['study_times'].append(round(stat.total_study_time_seconds / 60, 1))
            chart_data['questions_answered'].append(stat.total_questions_answered)
            chart_data['accuracy_rates'].append(stat.accuracy_percentage)
        else:
            chart_data['study_times'].append(0)
            chart_data['questions_answered'].append(0)
            chart_data['accuracy_rates'].append(0)

        current_date += timedelta(days=1)

    return JsonResponse({
        'success': True,
        'stats_summary': stats_summary,
        'chart_data': chart_data,
    })


@login_required
@require_GET
def api_word_performance(request):
    """API endpoint to get individual word performance data."""
    # Get words with their performance metrics
    words = Flashcard.objects.filter(user=request.user).values(
        'word', 'total_reviews', 'correct_reviews', 'difficulty_score',
        'accuracy_percentage', 'last_reviewed'
    ).order_by('-total_reviews')[:50]  # Top 50 most reviewed words

    word_data = []
    for word in words:
        word_data.append({
            'word': word['word'],
            'total_reviews': word['total_reviews'],
            'correct_reviews': word['correct_reviews'],
            'accuracy_percentage': word['accuracy_percentage'],
            'difficulty_level': 'Easy' if word['difficulty_score'] <= 0.3 else
                              'Medium' if word['difficulty_score'] <= 0.6 else 'Hard',
            'last_reviewed': word['last_reviewed'].strftime('%Y-%m-%d') if word['last_reviewed'] else None,
        })

    return JsonResponse({
        'success': True,
        'words': word_data,
    })


@login_required
def test_statistics_view(request):
    """Test view to verify statistics template renders correctly."""
    from .statistics_utils import get_user_statistics_summary
    from .models import DailyStatistics, WeeklyStatistics, StudySession
    import json as _json

    # Get basic statistics
    stats_summary = get_user_statistics_summary(request.user, 30)

    # Create minimal context for testing
    context = {
        'period_days': 30,
        'stats_summary': stats_summary,
        'recent_sessions': [],

        # Empty chart data for testing
        'chart_dates': _json.dumps([]),
        'study_times': _json.dumps([]),
        'questions_answered': _json.dumps([]),
        'accuracy_rates': _json.dumps([]),
        'weekly_labels': _json.dumps([]),
        'weekly_consistency': _json.dumps([]),

        # Empty deck data
        'deck_labels': _json.dumps([]),
        'deck_counts': _json.dumps([]),

        # Period options
        'period_options': [
            {'value': '7', 'label': 'Last 7 days'},
            {'value': '30', 'label': 'Last 30 days'},
            {'value': '90', 'label': 'Last 3 months'},
            {'value': '365', 'label': 'Last year'},
        ],
        'current_period': '30',
    }
    return render(request, 'vocabulary/enhanced_statistics.html', context)

# Create your views here.

@login_required
def dashboard(request):
    # Thống kê cơ bản cho user hiện tại
    user_flashcards = Flashcard.objects.filter(user=request.user)
    total_cards = user_flashcards.count()
    recent_cards = user_flashcards.filter(
        created_at__gte=datetime.now() - timedelta(days=7)
    ).count()
    
    # Tính progress percentage (dựa trên target 50 cards/tuần)
    weekly_target = 50
    progress_percentage = min((recent_cards / weekly_target) * 100, 100) if weekly_target > 0 else 0
    
    # Flashcard gần đây của user
    latest_cards = user_flashcards.select_related().prefetch_related('definitions').order_by('-created_at')[:6]
    
    # Thống kê theo ngày (7 ngày gần đây) cho user hiện tại
    daily_stats = []
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        count = user_flashcards.filter(
            created_at__date=date.date()
        ).count()
        daily_stats.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    daily_stats.reverse()
    
    context = {
        'total_cards': total_cards,
        'recent_cards': recent_cards,
        'latest_cards': latest_cards,
        'daily_stats': daily_stats,
        'progress_percentage': progress_percentage,
    }
    return render(request, 'vocabulary/dashboard.html', context)

@login_required
def add_flashcard_view(request):
    decks = Deck.objects.filter(user=request.user)
    context = {
        'decks': decks
    }
    return render(request, 'vocabulary/add_flashcard.html', context)

@login_required
@require_POST
def create_deck_api(request):
    try:
        data = json.loads(request.body)
        deck_name = data.get('name', '').strip()

        if not deck_name:
            return JsonResponse({'success': False, 'error': 'Tên bộ thẻ không được để trống.'}, status=400)

        if Deck.objects.filter(user=request.user, name__iexact=deck_name).exists():
            return JsonResponse({'success': False, 'error': 'Bạn đã có một bộ thẻ với tên này.'}, status=409)

        deck = Deck.objects.create(user=request.user, name=deck_name)
        return JsonResponse({'success': True, 'deck': {'id': deck.id, 'name': deck.name}})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dữ liệu JSON không hợp lệ.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def suggest_words(request):
    query = request.GET.get('q', '')

    if settings.ENABLE_DEBUG:
        print(f"[DEBUG] suggest_words called with query: {query}")

    suggestions = get_word_suggestions_from_datamuse(query)

    if settings.ENABLE_DEBUG:
        print(f"[DEBUG] Returning suggestions: {suggestions}")

    return JsonResponse(suggestions, safe=False)

@login_required
def check_word_spelling(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Yêu cầu phải là POST.'}, status=405)

    word = request.POST.get('word', '').strip()

    if not word:
        return JsonResponse({'error': 'Tham số "word" bị thiếu hoặc rỗng.'}, status=400)

    if settings.ENABLE_DEBUG:
        print(f"[DEBUG] check_word_spelling called with word: {word}")

    is_correct = check_word_spelling_with_languagetool(word)

    if settings.ENABLE_DEBUG:
        print(f"[DEBUG] Is word '{word}' correct? {is_correct}")

    return JsonResponse({'is_correct': is_correct})

@login_required
def get_word_details_api(request):
    word = request.GET.get('word', '').strip()

    if settings.ENABLE_DEBUG:
        print(f"[DEBUG] get_word_details_api called for word: {word}")

    if not word:
        return JsonResponse({'error': 'No word provided'}, status=400)

    details = get_word_details(word)

    if settings.ENABLE_DEBUG:
        print(f"[DEBUG] Word details from service: {details}")

    if "error" in details:
        return JsonResponse(details, status=404 if "Không tìm thấy từ" in details["error"] else 500)
    
    return JsonResponse(details, safe=False)

@login_required
@csrf_exempt
@require_POST
def save_flashcards(request):
    try:
        deck_id = request.POST.get('deck_id')
        deck = None
        if deck_id:
            try:
                deck = Deck.objects.get(id=deck_id, user=request.user)
            except Deck.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Bộ thẻ không hợp lệ.'}, status=404)
        else:
            return JsonResponse({'success': False, 'error': 'Vui lòng chọn một bộ thẻ.'}, status=400)
            
        saved_words = []
        data = {}

        # Group data by index from request.POST and request.FILES
        for key, value in request.POST.items():
            if key.startswith('flashcards-'):
                parts = key.split('-')
                idx = int(parts[1])
                field = parts[2]
                if idx not in data:
                    data[idx] = {}
                data[idx][field] = value

        for key, value in request.FILES.items():
            if key.startswith('flashcards-'):
                parts = key.split('-')
                idx = int(parts[1])
                field = parts[2]
                if idx not in data:
                    data[idx] = {}
                data[idx][field] = value

        # Process each flashcard group
        for idx in sorted(data.keys()):
            card_data = data[idx]
            word = card_data.get('word')
            if not word:
                continue

            # Use update_or_create to avoid IntegrityError for existing words
            # and allow users to update existing flashcards.
            defaults = {
                'phonetic': card_data.get('phonetic'),
                'part_of_speech': card_data.get('part_of_speech'),
                'audio_url': card_data.get('audio_url'),
                'deck': deck
            }
            
            # Only update image if a new one is provided
            if 'image' in card_data:
                defaults['image'] = card_data.get('image')

            flashcard, created = Flashcard.objects.update_or_create(
                user=request.user,
                word=word,
                defaults=defaults
            )

            # Clear old definitions and create new one(s)
            flashcard.definitions.all().delete()
            Definition.objects.create(
                flashcard=flashcard,
                english_definition=card_data.get('english_definition'),
                vietnamese_definition=card_data.get('vietnamese_definition', '')
            )
            saved_words.append(word)

        if not saved_words:
            return JsonResponse({'success': False, 'error': 'No valid flashcard data received.'})

        return JsonResponse({'success': True, 'saved': saved_words})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def deck_list(request):
    decks = Deck.objects.filter(user=request.user).annotate(
        card_count=Count('flashcards')
    ).order_by('-created_at')
    
    context = {
        'decks': decks
    }
    return render(request, 'vocabulary/deck_list.html', context)


@login_required
def deck_detail(request, deck_id):
    try:
        deck = Deck.objects.get(id=deck_id, user=request.user)
        flashcards = Flashcard.objects.filter(deck=deck).prefetch_related('definitions')

        # Get navigation information for deck-to-deck navigation
        user_decks = Deck.objects.filter(user=request.user).order_by('id')

        # Find previous and next decks
        previous_deck = user_decks.filter(id__lt=deck_id).order_by('-id').first()
        next_deck = user_decks.filter(id__gt=deck_id).order_by('id').first()

        # Get deck position information
        deck_position = user_decks.filter(id__lte=deck_id).count()
        total_decks = user_decks.count()

        context = {
            'deck': deck,
            'flashcards': flashcards,
            'previous_deck': previous_deck,
            'next_deck': next_deck,
            'deck_position': deck_position,
            'total_decks': total_decks,
            'has_navigation': total_decks > 1,  # Show navigation only if user has multiple decks
        }
        return render(request, 'vocabulary/deck_detail.html', context)
    except Deck.DoesNotExist:
        return redirect('deck_list')


@login_required
def flashcard_list(request):
    flashcards = Flashcard.objects.filter(user=request.user).order_by('-created_at')
    flashcard_defs = []
    for card in flashcards:
        definitions = card.definitions.all()
        flashcard_defs.append((card, definitions))
    return render(request, 'vocabulary/flashcard_list.html', {'flashcard_defs': flashcard_defs})

@login_required
@require_GET
def check_word_exists(request):
    word = request.GET.get('word', '').strip()
    exists = Flashcard.objects.filter(user=request.user, word__iexact=word).exists()
    return JsonResponse({'exists': exists})

@login_required
@require_GET
def api_search_word_in_decks(request):
    """
    Search for a specific word across all user's decks.
    Returns which decks contain the word and deck information.
    """
    search_word = request.GET.get('word', '').strip()

    if not search_word:
        return JsonResponse({
            'success': False,
            'error': 'Search word is required'
        }, status=400)

    try:
        # Search for the word in user's flashcards (case-insensitive)
        matching_cards = Flashcard.objects.filter(
            user=request.user,
            word__icontains=search_word
        ).select_related('deck').order_by('word')

        if not matching_cards.exists():
            return JsonResponse({
                'success': True,
                'found': False,
                'message': f'Word "{search_word}" not found in any of your decks.',
                'results': []
            })

        # Group results by deck
        deck_results = {}
        for card in matching_cards:
            deck_id = card.deck.id
            deck_name = card.deck.name

            if deck_id not in deck_results:
                deck_results[deck_id] = {
                    'deck_id': deck_id,
                    'deck_name': deck_name,
                    'words': []
                }

            # Get first definition for preview
            first_definition = card.definitions.first()
            definition_preview = ""
            if first_definition:
                if first_definition.english_definition:
                    definition_preview = first_definition.english_definition[:100]
                elif first_definition.vietnamese_definition:
                    definition_preview = first_definition.vietnamese_definition[:100]

            deck_results[deck_id]['words'].append({
                'id': card.id,
                'word': card.word,
                'phonetic': card.phonetic or '',
                'part_of_speech': card.part_of_speech or '',
                'definition_preview': definition_preview,
                'exact_match': card.word.lower() == search_word.lower()
            })

        # Convert to list and sort by exact matches first
        results = list(deck_results.values())
        for deck_result in results:
            deck_result['words'].sort(key=lambda x: (not x['exact_match'], x['word'].lower()))

        return JsonResponse({
            'success': True,
            'found': True,
            'search_word': search_word,
            'total_matches': matching_cards.count(),
            'deck_count': len(results),
            'results': results
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }, status=500)

@login_required
@require_GET
def api_get_word_suggestions(request):
    """
    Get autocomplete suggestions for word search.
    Returns a list of words that match the partial input.
    """
    partial_word = request.GET.get('partial', '').strip()

    if not partial_word or len(partial_word) < 2:
        return JsonResponse({
            'success': True,
            'suggestions': []
        })

    try:
        # Get words that start with or contain the partial word
        # Prioritize words that start with the partial word
        start_matches = Flashcard.objects.filter(
            user=request.user,
            word__istartswith=partial_word
        ).select_related('deck').order_by('word')[:5]

        contain_matches = Flashcard.objects.filter(
            user=request.user,
            word__icontains=partial_word
        ).exclude(
            word__istartswith=partial_word
        ).select_related('deck').order_by('word')[:5]

        # Combine results, prioritizing start matches
        all_matches = list(start_matches) + list(contain_matches)

        suggestions = []
        seen_words = set()

        for card in all_matches[:8]:  # Limit to 8 suggestions
            if card.word.lower() not in seen_words:
                seen_words.add(card.word.lower())

                # Get first definition for preview
                first_definition = card.definitions.first()
                definition_preview = ""
                if first_definition and first_definition.english_definition:
                    definition_preview = first_definition.english_definition[:50]

                suggestions.append({
                    'word': card.word,
                    'phonetic': card.phonetic or '',
                    'part_of_speech': card.part_of_speech or '',
                    'definition_preview': definition_preview,
                    'deck_name': card.deck.name,
                    'starts_with': card.word.lower().startswith(partial_word.lower())
                })

        return JsonResponse({
            'success': True,
            'suggestions': suggestions
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to get suggestions: {str(e)}'
        }, status=500)

@login_required
@require_POST
def delete_flashcard(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
            card_id = data.get('id')
        else:
            card_id = request.POST.get('id')
        
        if not card_id:
            return JsonResponse({'success': False, 'error': 'ID không được cung cấp'})
        
        try:
            # Lấy instance để gọi method delete() tùy chỉnh (xóa file hình ảnh) - chỉ cho user hiện tại
            flashcard = Flashcard.objects.get(id=card_id, user=request.user)
            flashcard.delete()  # Gọi method delete() tùy chỉnh
            return JsonResponse({'success': True})
        except Flashcard.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Không tìm thấy flashcard để xóa'})
            
    except json.JSONDecodeError as e:
        return JsonResponse({'success': False, 'error': f'Lỗi parse JSON: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Lỗi server: {str(e)}'})

@login_required
@require_GET
def translate_to_vietnamese(request):
    text_to_translate = request.GET.get('text', '')
    if not text_to_translate:
        return JsonResponse({'error': 'No text provided'}, status=400)
    try:
        # Sử dụng deep-translator
        translated_text = GoogleTranslator(source='auto', target='vi').translate(text_to_translate)
        return JsonResponse({'translated_text': translated_text})
    except Exception as e:
        # Ghi lại lỗi để debug
        print(f"Lỗi dịch thuật với deep-translator: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def translate_word_to_vietnamese(request):
    """API to translate English word to Vietnamese meaning"""
    word = request.GET.get('word', '').strip()
    
    if not word:
        return JsonResponse({'error': 'No word provided'}, status=400)
    
    try:
        translator = Translator()
        # For single words, we want to get the meaning rather than direct translation
        # First try to get a more contextual translation
        result = translator.translate(f"The meaning of {word}", src='en', dest='vi')
        meaning_translation = result.text
        
        # Also get direct word translation
        direct_result = translator.translate(word, src='en', dest='vi')
        direct_translation = direct_result.text
        
        # Clean up the meaning translation (remove "The meaning of" part)
        if 'ý nghĩa của' in meaning_translation.lower():
            meaning_translation = meaning_translation.split('là')[-1].strip() if 'là' in meaning_translation else meaning_translation
            meaning_translation = meaning_translation.replace('ý nghĩa của', '').strip()
        
        return JsonResponse({
            'word': word,
            'direct_translation': direct_translation,
            'meaning_translation': meaning_translation,
            'recommended': direct_translation  # Use direct translation as default
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Translation failed: {str(e)}'}, status=500)

@login_required
@require_GET  
def get_related_image(request):
    """API to get related image URL for a word"""
    word = request.GET.get('word', '').strip()
    
    if not word:
        return JsonResponse({'error': 'No word provided'}, status=400)
    
    try:
        # Use Unsplash API for high-quality images
        # Note: You need to get a free API key from https://unsplash.com/developers
        UNSPLASH_ACCESS_KEY = getattr(settings, 'UNSPLASH_ACCESS_KEY', None)
        
        if not UNSPLASH_ACCESS_KEY:
            # Fallback to a simple image search API or placeholder
            return JsonResponse({
                'word': word,
                'image_url': f'https://source.unsplash.com/400x300/?{word}',
                'source': 'unsplash_public'
            })
        
        # Use official Unsplash API
        url = f'https://api.unsplash.com/search/photos'
        params = {
            'query': word,
            'per_page': 1,
            'orientation': 'landscape'
        }
        headers = {
            'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                image_data = data['results'][0]
                return JsonResponse({
                    'word': word,
                    'image_url': image_data['urls']['regular'],
                    'thumbnail_url': image_data['urls']['small'],
                    'description': image_data.get('alt_description', ''),
                    'source': 'unsplash_api'
                })
        
        # Fallback to public Unsplash source
        return JsonResponse({
            'word': word,
            'image_url': f'https://source.unsplash.com/400x300/?{word}',
            'source': 'unsplash_public'
        })
        
    except Exception as e:
        # Fallback in case of any error
        return JsonResponse({
            'word': word,
            'image_url': f'https://source.unsplash.com/400x300/?{word}',
            'source': 'fallback',
            'error': str(e)
        })

## Removed debug_language and language_test since i18n is disabled

@require_POST
def api_set_language(request):
    """Set UI language in session for manual_texts system (en/vi)."""
    try:
        data = json.loads(request.body) if request.body else {}
        lang = (data.get('language') or '').strip().lower()
        if lang not in ('en', 'vi'):
            return JsonResponse({'success': False, 'error': 'Invalid language'}, status=400)

        # Persist choice in session so context processor uses it
        request.session['django_language'] = lang
        request.session.save()
        return JsonResponse({'success': True, 'language': lang})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def statistics_view(request):
    from .statistics_utils import get_user_statistics_summary
    from .models import DailyStatistics, WeeklyStatistics
    import json as _json
    from django.db.models import Sum, Avg

    # Get time period from request (default to 30 days)
    period = request.GET.get('period', '30')
    try:
        period_days = int(period)
    except ValueError:
        period_days = 30

    # Get comprehensive statistics summary
    stats_summary = get_user_statistics_summary(request.user, period_days)

    # Get daily statistics for charts
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=period_days-1)

    daily_stats = DailyStatistics.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).order_by('date')

    # Prepare chart data
    chart_dates = []
    study_times = []
    questions_answered = []
    accuracy_rates = []

    # Fill in missing dates with zeros
    current_date = start_date
    daily_stats_dict = {stat.date: stat for stat in daily_stats}

    while current_date <= end_date:
        chart_dates.append(current_date.strftime('%m/%d'))

        if current_date in daily_stats_dict:
            stat = daily_stats_dict[current_date]
            study_times.append(round(stat.total_study_time_seconds / 60, 1))  # Convert to minutes
            questions_answered.append(stat.total_questions_answered)
            accuracy_rates.append(stat.accuracy_percentage)
        else:
            study_times.append(0)
            questions_answered.append(0)
            accuracy_rates.append(0)

        current_date += timedelta(days=1)

    # Get deck statistics
    user_decks = Deck.objects.filter(user=request.user)
    deck_data = user_decks.annotate(card_count=Count('flashcards')).order_by('-card_count')
    deck_labels = [deck.name for deck in deck_data]
    deck_counts = [deck.card_count for deck in deck_data]

    # Get recent study sessions
    recent_sessions = StudySession.objects.filter(
        user=request.user,
        session_end__isnull=False
    ).order_by('-session_start')[:10]

    # Get weekly statistics for consistency tracking
    weekly_stats = WeeklyStatistics.objects.filter(
        user=request.user
    ).order_by('-year', '-week_number')[:12]  # Last 12 weeks

    weekly_consistency = []
    weekly_labels = []
    for week_stat in reversed(weekly_stats):
        weekly_labels.append(f"W{week_stat.week_number}")
        weekly_consistency.append(week_stat.consistency_percentage)

    context = {
        'period_days': period_days,
        'stats_summary': stats_summary,
        'recent_sessions': recent_sessions,

        # Chart data (JSON)
        'chart_dates': _json.dumps(chart_dates),
        'study_times': _json.dumps(study_times),
        'questions_answered': _json.dumps(questions_answered),
        'accuracy_rates': _json.dumps(accuracy_rates),
        'weekly_labels': _json.dumps(weekly_labels),
        'weekly_consistency': _json.dumps(weekly_consistency),

        # Deck data
        'deck_labels': _json.dumps(deck_labels),
        'deck_counts': _json.dumps(deck_counts),

        # Period options
        'period_options': [
            {'value': '7', 'label': 'Last 7 days'},
            {'value': '30', 'label': 'Last 30 days'},
            {'value': '90', 'label': 'Last 3 months'},
            {'value': '365', 'label': 'Last year'},
        ],
        'current_period': period,
    }
    return render(request, 'vocabulary/enhanced_statistics.html', context)

@login_required
def study_page(request):
    decks = Deck.objects.filter(user=request.user)
    total_words_available = Flashcard.objects.filter(user=request.user).count()

    # End any incomplete sessions for this user
    incomplete_sessions = StudySession.objects.filter(
        user=request.user,
        session_end__isnull=True
    )
    for session in incomplete_sessions:
        end_study_session(session)

    return render(request, 'vocabulary/study.html', {
        'decks': decks,
        'total_words_available': total_words_available
    })

@login_required
@require_GET
def api_next_card(request):
    deck_ids = request.GET.getlist('deck_ids[]')

    # Use enhanced card selection algorithm
    card = _get_next_card_enhanced(request.user, deck_ids)
    if not card:
        return JsonResponse({'done': True})

    # Update tracking when card is shown
    _update_card_shown_tracking(card)
    defs = list(card.definitions.values('english_definition', 'vietnamese_definition'))
    return JsonResponse({
        'done': False,
        'card': {
            'id': card.id,
            'word': card.word,
            'phonetic': card.phonetic,
            'part_of_speech': card.part_of_speech,
            'audio_url': card.audio_url,
            'image_url': card.image.url if card.image else card.related_image_url,
            'definitions': defs,
        }
    })

@login_required
@require_POST
def api_submit_review(request):
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        grade = int(data.get('grade'))  # 0-3 mapping Again,Hard,Good,Easy
        card = Flashcard.objects.get(id=card_id, user=request.user)
    except Exception:
        return JsonResponse({'success': False}, status=400)

    # Use difficulty-based update with grade
    correct = grade >= 2  # Good or Easy considered correct
    try:
        _update_card_difficulty(card, correct, grade)
    except Exception as e:
        print(f"Error in difficulty update (grade): {e}")
        # Continue anyway - return success to avoid breaking the UI

    return JsonResponse({'success': True})

@login_required
@require_POST
def api_update_flashcard(request):
    """API endpoint to update a flashcard."""
    try:
        # Validate request body
        if not request.body:
            return JsonResponse({'success': False, 'error': 'No data provided'}, status=400)

        data = json.loads(request.body)
        card_id = data.get('card_id')

        # Validate card_id
        if not card_id:
            return JsonResponse({'success': False, 'error': 'Card ID is required'}, status=400)

        # Get the flashcard and verify ownership
        try:
            card = Flashcard.objects.get(id=card_id, user=request.user)
        except Flashcard.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Flashcard not found'}, status=404)

        # Update basic fields
        card.word = data.get('word', card.word).strip()
        card.phonetic = data.get('phonetic', card.phonetic or '').strip()
        card.part_of_speech = data.get('part_of_speech', card.part_of_speech or '').strip()
        card.audio_url = data.get('audio_url', card.audio_url or '').strip()
        card.related_image_url = data.get('related_image_url', card.related_image_url or '').strip()
        card.general_synonyms = data.get('general_synonyms', card.general_synonyms or '').strip()
        card.general_antonyms = data.get('general_antonyms', card.general_antonyms or '').strip()

        # Validate required fields
        if not card.word:
            return JsonResponse({'success': False, 'error': 'Word is required'}, status=400)

        # Check for duplicate words (excluding current card)
        if Flashcard.objects.filter(user=request.user, word__iexact=card.word).exclude(id=card.id).exists():
            return JsonResponse({'success': False, 'error': 'A card with this word already exists'}, status=400)

        # Save the card (don't reset spaced repetition data)
        card.save()

        # Update definitions
        definitions_data = data.get('definitions', [])
        if definitions_data:
            # Clear existing definitions
            card.definitions.all().delete()

            # Create new definitions
            for def_data in definitions_data:
                english_def = def_data.get('english_definition', '').strip()
                vietnamese_def = def_data.get('vietnamese_definition', '').strip()

                if english_def and vietnamese_def:
                    Definition.objects.create(
                        flashcard=card,
                        english_definition=english_def,
                        vietnamese_definition=vietnamese_def,
                        definition_synonyms=def_data.get('definition_synonyms', '').strip(),
                        definition_antonyms=def_data.get('definition_antonyms', '').strip()
                    )

        # Return updated card data
        definitions = list(card.definitions.values(
            'english_definition', 'vietnamese_definition',
            'definition_synonyms', 'definition_antonyms'
        ))

        return JsonResponse({
            'success': True,
            'card': {
                'id': card.id,
                'word': card.word,
                'phonetic': card.phonetic,
                'part_of_speech': card.part_of_speech,
                'audio_url': card.audio_url,
                'related_image_url': card.related_image_url,
                'general_synonyms': card.general_synonyms,
                'general_antonyms': card.general_antonyms,
                'definitions': definitions,
                'image_url': card.image.url if card.image else card.related_image_url,
            }
        })

    except json.JSONDecodeError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"JSON decode error in api_update_flashcard: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in api_update_flashcard: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def api_test_update_flashcard(request):
    """Test endpoint to debug flashcard update issues."""
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'message': 'Test endpoint is working',
            'method': request.method,
            'user': str(request.user),
            'csrf_token_present': bool(request.META.get('HTTP_X_CSRFTOKEN'))
        })
    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else {}
            return JsonResponse({
                'success': True,
                'message': 'POST request received successfully',
                'data_received': data,
                'csrf_token_present': bool(request.META.get('HTTP_X_CSRFTOKEN'))
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'method': request.method
            })
    else:
        return JsonResponse({'success': False, 'error': f'Method {request.method} not allowed'}, status=405)

@login_required
@require_POST
def api_update_deck_name(request):
    """API endpoint to update a deck name."""
    try:
        data = json.loads(request.body)
        deck_id = data.get('deck_id')
        new_name = data.get('name', '').strip()

        # Validate input
        if not new_name:
            return JsonResponse({'success': False, 'error': 'Deck name is required'}, status=400)

        # Get the deck and verify ownership
        try:
            deck = Deck.objects.get(id=deck_id, user=request.user)
        except Deck.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Deck not found'}, status=404)

        # Check for duplicate names (excluding current deck)
        if Deck.objects.filter(user=request.user, name__iexact=new_name).exclude(id=deck.id).exists():
            return JsonResponse({'success': False, 'error': 'A deck with this name already exists'}, status=400)

        # Update the deck name
        deck.name = new_name
        deck.save()

        return JsonResponse({
            'success': True,
            'deck': {
                'id': deck.id,
                'name': deck.name,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def api_fetch_missing_audio(request):
    """API endpoint to fetch missing audio for flashcards in a deck."""
    try:
        data = json.loads(request.body)
        deck_id = data.get('deck_id')

        # Get the deck and verify ownership
        try:
            deck = Deck.objects.get(id=deck_id, user=request.user)
        except Deck.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Deck not found'}, status=404)

        # Get flashcards without audio
        from django.db import models
        cards_without_audio = deck.flashcards.filter(
            models.Q(audio_url__isnull=True) | models.Q(audio_url='')
        )

        if not cards_without_audio.exists():
            return JsonResponse({
                'success': True,
                'message': 'No cards need audio fetching',
                'updated_count': 0
            })

        # Import audio service
        from .audio_service import fetch_audio_for_word
        import logging
        logger = logging.getLogger(__name__)

        updated_count = 0
        words_processed = []

        for card in cards_without_audio:
            try:
                audio_url = fetch_audio_for_word(card.word)
                if audio_url:
                    card.audio_url = audio_url
                    card.save(update_fields=['audio_url'])
                    updated_count += 1
                    words_processed.append({'word': card.word, 'found': True, 'url': audio_url})
                else:
                    words_processed.append({'word': card.word, 'found': False, 'url': None})
            except Exception as e:
                logger.error(f"Error fetching audio for word '{card.word}': {e}")
                words_processed.append({'word': card.word, 'found': False, 'error': str(e)})

        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'total_processed': len(words_processed),
            'words_processed': words_processed
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def api_fetch_audio_for_card(request):
    """API endpoint to fetch audio for a specific flashcard."""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')

        # Get the flashcard and verify ownership
        try:
            card = Flashcard.objects.get(id=card_id, user=request.user)
        except Flashcard.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Flashcard not found'}, status=404)

        # Import audio service
        from .audio_service import fetch_audio_for_word
        import logging
        logger = logging.getLogger(__name__)

        try:
            audio_url = fetch_audio_for_word(card.word)
            if audio_url:
                card.audio_url = audio_url
                card.save(update_fields=['audio_url'])

                return JsonResponse({
                    'success': True,
                    'audio_url': audio_url,
                    'word': card.word
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No audio found for this word',
                    'word': card.word
                })
        except Exception as e:
            logger.error(f"Error fetching audio for word '{card.word}': {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error fetching audio: {str(e)}',
                'word': card.word
            })

    except Exception as e:
        logger.error(f"Unexpected error in api_fetch_audio_for_card: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


@login_required
@require_POST
def api_fetch_enhanced_audio(request):
    """API endpoint to fetch multiple audio options for a flashcard."""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        word = data.get('word')

        # Validate required parameters
        if not card_id:
            return JsonResponse({'success': False, 'error': 'Card ID is required'}, status=400)

        if not word:
            return JsonResponse({'success': False, 'error': 'Word is required'}, status=400)

        # Get the flashcard and verify ownership
        try:
            card = Flashcard.objects.get(id=card_id, user=request.user)
        except Flashcard.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Flashcard not found'}, status=404)

        # Import enhanced audio service
        from .audio_service import fetch_multiple_audio_options
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Fetch multiple audio options
            audio_options = fetch_multiple_audio_options(word)

            # Format response data
            options_data = []
            for option in audio_options:
                options_data.append({
                    'url': option.url,
                    'label': option.label,
                    'selector_source': option.selector_source,
                    'is_valid': option.is_valid,
                    'error_message': option.error_message
                })

            return JsonResponse({
                'success': True,
                'word': word,
                'current_audio': card.audio_url or '',
                'audio_options': options_data,
                'total_found': len([opt for opt in audio_options if opt.is_valid])
            })

        except Exception as e:
            logger.error(f"Error fetching enhanced audio for word '{word}': {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error fetching audio options: {str(e)}',
                'word': word
            })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in api_fetch_enhanced_audio: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


@login_required
@require_POST
def api_update_flashcard_audio(request):
    """API endpoint to update a flashcard's audio URL with selected option."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Received audio update request from user: {request.user.email}")

        data = json.loads(request.body)
        card_id = data.get('card_id')
        audio_url = data.get('audio_url')

        logger.info(f"Request data - card_id: {card_id}, audio_url: {audio_url}")

        # Validate required parameters
        if not card_id:
            logger.warning("Missing card_id in request")
            return JsonResponse({'success': False, 'error': 'Card ID is required'}, status=400)

        if not audio_url:
            logger.warning("Missing audio_url in request")
            return JsonResponse({'success': False, 'error': 'Audio URL is required'}, status=400)

        # Get the flashcard and verify ownership
        try:
            card = Flashcard.objects.get(id=card_id, user=request.user)
            logger.info(f"Found flashcard: {card.word} (ID: {card.id})")
        except Flashcard.DoesNotExist:
            logger.error(f"Flashcard not found or access denied - card_id: {card_id}, user: {request.user.email}")
            return JsonResponse({'success': False, 'error': 'Flashcard not found'}, status=404)

        # Validate audio URL format
        if not audio_url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid audio URL format: {audio_url}")
            return JsonResponse({'success': False, 'error': 'Invalid audio URL format'}, status=400)

        try:
            # Store old audio URL for logging
            old_audio_url = card.audio_url

            # Update the flashcard's audio URL
            card.audio_url = audio_url
            card.save(update_fields=['audio_url'])

            # Verify the update was successful
            card.refresh_from_db()
            if card.audio_url == audio_url:
                logger.info(f"Successfully updated audio URL for flashcard {card_id} (word: {card.word})")
                logger.info(f"  Old URL: {old_audio_url}")
                logger.info(f"  New URL: {audio_url}")
            else:
                logger.error(f"Database update failed - expected: {audio_url}, actual: {card.audio_url}")
                return JsonResponse({
                    'success': False,
                    'error': 'Database update verification failed'
                })

            return JsonResponse({
                'success': True,
                'card_id': card_id,
                'audio_url': audio_url,
                'word': card.word,
                'old_audio_url': old_audio_url
            })

        except Exception as e:
            logger.error(f"Database error updating flashcard audio for card {card_id}: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Database error: {str(e)}'
            })

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in api_update_flashcard_audio: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Incorrect Words Review API Endpoints

@login_required
@require_POST
def api_add_incorrect_word(request):
    """Add a word to the incorrect words review list."""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        question_type = data.get('question_type')

        if not card_id or not question_type:
            return JsonResponse({'success': False, 'error': 'Missing card_id or question_type'}, status=400)

        if question_type not in ['mc', 'type', 'dictation']:
            return JsonResponse({'success': False, 'error': 'Invalid question_type'}, status=400)

        try:
            card = Flashcard.objects.get(id=card_id, user=request.user)
        except Flashcard.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Card not found'}, status=404)

        # Get or create the incorrect word review record
        incorrect_review, created = IncorrectWordReview.objects.get_or_create(
            user=request.user,
            flashcard=card,
            question_type=question_type,
            defaults={'error_count': 1}
        )

        if not created:
            # If it already exists, increment the error count
            incorrect_review.add_error()

        return JsonResponse({
            'success': True,
            'created': created,
            'error_count': incorrect_review.error_count
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_resolve_incorrect_word(request):
    """Mark an incorrect word as resolved (answered correctly)."""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        question_type = data.get('question_type')

        if not card_id or not question_type:
            return JsonResponse({'success': False, 'error': 'Missing card_id or question_type'}, status=400)

        try:
            card = Flashcard.objects.get(id=card_id, user=request.user)
        except Flashcard.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Card not found'}, status=404)

        # Find and resolve the incorrect word review
        try:
            incorrect_review = IncorrectWordReview.objects.get(
                user=request.user,
                flashcard=card,
                question_type=question_type,
                is_resolved=False
            )
            incorrect_review.mark_resolved()

            return JsonResponse({
                'success': True,
                'resolved': True
            })

        except IncorrectWordReview.DoesNotExist:
            # Word wasn't in incorrect list, which is fine
            return JsonResponse({
                'success': True,
                'resolved': False,
                'message': 'Word was not in incorrect list'
            })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def api_get_incorrect_words_count(request):
    """Get count of incorrect words for the user."""
    import sys
    try:
        print("=" * 80, file=sys.stderr)
        print("=== API_GET_INCORRECT_WORDS_COUNT CALLED ===", file=sys.stderr)
        print(f"User authenticated: {request.user.is_authenticated}", file=sys.stderr)
        print(f"User ID: {request.user.id if request.user.is_authenticated else 'None'}", file=sys.stderr)
        print(f"User email: {getattr(request.user, 'email', 'No email')}", file=sys.stderr)

        # Count unresolved incorrect words grouped by question type
        counts = {
            'total': 0,
            'mc': 0,
            'type': 0,
            'dictation': 0
        }

        # Debug: Check total IncorrectWordReview records for this user
        total_records = IncorrectWordReview.objects.filter(user=request.user).count()
        unresolved_records = IncorrectWordReview.objects.filter(user=request.user, is_resolved=False).count()
        print(f"Total IncorrectWordReview records for user: {total_records}", file=sys.stderr)
        print(f"Unresolved IncorrectWordReview records for user: {unresolved_records}", file=sys.stderr)

        incorrect_words = IncorrectWordReview.objects.filter(
            user=request.user,
            is_resolved=False
        ).values('question_type').annotate(count=Count('id'))

        print(f"Query result: {list(incorrect_words)}", file=sys.stderr)

        for item in incorrect_words:
            question_type = item['question_type']
            count = item['count']
            counts[question_type] = count
            counts['total'] += count

        print(f"Final counts: {counts}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)

        return JsonResponse({
            'success': True,
            'counts': counts
        })

    except Exception as e:
        print(f"Error in api_get_incorrect_words_count: {e}", file=sys.stderr)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Favorites API Endpoints

@login_required
@require_POST
def api_toggle_favorite(request):
    """Toggle favorite status for a flashcard."""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')

        if not card_id:
            return JsonResponse({'success': False, 'error': 'Missing card_id'}, status=400)

        try:
            card = Flashcard.objects.get(id=card_id, user=request.user)
        except Flashcard.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Card not found'}, status=404)

        # Toggle favorite status
        favorite, created = FavoriteFlashcard.toggle_favorite(request.user, card)

        return JsonResponse({
            'success': True,
            'is_favorited': created,  # True if favorited, False if unfavorited
            'favorites_count': FavoriteFlashcard.get_user_favorites_count(request.user)
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def api_get_favorites_count(request):
    """Get count of user's favorite flashcards."""
    try:
        count = FavoriteFlashcard.get_user_favorites_count(request.user)
        return JsonResponse({
            'success': True,
            'count': count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def api_check_favorite_status(request):
    """Check if specific flashcards are favorited."""
    try:
        card_ids = request.GET.getlist('card_ids[]')
        if not card_ids:
            return JsonResponse({'success': False, 'error': 'No card IDs provided'}, status=400)

        # Convert to integers
        card_ids = [int(cid) for cid in card_ids if cid.isdigit()]

        # Get favorite status for each card
        favorites = FavoriteFlashcard.objects.filter(
            user=request.user,
            flashcard_id__in=card_ids
        ).values_list('flashcard_id', flat=True)

        favorite_status = {card_id: card_id in favorites for card_id in card_ids}

        return JsonResponse({
            'success': True,
            'favorites': favorite_status
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def favorites_page(request):
    """Display user's favorite flashcards."""
    favorites = FavoriteFlashcard.get_user_favorites(request.user)

    # Paginate favorites (20 per page)
    from django.core.paginator import Paginator
    paginator = Paginator(favorites, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'favorites': page_obj,
        'total_favorites': favorites.count(),
    }

    return render(request, 'vocabulary/favorites.html', context)


def debug_study_template(request):
    """Debug view to check study template rendering without authentication."""
    context = {
        'manual_texts': {
            'study': 'Study',
            'learn_english': 'Learn English',
            'normal_study_by_decks': 'Study by Decks',
            'deck_study_description': 'Study flashcards from selected decks',
            'random_study': 'Random Study',
            'random_study_description': 'Study random flashcards',
            'review_incorrect_words': 'Review Mode',
            'review_study_description': 'Review incorrect words',
            'study_favorites': 'Study Favorites',
            'favorites_study_description': 'Study your favorite vocabulary words',
            'favorite_words_count': 'favorite words',
            'select_decks': 'Select Decks',
            'start_study': 'Start Study',
            'correct': 'Correct',
            'incorrect': 'Incorrect',
            'check': 'Check',
            'answer_placeholder': 'Your answer...',
            'grade_again': 'Again',
            'grade_hard': 'Hard',
            'grade_good': 'Good',
            'grade_easy': 'Easy',
            'no_cards_due': 'No cards due',
            'play_audio': 'Play Audio',
            'listen_and_type': 'Listen and Type',
            'type_what_you_hear': 'Type what you hear',
            'correct_answer': 'Correct Answer',
            'incorrect_answer': 'Incorrect Answer',
            'replay_audio': 'Replay Audio',
            'english_label': 'English',
            'vietnamese_label': 'Vietnamese',
            'review_completed_title': 'Review Completed',
            'review_completed_message': 'Great job!',
            'continue_studying': 'Continue Studying'
        }
    }
    return render(request, 'vocabulary/study.html', context)
