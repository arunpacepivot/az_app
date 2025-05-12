from rest_framework import serializers
from django.contrib.auth import get_user_model

# Get the User model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data
    """
    class Meta:
        model = User
        fields = ['id', 'firebase_uid', 'email', 'username', 'first_name', 'last_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'firebase_uid', 'created_at', 'updated_at']

class AuthResponseSerializer(serializers.Serializer):
    """
    Serializer for authentication responses
    """
    token = serializers.CharField(max_length=2048)
    refresh_token = serializers.CharField(max_length=2048)
    user = UserSerializer(read_only=True)
    expires_in = serializers.IntegerField()

class FirebaseAuthRequestSerializer(serializers.Serializer):
    """
    Serializer for Firebase authentication requests
    """
    token = serializers.CharField(max_length=2048)
    
class SignUpSerializer(serializers.Serializer):
    """
    Serializer for sign up data
    """
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)

class SignInSerializer(serializers.Serializer):
    """
    Serializer for sign in data
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True) 