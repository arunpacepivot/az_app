import functools
import inspect
import sys
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Union

from django.db import models
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from .services import AsyncErrorLogger

def log(
    message: str, 
    level: str = 'ERROR', 
    source: Optional[str] = None,
    component: Optional[str] = None,
    exc_info: Any = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Unified logging function that handles all types of logs.
    
    This single function replaces all the specific logging functions with
    automatic source detection and simplified usage.
    
    Args:
        message: The log message
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        source: Source component (auto-detected if None)
        component: Component name (auto-detected if None)
        exc_info: Exception info (True for current, or pass exception instance)
        metadata: Additional contextual data
    
    Examples:
        # Simple error log
        log("File processing failed")
        
        # Warning with component and metadata
        log("Invalid file format", level="WARNING", component="file_processor", 
            metadata={"file": "data.xlsx", "format": "csv"})
            
        # Log an exception with full traceback
        try:
            process_file()
        except Exception as e:
            log("Error processing file", exc_info=e, 
                metadata={"file_id": file_id})
    """
    # Get caller information
    frame = inspect.currentframe().f_back
    caller = inspect.getframeinfo(frame)
    
    # Auto-detect source from module name if not provided
    if source is None:
        module_name = caller.frame.f_globals['__name__'].split('.')
        if module_name and len(module_name) > 0:
            app_name = module_name[0].lower()
            source_map = {
                'sp': 'SP',
                'sb': 'SB',
                'sd': 'SD',
                'sqp': 'SQP',
                'lister': 'LISTENER',
            }
            source = source_map.get(app_name, app_name.upper())
    
    # Auto-detect component from caller if not provided
    if component is None:
        component = f"{caller.function}:{caller.lineno}"
    
    # Log the message
    AsyncErrorLogger.log_error_async(
        message=message,
        level=level,
        source=source,
        component=component,
        exc_info=exc_info,
        metadata=metadata
    )

def log_request(
    url: str,
    method: str = 'GET',
    status_code: Optional[int] = None,
    request_data: Any = None,
    response_data: Any = None,
    headers: Optional[Dict[str, str]] = None,
    duration_ms: Optional[float] = None,
    error: Optional[Exception] = None,
    level: str = 'INFO'
) -> None:
    """
    Log API requests and responses.
    
    This function is designed to log both outgoing and incoming API requests
    with their responses, which is useful for debugging network issues.
    
    Args:
        url: The request URL
        method: HTTP method (GET, POST, etc.)
        status_code: Response status code (if available)
        request_data: Request data (body/params)
        response_data: Response data
        headers: Request headers (sensitive headers will be redacted)
        duration_ms: Request duration in milliseconds
        error: Exception if request failed
        level: Log level (default: INFO, automatically set to ERROR if error exists)
    
    Examples:
        # Log a successful API call
        response = requests.get("https://api.example.com/data")
        log_request(
            url="https://api.example.com/data",
            method="GET",
            status_code=response.status_code,
            response_data=response.json(),
            duration_ms=850
        )
        
        # Log a failed API call
        try:
            response = requests.post("https://api.example.com/data", 
                                     json={"key": "value"})
            response.raise_for_status()
        except Exception as e:
            log_request(
                url="https://api.example.com/data",
                method="POST",
                request_data={"key": "value"},
                error=e,
                level="ERROR"
            )
    """
    # Set level to ERROR if there's an error
    if error and level == 'INFO':
        level = 'ERROR'
    
    # Create a safe copy of headers with sensitive data redacted
    safe_headers = None
    if headers:
        safe_headers = {}
        for key, value in headers.items():
            if key.lower() in ('authorization', 'cookie', 'x-api-key', 'api-key'):
                safe_headers[key] = '[REDACTED]'
            else:
                safe_headers[key] = value
    
    # Create metadata
    metadata = {
        'url': url,
        'method': method,
        'duration_ms': duration_ms,
    }
    
    if status_code:
        metadata['status_code'] = status_code
        
    if request_data:
        try:
            # Try to convert to JSON-friendly format
            if isinstance(request_data, dict) or isinstance(request_data, list):
                metadata['request_data'] = request_data
            else:
                metadata['request_data'] = str(request_data)
        except:
            metadata['request_data'] = str(request_data)
    
    if response_data:
        try:
            # Try to convert to JSON-friendly format
            if isinstance(response_data, dict) or isinstance(response_data, list):
                metadata['response_data'] = response_data
            else:
                metadata['response_data'] = str(response_data)
        except:
            metadata['response_data'] = str(response_data)
            
    if safe_headers:
        metadata['headers'] = safe_headers
    
    # Create message
    if error:
        message = f"API Request Error: {method} {url}"
        log(message, level=level, component="api_request", exc_info=error, metadata=metadata)
    else:
        message = f"API Request: {method} {url} {status_code}"
        log(message, level=level, component="api_request", metadata=metadata)

def auto_log_errors(source: Optional[str] = None, component: Optional[str] = None):
    """
    A function and class decorator that automatically logs exceptions.
    
    Can be used on:
    - Regular functions
    - DRF APIView classes
    - DRF ViewSet classes
    - Django models methods
    
    Args:
        source: The source system (defaults to auto-detection)
        component: The component name (defaults to function/class name)
        
    Example:
        @auto_log_errors()
        def process_data(data):
            # Any raised exception will be logged automatically
            return transform_data(data)
    """
    def decorator(func_or_cls):
        # For class decorations (APIView, ViewSet)
        if inspect.isclass(func_or_cls):
            # For DRF APIView and ViewSet classes
            if issubclass(func_or_cls, (APIView, ViewSet)):
                # Store original dispatch method
                original_dispatch = func_or_cls.dispatch
                
                # Create a new dispatch method with error logging
                @functools.wraps(original_dispatch)
                def dispatch_wrapper(self, request, *args, **kwargs):
                    # Create component name based on class and calling method
                    method_name = request.method.lower() if hasattr(request, 'method') else 'unknown'
                    class_name = func_or_cls.__name__
                    actual_component = component or f"{class_name}.{method_name}"
                    
                    try:
                        return original_dispatch(self, request, *args, **kwargs)
                    except Exception as e:
                        # Log the error
                        log(
                            message=str(e),
                            level='ERROR',
                            source=source,
                            component=actual_component,
                            exc_info=True,
                            metadata={
                                'args': str(args),
                                'kwargs': str(kwargs),
                                'view_class': class_name,
                                'http_method': method_name
                            }
                        )
                        # Re-raise the exception
                        raise
                
                # Replace the dispatch method
                func_or_cls.dispatch = dispatch_wrapper
                return func_or_cls
            
            # For model classes
            elif issubclass(func_or_cls, models.Model):
                # Track save, delete methods
                original_save = func_or_cls.save
                original_delete = func_or_cls.delete
                
                @functools.wraps(original_save)
                def save_wrapper(self, *args, **kwargs):
                    actual_component = component or f"{func_or_cls.__name__}.save"
                    try:
                        return original_save(self, *args, **kwargs)
                    except Exception as e:
                        log(
                            message=str(e),
                            level='ERROR',
                            source=source,
                            component=actual_component,
                            exc_info=True,
                            metadata={
                                'model': func_or_cls.__name__,
                                'instance_id': getattr(self, 'id', None),
                                'args': str(args),
                                'kwargs': str(kwargs),
                            }
                        )
                        raise
                
                @functools.wraps(original_delete)
                def delete_wrapper(self, *args, **kwargs):
                    actual_component = component or f"{func_or_cls.__name__}.delete"
                    try:
                        return original_delete(self, *args, **kwargs)
                    except Exception as e:
                        log(
                            message=str(e),
                            level='ERROR',
                            source=source,
                            component=actual_component,
                            exc_info=True,
                            metadata={
                                'model': func_or_cls.__name__,
                                'instance_id': getattr(self, 'id', None),
                                'args': str(args),
                                'kwargs': str(kwargs),
                            }
                        )
                        raise
                
                func_or_cls.save = save_wrapper
                func_or_cls.delete = delete_wrapper
                return func_or_cls
            
            # For regular classes
            else:
                # Wrap each method in the class
                for name, method in inspect.getmembers(func_or_cls, predicate=inspect.isfunction):
                    # Skip private methods
                    if name.startswith('_'):
                        continue
                    
                    wrapped = _wrap_function(
                        method, 
                        source, 
                        component or f"{func_or_cls.__name__}.{name}"
                    )
                    setattr(func_or_cls, name, wrapped)
                return func_or_cls
        
        # For function decorations
        else:
            return _wrap_function(
                func_or_cls, 
                source, 
                component or func_or_cls.__name__
            )
    
    def _wrap_function(func, src, comp):
        """Wrap a function with error logging"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get function metadata
                func_metadata = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
                
                # Log the error
                log(
                    message=str(e),
                    level='ERROR',
                    source=src,
                    component=comp,
                    exc_info=True,
                    metadata=func_metadata
                )
                
                # Re-raise the exception
                raise
        return wrapper
    
    return decorator

# HTTP request monitoring tools
class RequestsMonitor:
    """
    Monitor and log requests made with the 'requests' library.
    
    This module will patch the requests library to automatically log all requests.
    
    Usage:
        # At the start of your app, call:
        RequestsMonitor.patch()
        
        # Then all requests calls will be automatically logged
    """
    
    @staticmethod
    def patch():
        """Patch the requests library to log all requests."""
        try:
            import requests
            from requests import Session
            
            # Store original methods
            original_request = Session.request
            
            # Create wrapped method
            @functools.wraps(original_request)
            def request_wrapper(self, method, url, **kwargs):
                start_time = datetime.now()
                error = None
                response = None
                
                try:
                    response = original_request(self, method, url, **kwargs)
                    return response
                except Exception as e:
                    error = e
                    raise
                finally:
                    # Calculate duration
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Extract request data
                    req_data = None
                    if 'data' in kwargs:
                        req_data = kwargs['data']
                    elif 'json' in kwargs:
                        req_data = kwargs['json']
                    
                    # Extract response data if available
                    resp_data = None
                    status_code = None
                    if response is not None:
                        status_code = response.status_code
                        try:
                            if 'application/json' in response.headers.get('Content-Type', ''):
                                resp_data = response.json()
                            else:
                                # Limit text response to avoid huge logs
                                resp_text = response.text[:1000]
                                if len(response.text) > 1000:
                                    resp_text += "... [truncated]"
                                resp_data = resp_text
                        except:
                            pass
                    
                    # Log the request
                    log_request(
                        url=url,
                        method=method,
                        status_code=status_code,
                        request_data=req_data,
                        response_data=resp_data,
                        headers=kwargs.get('headers'),
                        duration_ms=duration,
                        error=error
                    )
            
            # Apply the patch
            Session.request = request_wrapper
            return True
        
        except ImportError:
            # requests library not available
            return False
        except Exception:
            # Something went wrong with patching
            return False

# For backward compatibility
log_sp_error = log
log_sb_error = log 
log_sd_error = log
log_sqp_error = log
log_listener_error = log
log_system_error = log 