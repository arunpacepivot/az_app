from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    
    def ready(self):
        # Import signals handlers when app is ready
        # Use try/except to prevent issues during app initialization
        try:
            import authentication.signals
        except ImportError:
            pass