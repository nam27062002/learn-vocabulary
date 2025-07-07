from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Flashcard # Import your Flashcard model
from django.conf import settings # Import settings
from .api_services import get_word_suggestions_from_datamuse, check_word_spelling_with_languagetool # Import new service functions
from .word_details_service import get_word_details # Import the new service function

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
