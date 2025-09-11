from django.urls import path
from .views import upload_avatar

urlpatterns = [
    path('avatar/', upload_avatar, name='upload_avatar'),
]


