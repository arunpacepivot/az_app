"""
Centralized error logging system for the application.
This module provides asynchronous error logging to database.
"""

def register_component(app_name, source_code, description=None):
    """
    Register a component as a source for error logging.
    
    This is a convenience function that can be called from any app's ready() method
    to register itself with the error logging system.
    
    Example:
        # In your app's apps.py:
        from django.apps import AppConfig
        from logger import register_component
        
        class MyAppConfig(AppConfig):
            name = 'my_app'
            
            def ready(self):
                register_component('my_app', 'MY_APP', 'My Custom Application')
    
    Args:
        app_name: The Django app name (used to match URLs and module names)
        source_code: The error source code (SP, SB, SD, etc.)
        description: Optional description of the component
    """
    from .apps import LoggerConfig
    return LoggerConfig.register_component(app_name, source_code, description)

# Export unified logging functions
from .utils import (
    log,                # Unified logging function for all purposes
    log_request,        # For logging API requests
    auto_log_errors,    # Decorator for auto-logging errors
    RequestsMonitor,    # For monitoring all requests
    
    # Keeping these for backward compatibility
    log_sp_error,
    log_sb_error,
    log_sd_error,
    log_sqp_error,
    log_listener_error,
    log_system_error,
)
