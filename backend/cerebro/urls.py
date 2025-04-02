from django.urls import path
from .views import process_cerebro

urlpatterns = [
    path('process_cerebro/', process_cerebro, name='process_cerebro'),
] 