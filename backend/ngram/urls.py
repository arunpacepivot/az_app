from django.urls import path
from .views import process_ngram

urlpatterns = [
    path('process_ngram/', process_ngram, name='process_ngram'),
]