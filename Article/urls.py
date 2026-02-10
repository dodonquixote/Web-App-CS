from . import views
from django.urls import path, include

urlpatterns = [
    path('anime/', views.anime, name='anime'),
    path('', views.home, name='home'),
    path('event/', views.event, name='event'),
    path('game/', views.game, name='game'),
    path('geek/', views.geek, name='geek'),
    path('article/', views.article, name='article'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('api/articles/<str:category_name>/', views.api_articles_by_category, name='api_articles'),
    path('api/articles/<str:category_name>/pinned/', views.api_pinned_article, name='api_pinned_article'),
    path('api/article/<slug:slug>/', views.api_article_detail, name='api_article_detail'),
    # Accept both with and without trailing slash to avoid APPEND_SLASH POST redirect errors
    path('api/translate', views.api_translate, name='api_translate_noslash'),
    path('api/translate/', views.api_translate, name='api_translate'),
    path('coba/', views.coba, name='coba'),
    path('test-translation/', views.test_translation, name='test_translation'),
    # Temporary testing route to preview the custom 404 page without changing DEBUG
    path('test-404/', views.custom_404, name='test_404'),
]