from django.db import transaction
from .models import User, Profile

class UserService:
    @staticmethod
    @transaction.atomic
    def create_user(email: str, password: str, **extra_fields) -> User:
        user = User.objects.create_user(
            email=email,
            username=email,
            password=password,
            **extra_fields
        )
        Profile.objects.create(user=user)
        return user

    @staticmethod
    def update_user(user: User, **fields) -> User:
        for field, value in fields.items():
            setattr(user, field, value)
        user.save()
        return user 