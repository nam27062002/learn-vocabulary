from django.urls import path
from . import views

urlpatterns = [
    path('api/dictation/process-video/', views.api_process_video, name='dictation_process_video'),
    path('api/dictation/videos/<str:video_id>/segments/', views.api_get_segments, name='dictation_get_segments'),
    path('api/dictation/check-answer/', views.api_check_answer, name='dictation_check_answer'),
    path('api/dictation/save-attempt/', views.api_save_attempt, name='dictation_save_attempt'),
    path('api/dictation/progress/<str:video_id>/', views.api_get_progress, name='dictation_progress'),
    path('api/dictation/quiz/generate/<str:video_id>/', views.api_generate_quiz, name='dictation_generate_quiz'),
    path('api/dictation/quiz/submit/<int:quiz_id>/', views.api_submit_quiz, name='dictation_submit_quiz'),
]
