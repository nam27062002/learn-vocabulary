"""
URL configuration for learn_english_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language, JavaScriptCatalog

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # Authentication URLs
    path('i18n/', include('django.conf.urls.i18n')),  # Include i18n URLs (not affected by language prefix)
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),  # JavaScript i18n catalog

    # API endpoints - NO language prefix (return JSON, not localized HTML)
    path('', include('vocabulary.api_urls')),
]

# Internationalized URLs - pages that need language prefixes
urlpatterns += i18n_patterns(
    path('', include('vocabulary.urls')),
    prefix_default_language=True  # Always show language prefix to avoid confusion
)

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
