from django.shortcuts import render
# Import pyrebase4 instead of pyrebase
try:
    import pyrebase
except ImportError:
    try:
        import pyrebase4 as pyrebase
    except ImportError:
        raise ImportError("Please install pyrebase4: pip install pyrebase4")

import os
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import RetrieveUpdateAPIView
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, 
    AuthResponseSerializer, 
    FirebaseAuthRequestSerializer,
    SignUpSerializer,
    SignInSerializer
)
from .firebase_service import FirebaseService

# Get the User model
User = get_user_model()

# Initialize pyrebase for client-side auth operations that Firebase Admin SDK doesn't support
FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.environ.get("FIREBASE_APP_ID"),
    "databaseURL": os.environ.get("FIREBASE_DATABASE_URL", ""),
}

# Only initialize Firebase if API key is available
firebase = None
firebase_auth = None
if FIREBASE_CONFIG["apiKey"]:
    try:
        firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
        firebase_auth = firebase.auth()
    except Exception as e:
        print(f"WARNING: Could not initialize Firebase client: {str(e)}")

class SignUpView(APIView):
    """
    API view for user signup with Firebase
    Registers user in both Firebase Auth and Django's PostgreSQL database
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            first_name = serializer.validated_data.get('first_name', '')
            last_name = serializer.validated_data.get('last_name', '')
            
            display_name = first_name
            if first_name and last_name:
                display_name = f"{first_name} {last_name}"
            
            if not firebase_auth:
                return Response(
                    {"error": "Firebase is not configured properly"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            try:
                # First, create user in Firebase
                firebase_user = FirebaseService.create_user(
                    email=email,
                    password=password,
                    display_name=display_name if display_name else None
                )
                
                # Sign in to get tokens
                auth_data = firebase_auth.sign_in_with_email_and_password(email, password)
                
                # Format auth response
                auth_response = {
                    'token': auth_data.get('idToken'),
                    'refresh_token': auth_data.get('refreshToken'),
                    'expires_in': int(auth_data.get('expiresIn', 3600)),
                }
                
                # Create or get user in Django PostgreSQL
                username = email.split('@')[0]
                # Ensure username is unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create Django user in PostgreSQL
                user, created = User.objects.get_or_create(
                    firebase_uid=firebase_user.uid,
                    defaults={
                        'email': email,
                        'username': username,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': True
                    }
                )
                
                # Add user data to response
                auth_response['user'] = UserSerializer(user).data
                
                # Send verification email
                try:
                    verification_link = FirebaseService.generate_email_verification_link(email)
                    # Here you can send the verification_link via your own email service if needed
                except Exception as e:
                    # Don't fail signup if verification email fails
                    print(f"Failed to send verification email: {str(e)}")
                
                # Serialize and return response
                response_serializer = AuthResponseSerializer(auth_response)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignInView(APIView):
    """
    API view for user signin with Firebase
    Ensures user exists in Django's PostgreSQL database
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            if not firebase_auth:
                return Response(
                    {"error": "Firebase is not configured properly"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            try:
                # Sign in with Firebase
                auth_data = firebase_auth.sign_in_with_email_and_password(email, password)
                
                # Verify the token to get user data
                decoded_token = FirebaseService.verify_token(auth_data.get('idToken'))
                uid = decoded_token.get('uid')
                
                # Get or create user in Django PostgreSQL
                try:
                    user = User.objects.get(firebase_uid=uid)
                except User.DoesNotExist:
                    # If user doesn't exist in Django but exists in Firebase,
                    # create the user in PostgreSQL
                    username = email.split('@')[0]
                    # Ensure username is unique
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    name = decoded_token.get('name', '')
                    first_name = ''
                    last_name = ''
                    if name:
                        name_parts = name.split(' ', 1)
                        first_name = name_parts[0]
                        last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    user = User.objects.create(
                        firebase_uid=uid,
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True
                    )
                
                # Format auth response
                auth_response = {
                    'token': auth_data.get('idToken'),
                    'refresh_token': auth_data.get('refreshToken'),
                    'expires_in': int(auth_data.get('expiresIn', 3600)),
                    'user': UserSerializer(user).data
                }
                
                # Serialize and return response
                response_serializer = AuthResponseSerializer(auth_response)
                return Response(response_serializer.data)
                
            except Exception as e:
                error_message = str(e)
                # Handle pyrebase errors which are returned as JSON strings
                if isinstance(e, Exception) and hasattr(e, 'args') and len(e.args) > 0:
                    arg = e.args[0]
                    if isinstance(arg, str) and arg.startswith('{'):
                        try:
                            error_data = json.loads(arg)
                            if 'error' in error_data:
                                error_message = error_data['error'].get('message', str(e))
                        except json.JSONDecodeError:
                            pass
                            
                return Response(
                    {"error": error_message},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyTokenView(APIView):
    """
    API view for verifying Firebase tokens
    Ensures user exists in Django's PostgreSQL database
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = FirebaseAuthRequestSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                # Verify the token
                decoded_token = FirebaseService.verify_token(token)
                uid = decoded_token.get('uid')
                
                # Get or create user in Django PostgreSQL
                try:
                    user = User.objects.get(firebase_uid=uid)
                except User.DoesNotExist:
                    # If the token is valid but the user doesn't exist in Django,
                    # create the user in PostgreSQL
                    email = decoded_token.get('email', f"{uid}@firebaseuser.com")
                    username = email.split('@')[0]
                    
                    # Ensure username is unique
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    name = decoded_token.get('name', '')
                    first_name = ''
                    last_name = ''
                    if name:
                        name_parts = name.split(' ', 1)
                        first_name = name_parts[0]
                        last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    user = User.objects.create(
                        firebase_uid=uid,
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True
                    )
                
                # Return user data
                return Response(UserSerializer(user).data)
                
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(RetrieveUpdateAPIView):
    """
    API view for retrieving and updating user profile in PostgreSQL
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def perform_update(self, serializer):
        # Save changes to PostgreSQL
        user = serializer.save()
        
        # Sync changes to Firebase if needed
        if user.firebase_uid and (serializer.validated_data.get('first_name') or 
                                 serializer.validated_data.get('last_name') or
                                 serializer.validated_data.get('email')):
            try:
                properties = {}
                
                # Update display name if first or last name changed
                if 'first_name' in serializer.validated_data or 'last_name' in serializer.validated_data:
                    display_name = user.first_name
                    if user.first_name and user.last_name:
                        display_name = f"{user.first_name} {user.last_name}"
                    properties['display_name'] = display_name
                
                # Update email if changed
                if 'email' in serializer.validated_data:
                    properties['email'] = user.email
                
                # Only update Firebase if we have properties to update
                if properties:
                    FirebaseService.update_user(user.firebase_uid, properties)
            except Exception as e:
                print(f"Failed to sync user updates to Firebase: {str(e)}")

class PasswordResetView(APIView):
    """
    API view for sending password reset link via Firebase
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Generate password reset link
            reset_link = FirebaseService.generate_password_reset_link(email)
            
            # Here you can choose to send the reset_link via your own email service
            # instead of relying on Firebase's email service
            
            return Response({"message": "Password reset link sent"})
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
