from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProcessedFileViewSet, process_sbads, get_csrf

router = DefaultRouter()
router.register(r'processed-files', ProcessedFileViewSet, basename='processed-file')

urlpatterns = [
    path('process_sbads/', process_sbads, name='process_sbads'),
    path('get_csrf/', get_csrf, name='get_csrf'),
    path('', include(router.urls)),
] 
