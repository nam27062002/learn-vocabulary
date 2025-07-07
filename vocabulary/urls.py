from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello_world, name='hello_world'),
    path('add/', views.add_flashcard_view, name='add_flashcard'),
    path('suggest-words/', views.suggest_words, name='suggest_words'),
    path('check-spelling/', views.check_word_spelling, name='check_spelling'),
    path('word-details/', views.get_word_details_api, name='get_word_details_api'),
] 