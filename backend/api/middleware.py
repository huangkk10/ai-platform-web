from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt


class DisableCSRFMiddleware(MiddlewareMixin):
    """
    Disable CSRF protection for specific API endpoints
    """
    
    EXEMPT_URLS = [
        '/api/auth/login/',
        '/api/auth/logout/',
        '/api/dify/',
    ]
    
    def process_request(self, request):
        """
        Check if the request URL should be exempt from CSRF protection
        """
        path = request.path_info
        
        for exempt_url in self.EXEMPT_URLS:
            if path.startswith(exempt_url):
                setattr(request, '_dont_enforce_csrf_checks', True)
                break
                
        return None