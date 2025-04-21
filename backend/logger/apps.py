from django.apps import AppConfig


class LoggerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logger'
    verbose_name = 'Error Logging System'
