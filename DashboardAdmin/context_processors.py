from django.conf import settings


def tinymce_api_key(request):
    """
    Add TinyMCE API key to template context
    """
    return {
        'TINYMCE_API_KEY': settings.TINYMCE_API_KEY,
    }
