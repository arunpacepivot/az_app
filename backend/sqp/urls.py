from django.urls import path
from .views import process_sqp

urlpatterns = [
    path('process_sqp/', process_sqp, name='process_sqp'),
] 