"""
URL patterns for Amazon Seller OAuth flow
"""
from django.urls import path
from . import views

app_name = 'amazon_seller'

urlpatterns = [
    # Seller API OAuth routes
    path('auth/init', views.AmazonAuthView.as_view(), name='auth_init'),
    path('auth/callback', views.AmazonCallbackView.as_view(), name='auth_callback'),
    
    # Advertising API OAuth routes
    path('advertising/auth/init', views.AmazonAdvertisingAuthView.as_view(), name='adv_auth_init'),
    path('advertising/auth/callback', views.AmazonAdvertisingCallbackView.as_view(), name='adv_auth_callback'),
] 