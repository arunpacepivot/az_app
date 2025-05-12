from django.urls import path
from .views import (
    SignUpView,
    SignInView,
    VerifyTokenView,
    UserProfileView,
    PasswordResetView
)

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('verify-token/', VerifyTokenView.as_view(), name='verify_token'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
] 