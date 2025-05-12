from django.contrib import admin
from .models import AmazonSellerAccount, AmazonAdvertisingAccount, AdvertisingReport, ReportSchedule

@admin.register(AmazonSellerAccount)
class AmazonSellerAccountAdmin(admin.ModelAdmin):
    list_display = ('seller_id', 'region', 'is_active', 'token_expires_at', 'last_refreshed_at')
    list_filter = ('region', 'is_active')
    search_fields = ('seller_id', 'marketplace_id')
    readonly_fields = ('created_at', 'updated_at', 'last_refreshed_at')
    fieldsets = (
        (None, {
            'fields': ('seller_id', 'marketplace_id', 'region', 'is_active', 'user')
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

@admin.register(AmazonAdvertisingAccount)
class AmazonAdvertisingAccountAdmin(admin.ModelAdmin):
    """Admin configuration for AmazonAdvertisingAccount model"""
    list_display = ('profile_id', 'region', 'is_active', 'token_expires_at', 'last_refreshed_at')
    list_filter = ('region', 'is_active')
    search_fields = ('profile_id', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'last_refreshed_at')
    fieldsets = (
        (None, {
            'fields': ('profile_id', 'region', 'is_active', 'user', 'seller_account')
        }),
        ('Authentication', {
            'fields': ('access_token', 'refresh_token', 'token_type', 'token_expires_at', 'scopes'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_refreshed_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(AdvertisingReport)
class AdvertisingReportAdmin(admin.ModelAdmin):
    """Admin configuration for AdvertisingReport model"""
    list_display = ('report_id', 'report_type', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'report_type', 'created_at')
    search_fields = ('report_id', 'advertising_account__profile_id', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    fieldsets = (
        (None, {
            'fields': ('report_id', 'report_type', 'status', 'advertising_account', 'user')
        }),
        ('Parameters', {
            'fields': ('metrics', 'start_date', 'end_date', 'segment'),
        }),
        ('Data', {
            'fields': ('download_url', 'report_data'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    """Admin configuration for ReportSchedule model"""
    list_display = ('name', 'frequency', 'report_type', 'next_run', 'last_run', 'is_active')
    list_filter = ('frequency', 'is_active', 'report_type')
    search_fields = ('name', 'advertising_account__profile_id', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'last_run', 'next_run')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active', 'advertising_account', 'user')
        }),
        ('Report Parameters', {
            'fields': ('report_type', 'metrics', 'segment', 'date_range', 'custom_start_date', 'custom_end_date'),
        }),
        ('Schedule', {
            'fields': ('frequency', 'day_of_week', 'day_of_month', 'hour', 'minute'),
        }),
        ('Status', {
            'fields': ('last_run', 'next_run'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
