from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
import os


@login_required
def upload_avatar(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    if 'avatar' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)

    file = request.FILES['avatar']

    # Basic validation: limit size ~2MB and simple content-type check
    if file.size > 2 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'File too large (max 2MB)'}, status=400)

    if not str(file.content_type).startswith('image/'):
        return JsonResponse({'success': False, 'error': 'Invalid file type'}, status=400)

    user = request.user
    
    # Delete old avatar if exists
    if user.avatar:
        old_avatar_path = os.path.join(settings.MEDIA_ROOT, str(user.avatar))
        if os.path.exists(old_avatar_path):
            try:
                os.remove(old_avatar_path)
            except OSError:
                pass  # Ignore if file can't be deleted
    
    # Ensure avatars directory exists
    avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
    os.makedirs(avatars_dir, exist_ok=True)
    
    user.avatar = file
    user.save(update_fields=['avatar'])

    avatar_url = user.avatar.url if user.avatar else user.avatar_url
    return JsonResponse({'success': True, 'avatar_url': avatar_url})

 
# Create your views here. 