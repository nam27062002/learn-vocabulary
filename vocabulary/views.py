from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Flashcard, Definition # Import your Flashcard and Definition models
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

# Create your views here.

def dashboard(request):
    # Thống kê cơ bản
    total_cards = Flashcard.objects.count()
    recent_cards = Flashcard.objects.filter(
        created_at__gte=datetime.now() - timedelta(days=7)
    ).count()
    
    # Tính progress percentage (dựa trên target 50 cards/tuần)
    weekly_target = 50
    progress_percentage = min((recent_cards / weekly_target) * 100, 100) if weekly_target > 0 else 0
    
    # Flashcard gần đây
    latest_cards = Flashcard.objects.select_related().prefetch_related('definitions').order_by('-created_at')[:6]
    
    # Thống kê theo ngày (7 ngày gần đây)
    daily_stats = []
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        count = Flashcard.objects.filter(
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

def add_flashcard_view(request):
    return render(request, 'vocabulary/add_flashcard.html')

def suggest_words(request):
    query = request.GET.get('q', '')

    if settings.ENABLE_DEBUG:
        print(f"[DEBUG] suggest_words called with query: {query}")

    suggestions = get_word_suggestions_from_datamuse(query)

    if settings.ENABLE_DEBUG:
        print(f"[DEBUG] Returning suggestions: {suggestions}")

    return JsonResponse(suggestions, safe=False)

def check_word_spelling(request):
    if request.method == 'POST':
        word = request.POST.get('word', '')

        if settings.ENABLE_DEBUG:
            print(f"[DEBUG] check_word_spelling called with word: {word}")

        if word:
            is_correct = check_word_spelling_with_languagetool(word)

            if settings.ENABLE_DEBUG:
                print(f"[DEBUG] Is word '{word}' correct? {is_correct}")

            return JsonResponse({'is_correct': is_correct})

    if settings.ENABLE_DEBUG:
        print(f"[DEBUG] Invalid request for check_word_spelling. Method: {request.method}")

    return JsonResponse({'error': 'Invalid request'}, status=400)

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

@csrf_exempt
@require_POST
def save_flashcards(request):
    try:
        flashcards = []
        idx = 0
        while True:
            prefix = f'flashcards[{idx}]'
            word = request.POST.get(f'{prefix}[word]')
            part_of_speech = request.POST.get(f'{prefix}[part_of_speech]')
            english_definition = request.POST.get(f'{prefix}[english_definition]')
            vietnamese_definition = request.POST.get(f'{prefix}[vietnamese_definition]')
            audio_url = request.POST.get(f'{prefix}[audio_url]')
            image = request.FILES.get(f'{prefix}[image]')
            if not word:
                break
            # Lưu flashcard
            flashcard = Flashcard(
                word=word,
                part_of_speech=part_of_speech,
                audio_url=audio_url,
                image=image  # Gán trực tiếp, Django sẽ tự lưu file
            )
            flashcard.save()
            # Lưu definition với cả English và Vietnamese
            Definition.objects.create(
                flashcard=flashcard,
                english_definition=english_definition,
                vietnamese_definition=vietnamese_definition or ''
            )
            flashcards.append(flashcard.word)
            idx += 1
        return JsonResponse({'success': True, 'saved': flashcards})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def flashcard_list(request):
    flashcards = Flashcard.objects.all().order_by('-created_at')
    flashcard_defs = []
    for card in flashcards:
        definitions = card.definitions.all()
        flashcard_defs.append((card, definitions))
    return render(request, 'vocabulary/flashcard_list.html', {'flashcard_defs': flashcard_defs})

@require_GET
def check_word_exists(request):
    word = request.GET.get('word', '').strip()
    exists = Flashcard.objects.filter(word__iexact=word).exists()
    return JsonResponse({'exists': exists})

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
            # Lấy instance để gọi method delete() tùy chỉnh (xóa file hình ảnh)
            flashcard = Flashcard.objects.get(id=card_id)
            flashcard.delete()  # Gọi method delete() tùy chỉnh
            return JsonResponse({'success': True})
        except Flashcard.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Không tìm thấy flashcard để xóa'})
            
    except json.JSONDecodeError as e:
        return JsonResponse({'success': False, 'error': f'Lỗi parse JSON: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Lỗi server: {str(e)}'})

@require_GET
def translate_to_vietnamese(request):
    """API to translate English text to Vietnamese"""
    text = request.GET.get('text', '').strip()
    
    if not text:
        return JsonResponse({'error': 'No text provided'}, status=400)
    
    try:
        translator = Translator()
        result = translator.translate(text, src='en', dest='vi')
        
        return JsonResponse({
            'original': text,
            'translated': result.text,
            'detected_language': result.src
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Translation failed: {str(e)}'}, status=500)

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
