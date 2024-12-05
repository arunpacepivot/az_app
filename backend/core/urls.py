"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.http import JsonResponse
from django.contrib import admin

# Root view
def api_root(request):
    return JsonResponse({
        "message": "Welcome to the API",
        "version": "1.0",
        "endpoints": {
            "health_check": "/api/v1/health/"
        }
    })

# API Version patterns
api_v1_patterns = [
    path('health/', include('health.urls')),
    # Add other app URLs here
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include((api_v1_patterns, 'v1'), namespace='v1')),
    path('', api_root),  # Add root endpoint
]
