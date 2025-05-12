from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions
from firebase_admin import auth
from django.contrib.auth import get_user_model

class NoAuthToken(exceptions.AuthenticationFailed):
    pass

class InvalidAuthToken(exceptions.AuthenticationFailed):
    pass

class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Firebase Authentication for Django REST Framework
    Verifies Firebase tokens and syncs with Django's user model in PostgreSQL
    """
    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            raise NoAuthToken("No auth token provided")

        # Extract token from header (format: "Bearer <token>")
        token = auth_header.split(" ")
        if len(token) != 2 or token[0].lower() != "bearer":
            raise InvalidAuthToken("Invalid token format")
            
        id_token = token[1]
        
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            
            # Get the UID from the token
            uid = decoded_token.get("uid")
            
            if not uid:
                raise InvalidAuthToken("Invalid token - missing UID")
                
            # Get user info from decoded token
            name = decoded_token.get("name", "")
            email = decoded_token.get("email", "")
            picture = decoded_token.get("picture", "")
            
            # Get User model using get_user_model to avoid circular imports
            User = get_user_model()
            
            # Get or create user in PostgreSQL
            try:
                user = User.objects.get(firebase_uid=uid)
                
                # Update user information if it has changed
                user_updated = False
                
                if email and user.email != email:
                    user.email = email
                    user_updated = True
                    
                if name and user.first_name != name:
                    # Split name into first and last
                    name_parts = name.split(' ', 1)
                    user.first_name = name_parts[0]
                    if len(name_parts) > 1:
                        user.last_name = name_parts[1]
                    user_updated = True
                
                # Save user if any fields were updated
                if user_updated:
                    user.save()
                    
            except User.DoesNotExist:
                # Create a new user in PostgreSQL
                username = email.split('@')[0] if email else f"user_{uid[:8]}"
                # Ensure username is unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Split name into first and last
                first_name = ""
                last_name = ""
                if name:
                    name_parts = name.split(' ', 1)
                    first_name = name_parts[0]
                    if len(name_parts) > 1:
                        last_name = name_parts[1]
                
                # Create the user in PostgreSQL
                user = User.objects.create(
                    firebase_uid=uid,
                    username=username,
                    email=email if email else f"{uid}@firebaseuser.com",
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True
                )
                
            return (user, None)
            
        except auth.ExpiredIdTokenError:
            raise InvalidAuthToken("Token expired")
        except auth.InvalidIdTokenError:
            raise InvalidAuthToken("Invalid token")
        except auth.RevokedIdTokenError:
            raise InvalidAuthToken("Token revoked")
        except Exception as e:
            raise InvalidAuthToken(f"Authentication error: {str(e)}") 