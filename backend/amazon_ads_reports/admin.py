from django.contrib import admin
from .models import (
    Tenant, AmazonAdsCredential, ReportType, AdsReport, 
    DailyProductAdsData, SearchTermReportData, ReportSchedule
)

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'identifier', 'is_active', 'created_at')
    search_fields = ('name', 'identifier')
    list_filter = ('is_active',)
    ordering = ('name',)

@admin.register(AmazonAdsCredential)
class AmazonAdsCredentialAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'profile_id', 'region', 'is_active', 'token_expires_at')
    search_fields = ('profile_id', 'tenant__name')
    list_filter = ('is_active', 'region')
    ordering = ('tenant__name',)
    readonly_fields = ('access_token', 'token_expires_at', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant')

@admin.register(ReportType)
class ReportTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'api_report_type', 'ad_product', 'time_unit')
    search_fields = ('name', 'slug', 'api_report_type')
    list_filter = ('ad_product', 'time_unit')
    ordering = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(AdsReport)
class AdsReportAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'report_type', 'start_date', 'end_date', 'status', 'is_stored', 'rows_processed', 'created_at')
    search_fields = ('tenant__name', 'amazon_report_id')
    list_filter = ('status', 'is_stored', 'start_date', 'end_date')
    readonly_fields = ('amazon_report_id', 'download_url', 'completed_at', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant', 'report_type')

@admin.register(DailyProductAdsData)
class DailyProductAdsDataAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'date', 'campaign_name', 'advertised_asin', 'advertised_sku', 'impressions', 'clicks', 'spend', 'sales_7d')
    search_fields = ('campaign_name', 'advertised_asin', 'advertised_sku')
    list_filter = ('date', 'tenant')
    date_hierarchy = 'date'
    ordering = ('-date',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant', 'report')
    
    def has_add_permission(self, request):
        return False  # Read-only model

@admin.register(SearchTermReportData)
class SearchTermReportDataAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'date', 'campaign_name', 'query', 'impressions', 'clicks', 'cost', 'sales_7d')
    search_fields = ('campaign_name', 'query')
    list_filter = ('date', 'tenant')
    date_hierarchy = 'date'
    ordering = ('-date',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant', 'report')
    
    def has_add_permission(self, request):
        return False  # Read-only model

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'report_type', 'frequency', 'is_active', 'last_run', 'next_run')
    search_fields = ('name', 'tenant__name')
    list_filter = ('frequency', 'is_active')
    readonly_fields = ('last_run', 'next_run', 'created_at', 'updated_at')
    ordering = ('next_run',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant', 'report_type', 'created_by')
