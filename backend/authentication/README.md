# Firebase Authentication with Django

This app provides authentication for the Django REST API using Firebase as the identity provider. It bridges Firebase Authentication with Django's user management system.

## Features

- Firebase-based authentication with Django REST Framework integration
- User creation and management in both Firebase and Django
- Token-based authentication (JWT) with Firebase verification
- API endpoints for signup, signin, password reset, and token verification
- Support for email/password authentication

## Setup

1. Add Firebase credentials to your `.env` file:

```
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your_app.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_bucket.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_DATABASE_URL=https://your_db.firebaseio.com
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CLIENT_CERT_URL=your_cert_url
```

2. Install required packages:

```bash
pip install firebase-admin pyrebase4
```

3. Run migrations:

```bash
python manage.py migrate
```

## API Endpoints

### Sign Up
- **URL**: `/api/v1/auth/signup/`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```
- **Response**:
  ```json
  {
    "token": "firebase_id_token",
    "refresh_token": "firebase_refresh_token",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "firebase_uid": "firebase_user_id",
      "email": "user@example.com",
      "username": "user",
      "first_name": "John",
      "last_name": "Doe",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  }
  ```

### Sign In
- **URL**: `/api/v1/auth/signin/`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123"
  }
  ```
- **Response**: Same as Sign Up

### Verify Token
- **URL**: `/api/v1/auth/verify-token/`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "token": "firebase_id_token"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "firebase_uid": "firebase_user_id",
    "email": "user@example.com",
    "username": "user",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
  ```

### User Profile
- **URL**: `/api/v1/auth/profile/`
- **Method**: GET, PUT, PATCH
- **Headers**: Authorization: Bearer {firebase_id_token}
- **Response** (GET):
  ```json
  {
    "id": 1,
    "firebase_uid": "firebase_user_id",
    "email": "user@example.com",
    "username": "user",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
  ```
- **Request** (PUT/PATCH):
  ```json
  {
    "first_name": "John",
    "last_name": "Smith"
  }
  ```

### Password Reset
- **URL**: `/api/v1/auth/password-reset/`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Password reset link sent"
  }
  ```

## Integration with Frontend

### React/Next.js Integration

Use Firebase Auth SDK on the frontend:

```javascript
import { initializeApp } from 'firebase/app';
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword,
  signOut 
} from 'firebase/auth';

// Initialize Firebase
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Sign up function
export const signUp = async (email, password) => {
  const userCredential = await createUserWithEmailAndPassword(auth, email, password);
  return userCredential.user;
};

// Sign in function
export const signIn = async (email, password) => {
  const userCredential = await signInWithEmailAndPassword(auth, email, password);
  return userCredential.user;
};

// Get current user's ID token
export const getIdToken = async () => {
  const user = auth.currentUser;
  if (user) {
    return await user.getIdToken();
  }
  return null;
};

// Sign out function
export const logOut = async () => {
  await signOut(auth);
};
```

Then make authenticated API calls:

```javascript
// Example API call with Firebase token
const fetchUserProfile = async () => {
  const token = await getIdToken();
  if (!token) return null;
  
  const response = await fetch('http://localhost:8000/api/v1/auth/profile/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (response.ok) {
    return await response.json();
  }
  return null;
};
```

## Security Considerations

1. Always transmit tokens over HTTPS
2. Keep Firebase credentials secure and out of source control
3. Set appropriate CORS headers in your Django settings
4. Consider token expiration time and implement refresh token logic 