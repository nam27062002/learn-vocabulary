from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_flashcard_view, name='add_flashcard'),
    path('suggest-words/', views.suggest_words, name='suggest_words'),
    path('check-spelling/', views.check_word_spelling, name='check_spelling'),
    path('word-details/', views.get_word_details_api, name='get_word_details_api'),
    path('api/save-flashcards/', views.save_flashcards, name='save_flashcards'),
    path('flashcards/', views.flashcard_list, name='flashcard_list'),
    path('api/check-word-exists/', views.check_word_exists, name='check_word_exists'),
    path('api/delete-flashcard/', views.delete_flashcard, name='delete_flashcard'),
] 