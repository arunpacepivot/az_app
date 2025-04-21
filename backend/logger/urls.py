from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'logs', views.ErrorLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', views.error_log_stats, name='error-log-stats'),
] 