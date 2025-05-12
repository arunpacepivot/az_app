from django.urls import path
from . import views

app_name = 'health'

urlpatterns = [
    path('', views.health_check, name='health_check'),
    path('connectivity-test/', views.connectivity_test, name='connectivity_test'),
] 



