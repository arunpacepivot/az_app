from django.db.models import QuerySet
from .models import User

def get_active_users() -> QuerySet[User]:
    return User.objects.filter(is_active=True)

def get_user_by_email(email: str) -> User:
    return User.objects.get(email=email) 