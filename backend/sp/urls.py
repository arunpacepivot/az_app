from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, process_spads

router = DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('process_spads/', process_spads, name='process_spads'),
    path('', include(router.urls)),
]
