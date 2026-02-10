from django.contrib import admin
from .models import Category, Article, ArticleTranslation


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('id', 'name')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
	list_display = ('article_id', 'title', 'status', 'category', 'admin', 'published_at', 'created_at')
	list_filter = ('status', 'category')
	search_fields = ('article_id', 'title')


@admin.register(ArticleTranslation)
class ArticleTranslationAdmin(admin.ModelAdmin):
	list_display = ('id', 'article', 'lang', 'updated_at')
	list_filter = ('lang', 'updated_at')
	search_fields = ('article__article_id', 'article__title')
	readonly_fields = ('source_hash', 'updated_at')
