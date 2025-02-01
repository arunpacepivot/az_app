# Add CORS configuration
CORS_ALLOWED_ORIGINS = [
    "https://next-frontend-app-a2h4eca5bbe4ekfj.centralindia-01.azurewebsites.net",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Add 'corsheaders' to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps ...
    "corsheaders",
    # ... other apps ...
]

# Add CorsMiddleware as high as possible in the middleware list
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    # ... other middleware ...
] 