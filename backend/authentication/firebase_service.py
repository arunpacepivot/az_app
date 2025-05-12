import os
import firebase_admin
from firebase_admin import auth, credentials
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

# Initialize Firebase Admin SDK with minimal credentials
firebase_app = None
def initialize_firebase():
    global firebase_app
    # Skip initialization if DJANGO_SKIP_FIREBASE_INIT is set (for migrations)
    if os.environ.get('DJANGO_SKIP_FIREBASE_INIT'):
        print("INFO: Skipping Firebase initialization as DJANGO_SKIP_FIREBASE_INIT is set")
        return None
        
    if firebase_app is not None:
        return firebase_app
        
    try:
        # Try to get existing app first
        firebase_app = firebase_admin.get_app()
        return firebase_app
    except ValueError:
        # App doesn't exist, create it
        try:
            # Check if FIREBASE_PROJECT_ID is available (minimum required)
            project_id = os.environ.get("FIREBASE_PROJECT_ID")
            if not project_id:
                print("WARNING: FIREBASE_PROJECT_ID not configured. Token verification may not work properly.")
                return None
                
            # Minimum configuration with just project ID for token verification
            cred_dict = {
                "type": "service_account",
                "project_id": project_id,
            }
            
            # Add service account details if available
            if os.environ.get("FIREBASE_PRIVATE_KEY") and os.environ.get("FIREBASE_CLIENT_EMAIL"):
                cred_dict.update({
                    "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID", ""),
                    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
                    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL", ""),
                    "client_id": os.environ.get("FIREBASE_CLIENT_ID", ""),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_CERT_URL", "")
                })
                print("INFO: Using full Firebase service account configuration")
            else:
                # Add minimally required fields for a valid credential
                cred_dict.update({
                    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE-----END PRIVATE KEY-----\n",
                    "client_email": f"placeholder@{project_id}.iam.gserviceaccount.com",
                    "token_uri": "https://oauth2.googleapis.com/token"
                })
                print("INFO: Using minimal Firebase configuration for token verification only")
                
            # Initialize with appropriate options
            firebase_cred = credentials.Certificate(cred_dict)
            firebase_app = firebase_admin.initialize_app(firebase_cred)
            return firebase_app
        except Exception as e:
            print(f"ERROR initializing Firebase: {str(e)}")
            return None

# Try to initialize Firebase but don't fail if it doesn't work
try:
    # Skip initialization for now, will initialize on first API call
    pass
except Exception as e:
    print(f"WARNING: Could not initialize Firebase: {str(e)}")

class FirebaseService:
    """
    Service class to handle Firebase authentication operations
    """
    @staticmethod
    def verify_token(token):
        """
        Verify Firebase ID token and return decoded token
        """
        app = initialize_firebase()  # Make sure Firebase is initialized
        if not app:
            raise AuthenticationFailed("Firebase is not properly configured")
            
        try:
            return auth.verify_id_token(token)
        except Exception as e:
            raise AuthenticationFailed(f"Invalid token: {str(e)}")
    
    @staticmethod
    def create_user(email, password, display_name=None):
        """
        Create a new user in Firebase
        """
        app = initialize_firebase()  # Make sure Firebase is initialized
        if not app:
            raise AuthenticationFailed("Firebase is not properly configured for user management")
            
        try:
            user_properties = {
                'email': email,
                'password': password,
                'email_verified': False,
            }
            
            if display_name:
                user_properties['display_name'] = display_name
                
            user = auth.create_user(**user_properties)
            return user
        except Exception as e:
            raise AuthenticationFailed(f"Failed to create user: {str(e)}")
    
    @staticmethod
    def sign_in_with_email_password(email, password):
        """
        Sign in using email and password
        Note: This requires Firebase REST API as Admin SDK doesn't support this directly
        Use the frontend Firebase Auth for this functionality instead.
        """
        raise NotImplementedError("Use the frontend Firebase Auth SDK for sign-in functionality")
        
    @staticmethod
    def generate_email_verification_link(email):
        """
        Generate email verification link
        """
        app = initialize_firebase()  # Make sure Firebase is initialized
        if not app:
            raise AuthenticationFailed("Firebase is not properly configured for email operations")
            
        try:
            link = auth.generate_email_verification_link(email)
            return link
        except Exception as e:
            raise AuthenticationFailed(f"Failed to generate verification link: {str(e)}")
    
    @staticmethod
    def generate_password_reset_link(email):
        """
        Generate password reset link
        """
        app = initialize_firebase()  # Make sure Firebase is initialized
        if not app:
            raise AuthenticationFailed("Firebase is not properly configured for email operations")
            
        try:
            link = auth.generate_password_reset_link(email)
            return link
        except Exception as e:
            raise AuthenticationFailed(f"Failed to generate password reset link: {str(e)}")
    
    @staticmethod
    def update_user(uid, properties):
        """
        Update user properties in Firebase
        """
        app = initialize_firebase()  # Make sure Firebase is initialized
        if not app:
            raise AuthenticationFailed("Firebase is not properly configured for user management")
            
        try:
            return auth.update_user(uid, **properties)
        except Exception as e:
            raise AuthenticationFailed(f"Failed to update user: {str(e)}") 