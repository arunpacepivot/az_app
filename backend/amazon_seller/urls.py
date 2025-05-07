"""
URL patterns for Amazon Seller and Advertising APIs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'amazon_seller'

router = DefaultRouter()
router.register(r'report-schedules', views.ReportScheduleAPIView, basename='report-schedule')
router.register(r'reports', views.ReportAPIView, basename='report')

urlpatterns = [
    # Seller API OAuth routes
    path('auth/init', views.AmazonAuthView.as_view(), name='auth_init'),
    path('auth/callback', views.AmazonCallbackView.as_view(), name='auth_callback'),
    
    # Advertising API OAuth routes
    path('advertising/auth/init', views.AmazonAdvertisingAuthView.as_view(), name='adv_auth_init'),
    path('advertising/auth/callback', views.AmazonAdvertisingCallbackView.as_view(), name='adv_auth_callback'),
    
    # Advertising API endpoints (authenticated)
    path('advertising/profiles', views.AdvertisingProfilesAPIView.as_view(), name='adv_profiles'),
    path('advertising/campaigns/<str:profile_id>', views.AdvertisingCampaignsAPIView.as_view(), name='adv_campaigns'),
    path('advertising/ad-groups/<str:profile_id>', views.AdvertisingAdGroupsAPIView.as_view(), name='adv_ad_groups'),
    path('advertising/reports/<str:profile_id>', views.AdvertisingReportsAPIView.as_view(), name='adv_reports'),
    
    # Include router URLs
    path('', include(router.urls)),
] 