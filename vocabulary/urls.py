from django.urls import path
from . import views
from django.shortcuts import redirect

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('account_login')

urlpatterns = [
    path('', home_redirect, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add/', views.add_flashcard_view, name='add_flashcard'),
    path('suggest-words/', views.suggest_words, name='suggest_words'),
    path('check-spelling/', views.check_word_spelling, name='check_spelling'),
    path('word-details/', views.get_word_details_api, name='get_word_details_api'),
    path('api/save-flashcards/', views.save_flashcards, name='save_flashcards'),
    path('flashcards/', views.flashcard_list, name='flashcard_list'),
    path('api/check-word-exists/', views.check_word_exists, name='check_word_exists'),
    path('api/delete-flashcard/', views.delete_flashcard, name='delete_flashcard'),
    path('api/translate-to-vietnamese/', views.translate_to_vietnamese, name='translate_to_vietnamese'),
    path('api/translate-word-to-vietnamese/', views.translate_word_to_vietnamese, name='translate_word_to_vietnamese'),
    path('api/get-related-image/', views.get_related_image, name='get_related_image'),
    path('debug/language/', views.debug_language, name='debug_language'),
    path('test/language/', views.language_test, name='language_test'),
] 