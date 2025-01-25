from django.urls import path, include
from az_app.backend.core import settings
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, process_spads

router = DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('process_spads/', process_spads, name='process_spads'),
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
