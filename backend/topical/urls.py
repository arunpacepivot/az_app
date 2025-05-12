from django.urls import path
from .views import process_topical

urlpatterns = [
    path('process_topical/', process_topical, name='process_topical'),
] 