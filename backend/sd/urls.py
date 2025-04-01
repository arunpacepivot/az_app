from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProcessedFileViewSet, process_sdads, get_csrf

router = DefaultRouter()
router.register(r'processed-files', ProcessedFileViewSet, basename='processed-file')

urlpatterns = [
    path('process_sdads/', process_sdads, name='process_sdads'),
    path('get_csrf/', get_csrf, name='get_csrf'),
    path('', include(router.urls)),
] 
