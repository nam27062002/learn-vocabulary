from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import Flashcard, Definition, Deck # Import Deck model
from django.conf import settings # Import settings
from .api_services import get_word_suggestions_from_datamuse, check_word_spelling_with_languagetool # Import new service functions
from .word_details_service import get_word_details # Import the new service function
from googletrans import Translator
import requests
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Count
from datetime import datetime, timedelta
import os
import json
from django.contrib.auth.decorators import login_required
from deep_translator import GoogleTranslator
from django.db.models.functions import Random

# Enhanced Spaced Repetition Configuration
SPACED_REPETITION_CONFIG = {
    'MAX_DAILY_REVIEWS': 3,          # Maximum times a card can be shown per day
    'NEGLECT_THRESHOLD_DAYS': 14,    # Days after which a card is considered neglected
    'SIMILARITY_THRESHOLD': 0.6,     # Threshold for semantic similarity filtering
    'DIFFICULTY_ADJUSTMENT': 0.3,    # How much difficulty affects interval (0.0-1.0)
    'MIN_DISTRACTORS': 10,          # Minimum distractors to collect for filtering
}
import random

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

# Enhanced word selection algorithm
def _get_next_card_enhanced(user, deck_ids=None):
    """
    Enhanced card selection algorithm that prevents short-term repetition
    and long-term neglect while maintaining spaced repetition principles.
    """
    from django.db.models import F, Q, Case, When, FloatField
    from django.db.models.functions import Random
    from datetime import datetime, timedelta

    today = datetime.now().date()
    now = datetime.now()

    # Base queryset
    qs = Flashcard.objects.filter(user=user)
    if deck_ids:
        qs = qs.filter(deck_id__in=deck_ids)

    # Reset daily counters if needed
    qs.filter(last_seen_date__lt=today).update(times_seen_today=0)

    # Priority 1: Cards due for review that haven't been seen too much today
    due_cards = qs.filter(
        next_review__lte=today,
        times_seen_today__lt=SPACED_REPETITION_CONFIG['MAX_DAILY_REVIEWS']
    ).annotate(
        # Priority score: older due dates get higher priority
        priority_score=Case(
            When(next_review__lt=today - timedelta(days=7), then=10.0),  # Very overdue
            When(next_review__lt=today - timedelta(days=3), then=8.0),   # Overdue
            When(next_review__lt=today - timedelta(days=1), then=6.0),   # Yesterday
            When(next_review=today, then=4.0),                           # Due today
            default=2.0,
            output_field=FloatField()
        )
    ).order_by('-priority_score', 'next_review', Random())

    card = due_cards.first()
    if card:
        return card

    # Priority 2: Cards that haven't been seen in a long time (prevent neglect)
    neglected_threshold = today - timedelta(days=SPACED_REPETITION_CONFIG['NEGLECT_THRESHOLD_DAYS'])
    neglected_cards = qs.filter(
        Q(last_reviewed__lt=neglected_threshold) | Q(last_reviewed__isnull=True),
        times_seen_today__lt=SPACED_REPETITION_CONFIG['MAX_DAILY_REVIEWS'] - 1  # Less strict limit for neglected cards
    ).order_by('last_reviewed', Random())

    card = neglected_cards.first()
    if card:
        return card

    # Priority 3: Random card from available pool (practice mode)
    available_cards = qs.filter(times_seen_today__lt=1).order_by(Random())
    card = available_cards.first()
    if card:
        return card

    # Fallback: Any card (but this should rarely happen)
    return qs.order_by(Random()).first()

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

# Helper for SM-2 update with enhanced tracking
def _update_sm2(card, correct: bool):
    from datetime import datetime, timedelta

    grade = 2 if correct else 0  # Good vs Again mapping
    ef = card.ease_factor
    reps = card.repetitions
    interval = card.interval
    today = datetime.now().date()

    # Update review tracking fields
    card.total_reviews += 1
    if correct:
        card.correct_reviews += 1

    # Calculate difficulty score (0.0 = easy, 1.0 = very difficult)
    if card.total_reviews > 0:
        accuracy = card.correct_reviews / card.total_reviews
        card.difficulty_score = 1.0 - accuracy

    # SM-2 algorithm
    if not correct:
        reps = 0
        interval = 1
        # Increase difficulty for incorrect answers
        card.difficulty_score = min(1.0, card.difficulty_score + 0.1)
    else:
        ef = max(1.3, ef + 0.1 - (5 - 4) * (0.08 + (5 - 4) * 0.02))  # grade 4 equivalent
        reps += 1
        if reps == 1:
            interval = 1
        elif reps == 2:
            interval = 6
        else:
            interval = round(interval * ef)

        # Adjust interval based on difficulty score
        difficulty_multiplier = 1.0 - (card.difficulty_score * SPACED_REPETITION_CONFIG['DIFFICULTY_ADJUSTMENT'])
        interval = max(1, round(interval * difficulty_multiplier))

    next_review_date = today + timedelta(days=interval)
    card.ease_factor = ef
    card.repetitions = reps
    card.interval = interval
    card.next_review = next_review_date
    card.last_reviewed = datetime.now()
    card.save()


@login_required
@require_GET
def api_next_question(request):
    import random as _rnd
    MODES = ['mc', 'type', 'dictation']
    deck_ids = request.GET.getlist('deck_ids[]')

    # Use enhanced card selection algorithm
    card = _get_next_card_enhanced(request.user, deck_ids)
    if not card:
        return JsonResponse({'done': True})

    # Check if card has audio for dictation mode
    has_audio = card.audio_url and card.audio_url.strip()

    # Determine available modes based on audio availability
    available_modes = ['mc', 'type']
    if has_audio:
        available_modes.append('dictation')

    # Select random mode from available options
    mode = _rnd.choice(available_modes)

    # For dictation mode, ensure we have audio
    if mode == 'dictation' and not has_audio:
        mode = _rnd.choice(['mc', 'type'])

    # Update tracking fields when card is shown
    _update_card_shown_tracking(card)

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
    data = json.loads(request.body)
    card_id = data.get('card_id')
    correct = data.get('correct')  # bool
    try:
        card = Flashcard.objects.get(id=card_id, user=request.user)
    except Flashcard.DoesNotExist:
        return JsonResponse({'success': False}, status=404)

    _update_sm2(card, correct)
    return JsonResponse({'success': True})

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
        context = {
            'deck': deck,
            'flashcards': flashcards,
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

@require_GET
def debug_language(request):
    """Debug view to check current language settings"""
    from django.utils import translation
    
    debug_info = {
        'current_language': translation.get_language(),
        'session_language': request.session.get('django_language', 'Not set'),
        'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', 'Not set'),
        'language_from_request': translation.get_language_from_request(request),
        'supported_languages': dict(settings.LANGUAGES),
        'default_language': settings.LANGUAGE_CODE,
    }
    
    return JsonResponse(debug_info)

def language_test(request):
    """Simple test view for language debugging"""
    from django.utils import translation
    
    current_lang = translation.get_language()
    
    # Manual translations for testing
    translations = {
        'en': {
            'title': 'Language Test',
            'welcome': 'Welcome to LearnEnglish',
            'add_words': 'Add New Words',
            'flashcards': 'My Flashcards',
            'navigation': 'Home | Flashcards | Add Word',
            'back': 'Back to Dashboard'
        },
        'vi': {
            'title': 'Test Ngôn Ngữ',
            'welcome': 'Chào mừng đến với LearnEnglish',
            'add_words': 'Thêm từ mới',
            'flashcards': 'Thẻ từ vựng của tôi',
            'navigation': 'Trang chủ | Thẻ từ vựng | Thêm từ',
            'back': 'Về Bảng Điều Khiển'
        }
    }
    
    context = {
        'current_language': current_lang,
        'session_language': request.session.get('django_language', 'Not set'),
        'all_session_data': dict(request.session),
        'texts': translations.get(current_lang, translations['en']),
    }
    
    return render(request, 'vocabulary/language_test.html', context)

@login_required
def statistics_view(request):
    user_decks = Deck.objects.filter(user=request.user)
    total_decks = user_decks.count()
    total_cards = Flashcard.objects.filter(user=request.user).count()
    avg_cards = round(total_cards / total_decks, 2) if total_decks > 0 else 0

    # Prepare data for chart (cards per deck)
    deck_data = user_decks.annotate(card_count=Count('flashcards')).order_by('-card_count')
    deck_labels = [deck.name for deck in deck_data]
    deck_counts = [deck.card_count for deck in deck_data]

    import json as _json
    deck_labels_json = _json.dumps(deck_labels)
    deck_counts_json = _json.dumps(deck_counts)

    context = {
        'total_decks': total_decks,
        'total_cards': total_cards,
        'avg_cards': avg_cards,
        'deck_labels': deck_labels_json,
        'deck_counts': deck_counts_json,
    }
    return render(request, 'vocabulary/statistics.html', context)

@login_required
def study_page(request):
    decks = Deck.objects.filter(user=request.user)
    return render(request, 'vocabulary/study.html', {'decks': decks})

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

    # Use enhanced SM-2 update with grade mapping
    correct = grade >= 2  # Good or Easy considered correct
    _update_sm2(card, correct)
    return JsonResponse({'success': True})
