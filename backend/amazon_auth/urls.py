"""
URL patterns for Amazon SP API authentication
"""
from django.urls import path
from . import views

app_name = 'amazon_auth'

urlpatterns = [
    # Token management endpoints
    path('tokens/', views.token_list, name='token_list'),
    path('tokens/active/', views.get_active_token, name='get_active_token'),
    path('tokens/create/', views.create_token, name='create_token'),
    path('tokens/<int:token_id>/update/', views.update_token, name='update_token'),
    path('tokens/<int:token_id>/delete/', views.delete_token, name='delete_token'),
    path('tokens/<int:token_id>/refresh/', views.refresh_token, name='refresh_token'),
    path('tokens/<int:token_id>/set-active/', views.set_active_token, name='set_active_token'),
    
    # Token retrieval for API usage
    path('access-token/', views.get_current_access_token, name='get_current_access_token'),
] 