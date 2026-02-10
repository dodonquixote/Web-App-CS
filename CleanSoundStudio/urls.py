from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Article import views as article_views

def add_lang_kwarg(urlpatterns, lang):
    """Add lang kwarg to all article URL patterns"""
    new_patterns = []
    for pattern in urlpatterns:
        if hasattr(pattern.pattern, '_route'):
            # For path() patterns
            pattern.default_args = {**(pattern.default_args or {}), 'lang': lang}
        new_patterns.append(pattern)
    return new_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('DashboardAdmin.urls')),
    # Article URLs without language prefix (default Indonesian)
    path('', include('Article.urls')),
    # Article URLs with language prefix (en, jp, ja, id)
    path('en/', include('Article.urls'), kwargs={'lang': 'en'}),
    path('jp/', include('Article.urls'), kwargs={'lang': 'jp'}),
    path('ja/', include('Article.urls'), kwargs={'lang': 'ja'}),
    path('id/', include('Article.urls'), kwargs={'lang': 'id'}),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom 404 handler (renders Article/not-found.html)
handler404 = 'Article.views.custom_404'