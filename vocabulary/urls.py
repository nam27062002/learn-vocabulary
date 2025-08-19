from django.urls import path
from . import views
from django.shortcuts import redirect

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('account_login')

# Page URLs - these SHOULD have language prefixes for localization
urlpatterns = [
    path('', home_redirect, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add/', views.add_flashcard_view, name='add_flashcard'),
    path('suggest-words/', views.suggest_words, name='suggest_words'),
    path('check-spelling/', views.check_word_spelling, name='check_spelling'),
    path('word-details/', views.get_word_details_api, name='get_word_details_api'),
    path('decks/', views.deck_list, name='deck_list'),
    path('decks/<int:deck_id>/', views.deck_detail, name='deck_detail'),
    path('decks/<int:deck_id>/delete/', views.delete_deck, name='delete_deck'),
    path('favorites/', views.favorites_page, name='favorites'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('study/', views.study_page, name='study'),
    path('test-statistics/', views.test_statistics_view, name='test_statistics'),
    path('debug-study/', views.debug_study_template, name='debug_study'),
]