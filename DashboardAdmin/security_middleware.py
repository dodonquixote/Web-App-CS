"""
Simple rate limiting middleware for login attempts
"""
import time
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings
import logging

logger = logging.getLogger('django.security')


class LoginRateLimitMiddleware:
    """
    Simple rate limiting for login attempts
    Blocks IP after MAX_ATTEMPTS failed attempts within BLOCK_DURATION
    
    Configuration:
    - MAX_ATTEMPTS: Number of failed login attempts before blocking (default: 5)
    - BLOCK_DURATION: Duration of block in seconds (default: 900 = 15 minutes)
    - WINDOW_DURATION: Time window to count attempts (default: same as BLOCK_DURATION)
    
    Can be overridden in settings.py:
        LOGIN_RATE_LIMIT_ATTEMPTS = 10
        LOGIN_RATE_LIMIT_BLOCK = 900  # seconds
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Allow configuration via settings
        self.MAX_ATTEMPTS = getattr(settings, 'LOGIN_RATE_LIMIT_ATTEMPTS', 10)
        self.BLOCK_DURATION = getattr(settings, 'LOGIN_RATE_LIMIT_BLOCK', 900)  # 15 minutes
    
    def __call__(self, request):
        # Only check login endpoint
        if request.path == '/dashboard/login/' and request.method == 'POST':
            ip_address = self.get_client_ip(request)
            cache_key = f'login_attempts_{ip_address}'
            
            # Check if IP is blocked
            if cache.get(f'blocked_{ip_address}'):
                logger.warning(f'Blocked login attempt from {ip_address}')
                return HttpResponse(
                    'Too many failed login attempts. Please try again in 15 minutes.',
                    status=429
                )
            
            # Process request
            response = self.get_response(request)
            
            # Track failed attempts (status != 302 means login failed)
            if response.status_code != 302:
                attempts = cache.get(cache_key, 0) + 1
                cache.set(cache_key, attempts, timeout=self.BLOCK_DURATION)
                
                if attempts >= self.MAX_ATTEMPTS:
                    cache.set(f'blocked_{ip_address}', True, timeout=self.BLOCK_DURATION)
                    logger.warning(
                        f'IP {ip_address} blocked after {attempts} failed login attempts'
                    )
            else:
                # Successful login - clear attempts
                cache.delete(cache_key)
                cache.delete(f'blocked_{ip_address}')
            
            return response
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware:
    """
    Add additional security headers
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        if not settings.DEBUG:
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response
