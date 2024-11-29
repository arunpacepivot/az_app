from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import User
from apps.api.v1.serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] 