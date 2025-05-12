from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, process_asins

router = DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('process_asins/', process_asins, name='process_asins'),
    path('', include(router.urls)),
]

