from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema # type: ignore
from apps.users.models import User
from apps.users.services import UserService
from .serializers import UserSerializer
from utils.permissions import IsOwnerOrReadOnly

@extend_schema(tags=['Users'])
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user accounts.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filterset_fields = ['email', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'email']

    @extend_schema(
        summary="Create new user",
        description="Create a new user account with the provided information.",
        request=UserCreateSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Valid Request',
                value={
                    'email': 'user@example.com',
                    'password': 'securepass123',
                    'first_name': 'John',
                    'last_name': 'Doe'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Success Response',
                value={
                    'id': 1,
                    'email': 'user@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'profile': {
                        'id': 1,
                        'bio': '',
                        'avatar': None,
                        'birth_date': None
                    }
                },
                response_only=True,
            ),
        ]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Get current user",
        description="Retrieve the profile of the currently authenticated user.",
        responses={200: UserSerializer},
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    'id': 1,
                    'email': 'user@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'profile': {
                        'id': 1,
                        'bio': 'Software Developer',
                        'avatar': 'http://example.com/avatar.jpg',
                        'birth_date': '1990-01-01'
                    }
                }
            )
        ]
    )
    @action(detail=False, methods=['GET'])
    def me(self, request):
        """Get the current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='email',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filter by email address'
            ),
            OpenApiParameter(
                name='is_active',
                type=bool,
                location=OpenApiParameter.QUERY,
                description='Filter by active status'
            ),
            OpenApiParameter(
                name='search',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Search in email, first_name, and last_name'
            ),
            OpenApiParameter(
                name='ordering',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Order by field (prefix with - for descending)'
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        List users with optional filtering and ordering.
        """
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        try:
            UserService.create_user(**serializer.validated_data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )