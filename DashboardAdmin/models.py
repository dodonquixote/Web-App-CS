from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

import itertools

User = get_user_model()


class Category(models.Model):
	name = models.CharField(max_length=100)

	def __str__(self):
		return self.name


class Article(models.Model):
	STATUS_CHOICES = [
		('draft', 'Draft'),
		('published', 'Published'),
		('archived', 'Archived'),
	]

	article_id = models.CharField(max_length=50, unique=True)
	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=255, unique=True, blank=True)
	content = models.TextField()
	featured_image = models.ImageField(upload_to='articles/', null=True, blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
	published_at = models.DateTimeField(null=True, blank=True)
	category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
	admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
	# allow pinning one article per category (only one article with is_pinned=True per category)
	is_pinned = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.article_id} - {self.title}"

	def save(self, *args, **kwargs):
		# generate unique slug from title if not present
		if not self.slug:
			base = slugify(self.title)[:200]
			slug = base
			for i in itertools.count(1):
				if not Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
					self.slug = slug
					break
				slug = f"{base}-{i}"
		# Save first so we have a primary key when toggling other records
		super().save(*args, **kwargs)

		# If this article is pinned, ensure no other article in same category remains pinned
		try:
			if self.is_pinned:
				Article.objects.filter(category=self.category, is_pinned=True).exclude(pk=self.pk).update(is_pinned=False)
		except Exception:
			# Be defensive: do not raise on save if DB not ready or migration state
			pass


class ArticleTranslation(models.Model):
	LANG_CHOICES = [
		('id', 'Indonesian'),
		('en', 'English'),
		('ja', 'Japanese'),
	]

	article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='translations')
	lang = models.CharField(max_length=5, choices=LANG_CHOICES)
	title = models.CharField(max_length=500)
	content = models.TextField()
	desc = models.TextField(blank=True, default='')
	source_hash = models.CharField(max_length=64, blank=True, default='')
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['article', 'lang'], name='unique_article_lang')
		]

	def __str__(self):
		try:
			return f"{self.article.article_id} - {self.lang}"
		except Exception:
			return f"ArticleTranslation - {self.lang}"


class SiteSetting(models.Model):
	"""Simple singleton model to store site-wide links and settings for the dashboard.

	Use SiteSetting.get_solo() to retrieve the single instance.
	"""
	spotify_link = models.URLField(max_length=500, blank=True, default='')
	youtube_link = models.URLField(max_length=500, blank=True, default='')
	# Short description / caption for the featured YouTube video shown on the homepage
	youtube_desc = models.TextField(blank=True, default='')
	# Link for the "vote" action used on the homepage (configurable)
	vote_link = models.URLField(max_length=1000, blank=True, default='')
	# Optional ad images for site layout (left / right / bottom)
	ad_left = models.ImageField(upload_to='ads/', null=True, blank=True)
	ad_right = models.ImageField(upload_to='ads/', null=True, blank=True)
	ad_down = models.ImageField(upload_to='ads/', null=True, blank=True)
	# Additional ad slot (top or header) — new field for fourth ad
	ad_top = models.ImageField(upload_to='ads/', null=True, blank=True)
	# Optional target URLs for each ad image
	ad_left_link = models.URLField(max_length=1000, blank=True, default='')
	ad_right_link = models.URLField(max_length=1000, blank=True, default='')
	ad_top_link = models.URLField(max_length=1000, blank=True, default='')
	ad_down_link = models.URLField(max_length=1000, blank=True, default='')

	# Translation service settings (self-hosted LibreTranslate URL + optional API key)
	translate_api_url = models.URLField(max_length=1000, blank=True, default='')
	translate_api_key = models.CharField(max_length=500, blank=True, default='')

	class Meta:
		verbose_name = 'Site Setting'
		verbose_name_plural = 'Site Settings'

	def __str__(self):
		return 'Site settings'

	@classmethod
	def get_solo(cls):
		obj, created = cls.objects.get_or_create(pk=1)
		return obj

class SiteSettingTranslation(models.Model):
	"""Store translations of SiteSetting.youtube_desc in multiple languages."""
	
	LANG_CHOICES = [
		('id', 'Indonesian'),
		('en', 'English'),
		('ja', 'Japanese'),
	]

	setting = models.ForeignKey(SiteSetting, on_delete=models.CASCADE, related_name='translations')
	lang = models.CharField(max_length=5, choices=LANG_CHOICES)
	youtube_desc = models.TextField(blank=True, default='')
	source_hash = models.CharField(max_length=64, blank=True, default='')
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['setting', 'lang'], name='unique_sitesetting_lang')
		]

	def __str__(self):
		return f"SiteSetting - {self.lang}"