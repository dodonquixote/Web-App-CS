from .views import index, list_articles, login, logout, view_article, edit_article, delete_article, settings_view, fetch_youtube_desc, debug_settings, pin_article
from django.urls import path
from django.views.generic.base import RedirectView
from .views import upload_image

app_name = 'DashboardAdmin'

urlpatterns = [
    # Dashboard root redirects to the articles listing (/dashboard/articles/)
    path('', RedirectView.as_view(pattern_name='DashboardAdmin:list_articles', permanent=False), name='index'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    # API moved to `Article` app: /api/articles/<category>/
    path('articles/', list_articles, name='list_articles'),
    # Add article is at /dashboard/add/
    path('add/', index, name='add_article'),
    path('articles/<slug:slug>/', view_article, name='view_article'),
    path('articles/<slug:slug>/edit/', edit_article, name='edit_article'),
    path('articles/<slug:slug>/delete/', delete_article, name='delete_article'),
    path('articles/<slug:slug>/pin/', pin_article, name='pin_article'),
    # image upload endpoint used by TinyMCE
    path('upload-image/', upload_image, name='upload_image'),
    path('settings/', settings_view, name='settings'),
    path('fetch-youtube-desc/', fetch_youtube_desc, name='fetch_youtube_desc'),
    path('debug-settings/', debug_settings, name='debug_settings'),

]