from django.urls import path
from . import views

urlpatterns = [
    path('dictation/', views.video_list, name='dictation_list'),
    path('dictation/<str:video_id>/', views.practice, name='dictation_practice'),
]
