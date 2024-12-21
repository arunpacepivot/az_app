from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, process_asins,get_csrf

router = DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('process_asins/', process_asins, name='process_asins'),
    path('get_csrf/', get_csrf, name='get_csrf'),
    
]
