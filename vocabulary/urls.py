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
    path('api/create-deck/', views.create_deck_api, name='create_deck_api'),
    path('suggest-words/', views.suggest_words, name='suggest_words'),
    path('check-spelling/', views.check_word_spelling, name='check_spelling'),
    path('word-details/', views.get_word_details_api, name='get_word_details_api'),
    path('api/save-flashcards/', views.save_flashcards, name='save_flashcards'),
    path('decks/', views.deck_list, name='deck_list'),
    path('decks/<int:deck_id>/', views.deck_detail, name='deck_detail'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('api/check-word-exists/', views.check_word_exists, name='check_word_exists'),
    path('api/delete-flashcard/', views.delete_flashcard, name='delete_flashcard'),
    path('api/translate-to-vietnamese/', views.translate_to_vietnamese, name='translate_to_vietnamese'),
    path('api/translate-word-to-vietnamese/', views.translate_word_to_vietnamese, name='translate_word_to_vietnamese'),
    path('api/get-related-image/', views.get_related_image, name='get_related_image'),
    path('debug/language/', views.debug_language, name='debug_language'),
    path('test/language/', views.language_test, name='language_test'),
    path('study/', views.study_page, name='study'),
    path('api/study/next-card/', views.api_next_card, name='api_next_card'),
    path('api/study/submit-review/', views.api_submit_review, name='api_submit_review'),
    path('api/study/next-question/', views.api_next_question, name='api_next_question'),
    path('api/study/submit-answer/', views.api_submit_answer, name='api_submit_answer'),
    path('api/update-flashcard/', views.api_update_flashcard, name='api_update_flashcard'),
    path('api/update-deck-name/', views.api_update_deck_name, name='api_update_deck_name'),
]