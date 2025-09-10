from django.urls import path
from . import views

# API endpoints - these should NOT have language prefixes
# since they return JSON data, not localized HTML content
urlpatterns = [
    # Deck management APIs
    path('api/create-deck/', views.create_deck_api, name='create_deck_api'),
    path('api/save-flashcards/', views.save_flashcards, name='save_flashcards'),
    path('api/check-word-exists/', views.check_word_exists, name='check_word_exists'),
    path('api/search-word-in-decks/', views.api_search_word_in_decks, name='api_search_word_in_decks'),
    path('api/get-word-suggestions/', views.api_get_word_suggestions, name='api_get_word_suggestions'),
    path('api/delete-flashcard/', views.delete_flashcard, name='delete_flashcard'),
    path('api/update-flashcard/', views.api_update_flashcard, name='api_update_flashcard'),
    path('api/test-update-flashcard/', views.api_test_update_flashcard, name='api_test_update_flashcard'),
    path('api/update-deck-name/', views.api_update_deck_name, name='api_update_deck_name'),
    
    # Translation and word services APIs
    path('api/translate-to-vietnamese/', views.translate_to_vietnamese, name='translate_to_vietnamese'),
    path('api/translate-word-to-vietnamese/', views.translate_word_to_vietnamese, name='translate_word_to_vietnamese'),
    path('api/get-related-image/', views.get_related_image, name='get_related_image'),
    
    # Audio APIs
    path('api/fetch-missing-audio/', views.api_fetch_missing_audio, name='api_fetch_missing_audio'),
    path('api/fetch-audio-for-card/', views.api_fetch_audio_for_card, name='api_fetch_audio_for_card'),
    path('api/fetch-enhanced-audio/', views.api_fetch_enhanced_audio, name='api_fetch_enhanced_audio'),
    path('api/update-flashcard-audio/', views.api_update_flashcard_audio, name='api_update_flashcard_audio'),
    
    # Study APIs
    path('api/study/next-card/', views.api_next_card, name='api_next_card'),
    path('api/study/submit-review/', views.api_submit_review, name='api_submit_review'),
    path('api/study/next-question/', views.api_next_question, name='api_next_question'),
    path('api/study/submit-answer/', views.api_submit_answer, name='api_submit_answer'),
    path('api/study/end-session/', views.api_end_study_session, name='api_end_study_session'),
    
    # Statistics APIs
    path('api/statistics/data/', views.api_statistics_data, name='api_statistics_data'),
    path('api/statistics/word-performance/', views.api_word_performance, name='api_word_performance'),
    
    # Incorrect Words Review APIs
    path('api/incorrect-words/add/', views.api_add_incorrect_word, name='api_add_incorrect_word'),
    path('api/incorrect-words/resolve/', views.api_resolve_incorrect_word, name='api_resolve_incorrect_word'),
    path('api/incorrect-words/count/', views.api_get_incorrect_words_count, name='api_get_incorrect_words_count'),

    # Favorites APIs
    path('api/favorites/toggle/', views.api_toggle_favorite, name='api_toggle_favorite'),
    path('api/favorites/count/', views.api_get_favorites_count, name='api_get_favorites_count'),
    path('api/favorites/check/', views.api_check_favorite_status, name='api_check_favorite_status'),

    # Blacklist APIs
    path('api/blacklist/', views.api_blacklist, name='api_blacklist'),
    path('api/blacklist/toggle/', views.api_toggle_blacklist, name='api_toggle_blacklist'),
    path('api/blacklist/count/', views.api_get_blacklist_count, name='api_get_blacklist_count'),
    path('api/blacklist/check/', views.api_check_blacklist_status, name='api_check_blacklist_status'),

    # Language (manual language switch without Django i18n)
    path('api/set-language/', views.api_set_language, name='api_set_language'),
]
