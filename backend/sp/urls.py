from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProcessedFileViewSet, process_spads, get_csrf, all_optimisations

router = DefaultRouter()
router.register(r'processed-files', ProcessedFileViewSet, basename='processed-file')

urlpatterns = [
    path('process_spads/', process_spads, name='process_spads'),
    path('get_csrf/', get_csrf, name='get_csrf'),
    path('all_optimisations/', all_optimisations, name='all_optimisations'),
    path('', include(router.urls)),
]
