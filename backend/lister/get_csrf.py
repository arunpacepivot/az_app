from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import path


@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'csrfToken': request.csrf_token})  

urlpatterns = [
    path('get_csrf/', get_csrf_token, name='get_csrf'),
]