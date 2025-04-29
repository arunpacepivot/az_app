from django.contrib import admin
from .models import AmazonSellerAccount

@admin.register(AmazonSellerAccount)
class AmazonSellerAccountAdmin(admin.ModelAdmin):
    list_display = ('seller_id', 'region', 'is_active', 'token_expires_at', 'last_refreshed_at')
    list_filter = ('region', 'is_active')
    search_fields = ('seller_id', 'marketplace_id')
    readonly_fields = ('created_at', 'updated_at', 'last_refreshed_at')
    fieldsets = (
        (None, {
            'fields': ('seller_id', 'marketplace_id', 'region', 'is_active')
        }),
        ('Authentication', {
            'fields': ('access_token', 'refresh_token', 'token_type', 'token_expires_at'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_refreshed_at'),
            'classes': ('collapse',),
        }),
    )
