from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


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
    user.avatar = file
    user.save(update_fields=['avatar'])

    return JsonResponse({'success': True, 'avatar_url': user.avatar.url})

 
# Create your views here. 