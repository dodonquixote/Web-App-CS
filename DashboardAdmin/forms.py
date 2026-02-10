
from django import forms
from .models import Article, Category
from .models import SiteSetting
from django.utils import timezone
from django.forms.widgets import ClearableFileInput


class CustomImageWidget(ClearableFileInput):
	"""Custom widget that hides the 'Currently' text and file path"""
	initial_text = ''
	input_text = ''
	clear_checkbox_label = ''
	
	def render(self, name, value, attrs=None, renderer=None):
		# Override to not show the file path at all
		from django.utils.html import format_html
		from django.forms.utils import flatatt
		
		final_attrs = self.build_attrs(attrs, {'type': 'file', 'name': name})
		if 'required' in final_attrs:
			final_attrs.pop('required')
		
		html = format_html('<input{} />', flatatt(final_attrs))
		return html


class ArticleForm(forms.ModelForm):
	published_at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

	class Meta:
		model = Article
		fields = ['article_id', 'title', 'content', 'featured_image', 'status', 'published_at', 'category']
		widgets = {
			'content': forms.Textarea(attrs={'rows': 20}),
			'status': forms.Select(),
		}

	def __init__(self, *args, **kwargs):
		# Ensure category queryset is available and published_at is formatted for datetime-local
		super().__init__(*args, **kwargs)
		try:
			self.fields['category'].queryset = Category.objects.all()
		except Exception:
			pass

		# If initialized with an instance that has published_at, format it for datetime-local
		instance = kwargs.get('instance')
		if instance is not None:
			# ensure category initial is set to the instance's category PK so the select shows it
			if getattr(instance, 'category', None):
				try:
					self.initial.setdefault('category', instance.category.pk)
				except Exception:
					pass
			if getattr(instance, 'published_at', None):
				local_dt = timezone.localtime(instance.published_at)
				self.initial.setdefault('published_at', local_dt.strftime('%Y-%m-%dT%H:%M'))


class SiteSettingForm(forms.ModelForm):
	class Meta:
		model = SiteSetting
		fields = ['spotify_link', 'youtube_link', 'youtube_desc', 'vote_link', 'translate_api_url', 'translate_api_key', 'ad_left', 'ad_left_link', 'ad_right', 'ad_right_link', 'ad_down', 'ad_down_link', 'ad_top', 'ad_top_link']
		widgets = {
			'spotify_link': forms.URLInput(attrs={'placeholder': 'https://open.spotify.com/...', 'class': 'w-full p-2 border rounded'}),
			'youtube_link': forms.URLInput(attrs={'placeholder': 'https://www.youtube.com/...', 'class': 'w-full p-2 border rounded'}),
			'youtube_desc': forms.Textarea(attrs={'rows':3, 'placeholder':'Short description/caption for the featured video', 'class':'w-full p-2 border rounded'}),
			'vote_link': forms.URLInput(attrs={'placeholder': 'https://example.com/vote', 'class': 'w-full p-2 border rounded'}),
			'translate_api_url': forms.URLInput(attrs={'placeholder': 'http://127.0.0.1:5000/translate', 'class': 'w-full p-2 border rounded'}),
			'translate_api_key': forms.TextInput(attrs={'placeholder': 'Optional API key (leave blank if none)', 'class': 'w-full p-2 border rounded'}),
			'ad_left_link': forms.URLInput(attrs={'placeholder': 'https://example.com/landing', 'class': 'w-full p-2 border rounded'}),
			'ad_right_link': forms.URLInput(attrs={'placeholder': 'https://example.com/landing', 'class': 'w-full p-2 border rounded'}),
			'ad_top_link': forms.URLInput(attrs={'placeholder': 'https://example.com/landing', 'class': 'w-full p-2 border rounded'}),
			'ad_down_link': forms.URLInput(attrs={'placeholder': 'https://example.com/landing', 'class': 'w-full p-2 border rounded'}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Use custom widget that doesn't show file path
		for field_name in ['ad_left', 'ad_right', 'ad_top', 'ad_down']:
			if field_name in self.fields:
				self.fields[field_name].widget = CustomImageWidget(attrs={'class': 'w-full'})