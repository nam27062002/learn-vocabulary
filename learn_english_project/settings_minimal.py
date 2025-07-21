import os
from .settings import *

# Minimal production settings
DEBUG = False
ENABLE_DEBUG = False

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-key-for-render-deployment')

# Allowed hosts
ALLOWED_HOSTS = ['*']  # Allow all hosts for simplicity

# Use SQLite for simplicity
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files with WhiteNoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Disable all security features that might cause issues
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# Simple email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable problematic features temporarily
SOCIALACCOUNT_PROVIDERS = {}  # Disable Google OAuth temporarily