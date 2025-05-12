from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom User admin configuration
    """
    list_display = ('email', 'username', 'first_name', 'last_name', 'firebase_uid', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'firebase_uid')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Firebase Info'), {'fields': ('firebase_uid',)}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'firebase_uid', 'first_name', 'last_name',
                        'is_staff', 'is_active')}
        ),
    )
    
    readonly_fields = ('created_at', 'updated_at')
