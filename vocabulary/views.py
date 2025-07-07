from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Flashcard, Definition # Import your Flashcard and Definition models
from django.conf import settings # Import settings
from .api_services import get_word_suggestions_from_datamuse, check_word_spelling_with_languagetool # Import new service functions
from .word_details_service import get_word_details # Import the new service function
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import json

# Create your views here.

def hello_world(request):
    return HttpResponse("hello")

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
            audio_url = request.POST.get(f'{prefix}[audio_url]')
            image = request.FILES.get(f'{prefix}[image]')
            if not word:
                break
            # Lưu flashcard
            flashcard = Flashcard(
                word=word,
                part_of_speech=part_of_speech,
                audio_url=audio_url
            )
            if image:
                flashcard.image.save(image.name, image)
            flashcard.save()
            # Lưu definition (chỉ tiếng Anh, tiếng Việt để rỗng)
            Definition.objects.create(
                flashcard=flashcard,
                english_definition=english_definition,
                vietnamese_definition='' # Có thể bổ sung nếu cần
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

@csrf_exempt
@require_POST
def delete_flashcard(request):
    try:
        data = json.loads(request.body)
        card_id = data.get('id')
        Flashcard.objects.filter(id=card_id).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
