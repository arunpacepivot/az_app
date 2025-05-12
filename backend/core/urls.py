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
from lister.views import get_csrf  # Import the CSRF view directly
from sp.views import get_csrf, optimize_all  # Import the CSRF view and optimize_all view
from .file_views import download_file, file_info, remove_file  # Import file API views

# Root view
def api_root(request):
    return JsonResponse({
        "message": "Welcome to the API",
        "version": "1.0",
        "endpoints": {
            "health_check": "/api/v1/health/",
            "lister": "api/v1/lister/",
            "csrf": "/get_csrf/",
            "sp": "/api/v1/sp/",
            "sb": "/api/v1/sb/",
            "sd": "/api/v1/sd/",
            "cerebro": "/api/v1/cerebro/",
            "sqp": "/api/v1/sqp/",
            "ngram": "/api/v1/ngram/",
            "topical": "/api/v1/topical/",
            "files": "/api/v1/files/",
            "optimize_all": "/api/v1/optimize/all/",
            "logger": "/api/v1/logger/",
            "amazon_seller": "/api/v1/amazon/",
            "amazon_ads_reports": "/api/v1/amazon-ads/",
            "amazon_auth": "/api/v1/amazon-auth/",
            "auth": "/api/v1/auth/"  # Add authentication endpoint
        }
    })

# File API patterns
file_api_patterns = [
    path('download/<str:file_id>/', download_file, name='download_file'),
    path('info/<str:file_id>/', file_info, name='file_info'),
    path('delete/<str:file_id>/', remove_file, name='remove_file'),
]

# API Version patterns
api_v1_patterns = [
    path('health/', include('health.urls')),
    path('lister/', include('lister.urls')),
    path('sp/', include('sp.urls')),
    path('sb/', include('sb.urls')),
    path('sd/', include('sd.urls')),
    path('cerebro/', include('cerebro.urls')),
    path('sqp/', include('sqp.urls')),
    path('ngram/', include('ngram.urls')),
    path('topical/', include('topical.urls')),
    path('files/', include((file_api_patterns, 'files'))),
    path('optimize/all/', optimize_all, name='optimize_all'),
    path('logger/', include('logger.urls')),
    path('amazon/', include('amazon_seller.urls')),
    path('amazon-ads/', include('amazon_ads_reports.urls')),
    path('amazon-auth/', include('amazon_auth.urls')),
    path('auth/', include('authentication.urls')),  # Add authentication URLs
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include((api_v1_patterns, 'v1'), namespace='v1')),
    path('', api_root),
    path('get_csrf/', get_csrf, name='get_csrf'),  # Add the CSRF view directly here
]
           
