import traceback
import threading
import json
import logging
import sys
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional, Callable, Type

from django.conf import settings
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# We'll use Django's default logger for fallback
django_logger = logging.getLogger('django')

# Import the model within functions to avoid circular imports
def get_error_log_model():
    from .models import ErrorLog
    return ErrorLog

class AsyncErrorLogger:
    """
    Asynchronous error logging service that stores errors in the database.
    
    This service provides both synchronous and asynchronous methods for logging errors,
    with the async version utilizing threading to avoid blocking the main execution.
    """
    
    @classmethod
    def log_error(cls, 
                message: str, 
                level: str = 'ERROR', 
                source: str = 'SYSTEM', 
                component: str = 'unknown', 
                exc_info=None, 
                metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error synchronously to the database.
        
        Args:
            message: The error message
            level: Error level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            source: Source component (SP, SB, SD, SQP, LISTENER, SYSTEM, OTHER)
            component: Specific component or function name
            exc_info: Exception info (sys.exc_info() or exception instance)
            metadata: Additional contextual data
        """
        try:
            ErrorLog = get_error_log_model()
            
            # Handle exception info
            tb_string = ""
            if exc_info:
                if isinstance(exc_info, tuple) and len(exc_info) == 3:
                    # If sys.exc_info() was passed
                    _, _, tb = exc_info
                    tb_string = ''.join(traceback.format_tb(tb))
                elif isinstance(exc_info, Exception):
                    # If an exception instance was passed
                    tb_string = traceback.format_exc()
                elif exc_info is True:
                    # If True was passed, get current exception info
                    tb_string = traceback.format_exc()
            
            # Create and save the error log
            with transaction.atomic():
                error_log = ErrorLog(
                    level=level,
                    source=source,
                    component=component,
                    message=message,
                    traceback=tb_string,
                    metadata=metadata or {}
                )
                error_log.save()
                
            # Also log to console in development mode
            if settings.DEBUG:
                django_logger.error(f"{level} - {source} - {component}: {message}")
                
            return error_log
        except Exception as e:
            # Fallback to Django logger if database logging fails
            django_logger.error(f"Failed to log error to database: {str(e)}")
            django_logger.error(f"Original error: {message}")
            return None
    
    @classmethod
    def log_error_async(cls, *args, **kwargs) -> None:
        """
        Log an error asynchronously using a separate thread.
        
        Takes the same arguments as log_error.
        """
        thread = threading.Thread(target=cls.log_error, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
    
    @classmethod
    def exception_handler(cls, source: str = 'SYSTEM', component: str = 'unknown'):
        """
        Decorator to catch and log exceptions in a function.
        
        Args:
            source: Source component (SP, SB, SD, SQP, LISTENER, SYSTEM, OTHER)
            component: Specific component or function name
            
        Example:
            @AsyncErrorLogger.exception_handler(source='SP', component='process_spads')
            def my_function():
                # Do something that might raise an exception
                pass
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Get function metadata
                    func_metadata = {
                        'function': func.__name__,
                        'args': str(args),
                        'kwargs': str(kwargs)
                    }
                    
                    # Log the error asynchronously
                    cls.log_error_async(
                        message=str(e),
                        level='ERROR',
                        source=source,
                        component=component,
                        exc_info=True,
                        metadata=func_metadata
                    )
                    
                    # Re-raise the exception
                    raise
            return wrapper
        return decorator 