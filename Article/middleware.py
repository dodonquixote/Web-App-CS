"""
Language middleware to handle language routing.
Extracts language from URL and stores it in request context.
"""
from django.conf import settings


class NgrokHostMiddleware:
    """Dynamically add ngrok domains to ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        http_host = request.META.get('HTTP_HOST', '')
        http_origin = request.META.get('HTTP_ORIGIN', '')
        host = http_host.split(':')[0]  # Remove port if present
        
        # Check if this is an ngrok domain and add to ALLOWED_HOSTS if not present
        if (host.endswith('.ngrok-free.app') or host.endswith('.ngrok.io') or 
            host == 'ngrok-free.app' or host == 'ngrok.io'):
            if host not in settings.ALLOWED_HOSTS:
                settings.ALLOWED_HOSTS.append(host)
        
        # Also add ngrok origin to CSRF_TRUSTED_ORIGINS if it's an ngrok domain
        if http_origin:
            if ('ngrok-free.app' in http_origin or 'ngrok.io' in http_origin):
                if http_origin not in settings.CSRF_TRUSTED_ORIGINS:
                    settings.CSRF_TRUSTED_ORIGINS.append(http_origin)
        
        response = self.get_response(request)
        return response


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract language from URL path
        # URLs can be: /, /en/, /jp/, /ja/, /id/
        # or: /article/slug/, /en/article/slug/, /jp/article/slug/, /ja/article/slug/, /id/article/slug/
        
        lang = 'id'  # default
        path_parts = request.path.strip('/').split('/')
        
        if path_parts and path_parts[0] in ['id', 'en', 'jp', 'ja']:
            lang = path_parts[0]
            # Normalize ja to ja (not jp)
            if lang == 'jp':
                lang = 'ja'
        
        # Store language in request context
        request.language = lang
        
        # Set language in session for persistence
        if hasattr(request, 'session'):
            request.session['language'] = lang
        
        response = self.get_response(request)
        return response
