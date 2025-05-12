import sys
import traceback
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve, Resolver404
from .services import AsyncErrorLogger

class ErrorLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to catch and log unhandled exceptions in views.
    Automatically detects the component from the URL or module name.
    """
    
    # Default app name to source mapping - used only as a fallback
    DEFAULT_SOURCES = {
        'sp': 'SP', 
        'sb': 'SB', 
        'sd': 'SD',
        'sqp': 'SQP',
        'lister': 'LISTENER'
    }
    
    def process_exception(self, request, exception):
        """
        Process the exception and log it.
        Automatically determines the source component from the URL or view module.
        """
        # Extract view and route information
        view_name = self._get_view_name(request)
        url_name = self._get_url_name(request)
        module_name = self._get_module_name(request)
        source = self._determine_source(request, module_name)
        
        # Extract relevant request information
        metadata = {
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', None),
            'ip': self._get_client_ip(request),
            'view_name': view_name,
            'url_name': url_name,
            'module_name': module_name,
            'request_data': self._get_request_data(request),
        }
        
        # Create component name based on route information
        component = f"{view_name or 'unknown'}"
        if url_name:
            component += f":{url_name}"
        
        # Log the error asynchronously
        AsyncErrorLogger.log_error_async(
            message=str(exception),
            level='ERROR',
            source=source,
            component=component,
            exc_info=sys.exc_info(),
            metadata=metadata
        )
        
        # Continue processing (will eventually reach Django's own exception handling)
        return None
    
    def _determine_source(self, request, module_name=None):
        """
        Determine the source component based on URL path or module name.
        
        This uses the first segment of the URL path for API routes, or the 
        module name of the view function for non-API routes.
        """
        path = request.path.strip('/')
        
        # Check API pattern like /api/v1/sp/ 
        if path.startswith('api/'):
            parts = path.split('/')
            if len(parts) >= 3:  # api/v1/component/...
                component = parts[2].upper()
                # Return known component codes or the uppercase app name
                return self.DEFAULT_SOURCES.get(parts[2], component)
        
        # Use first path segment if not empty
        parts = path.split('/')
        if parts and parts[0]:
            component = parts[0].upper()
            return self.DEFAULT_SOURCES.get(parts[0], component)
                
        # Fallback to module name
        if module_name:
            module_parts = module_name.split('.')
            if module_parts:
                app_name = module_parts[0]
                component = app_name.upper()
                return self.DEFAULT_SOURCES.get(app_name, component)
        
        # Final fallback
        return 'SYSTEM'
    
    def _get_module_name(self, request):
        """Get the module name of the view function"""
        try:
            if hasattr(request, 'resolver_match') and request.resolver_match:
                if hasattr(request.resolver_match, 'func'):
                    func = request.resolver_match.func
                    if hasattr(func, '__module__'):
                        return func.__module__
            return None
        except Exception:
            return None
        
    def _get_view_name(self, request):
        """Get the name of the view function handling the request"""
        try:
            if hasattr(request, 'resolver_match') and request.resolver_match:
                if hasattr(request.resolver_match, 'func') and request.resolver_match.func:
                    # Get function name
                    func = request.resolver_match.func
                    if hasattr(func, '__name__'):
                        return func.__name__
                    return str(func)
            return None
        except Exception:
            return None
    
    def _get_url_name(self, request):
        """Get the URL name if available"""
        try:
            if hasattr(request, 'resolver_match') and request.resolver_match:
                return request.resolver_match.url_name
            return None
        except Exception:
            return None
        
    def _get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
        
    def _get_request_data(self, request):
        """Extract useful data from the request object."""
        data = {}
        
        try:
            # GET parameters
            if request.GET:
                data['query_params'] = dict(request.GET.items())
                
            # POST parameters (excluding files)
            if request.POST:
                data['post_data'] = dict(request.POST.items())
                
            # Headers (excluding cookies and authorization)
            headers = {}
            for key, value in request.META.items():
                if key.startswith('HTTP_') and key not in ('HTTP_COOKIE', 'HTTP_AUTHORIZATION'):
                    headers[key[5:].lower()] = value
            if headers:
                data['headers'] = headers
                
            # Files (just names and sizes, not content)
            if request.FILES:
                files = []
                for key, file in request.FILES.items():
                    files.append({
                        'field': key,
                        'name': file.name,
                        'size': file.size,
                        'content_type': file.content_type,
                    })
                data['files'] = files
            
            # URL parameters from resolver match
            if hasattr(request, 'resolver_match') and request.resolver_match:
                if hasattr(request.resolver_match, 'kwargs') and request.resolver_match.kwargs:
                    data['url_params'] = request.resolver_match.kwargs
                
        except Exception as e:
            # Don't let this interfere with the error logging
            data['extraction_error'] = str(e)
            
        return data 