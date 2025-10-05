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
    path('word-details/', views.get_word_details_api, name='get_word_details_api'),
    path('decks/', views.deck_list, name='deck_list'),
    path('decks/<int:deck_id>/', views.deck_detail, name='deck_detail'),
    path('decks/<int:deck_id>/delete/', views.delete_deck, name='delete_deck'),
    path('favorites/', views.favorites_page, name='favorites'),
    path('blacklist/', views.blacklist_page, name='blacklist'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('study/', views.study_page, name='study'),
    
    # Notes functionality
    path('notes/', views.notes_list, name='notes_list'),
    path('notes/add/', views.note_create, name='note_create'),
    path('notes/<int:note_id>/', views.note_detail, name='note_detail'),
    path('notes/<int:note_id>/edit/', views.note_edit, name='note_edit'),
    path('notes/<int:note_id>/delete/', views.note_delete, name='note_delete'),
    
    path('test-statistics/', views.test_statistics_view, name='test_statistics'),
    path('debug-study/', views.debug_study_template, name='debug_study'),
]