"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# Ensure the correct settings module is set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    application = get_wsgi_application()
except Exception as e:
    print(f"WSGI Application Error: {e}")
    raise
