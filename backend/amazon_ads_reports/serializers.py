from rest_framework import serializers
from .models import (
    Tenant, AmazonAdsCredential, ReportType, AdsReport, 
    DailyProductAdsData, SearchTermReportData, ReportSchedule
)

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'identifier', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class AmazonAdsCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmazonAdsCredential
        fields = [
            'id', 'tenant', 'client_id', 'client_secret', 'refresh_token', 
            'profile_id', 'region', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'client_secret': {'write_only': True},
            'refresh_token': {'write_only': True},
        }

class ReportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportType
        fields = [
            'id', 'name', 'slug', 'description', 'api_report_type',
            'ad_product', 'metrics', 'time_unit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AdsReportSerializer(serializers.ModelSerializer):
    tenant_name = serializers.SerializerMethodField()
    report_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AdsReport
        fields = [
            'id', 'tenant', 'tenant_name', 'report_type', 'report_type_name',
            'amazon_report_id', 'start_date', 'end_date', 'selected_metrics',
            'group_by', 'status', 'download_url', 'error_message', 'is_stored',
            'rows_processed', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'amazon_report_id', 'status', 'download_url', 'error_message',
            'is_stored', 'rows_processed', 'created_at', 'updated_at', 'completed_at'
        ]
    
    def get_tenant_name(self, obj):
        return obj.tenant.name if obj.tenant else None
    
    def get_report_type_name(self, obj):
        return obj.report_type.name if obj.report_type else None

class DailyProductAdsDataSerializer(serializers.ModelSerializer):
    tenant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyProductAdsData
        fields = [
            'id', 'tenant', 'tenant_name', 'report', 'date', 'portfolio_id',
            'campaign_name', 'campaign_id', 'ad_group_name', 'ad_group_id',
            'ad_id', 'campaign_budget_type', 'campaign_budget_amount',
            'campaign_budget_currency_code', 'campaign_status',
            'advertised_asin', 'advertised_sku', 'impressions', 'clicks',
            'click_through_rate', 'cost', 'cost_per_click', 'spend',
            'units_sold_clicks_30d', 'units_sold_same_sku_30d',
            'sales_1d', 'sales_7d', 'sales_14d', 'sales_30d',
            'attributed_sales_same_sku_30d', 'purchases_1d', 'purchases_7d',
            'purchases_14d', 'purchases_30d', 'purchases_same_sku_30d',
            'units_sold_other_sku_7d', 'sales_other_sku_7d',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_tenant_name(self, obj):
        return obj.tenant.name if obj.tenant else None

class SearchTermReportDataSerializer(serializers.ModelSerializer):
    tenant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SearchTermReportData
        fields = [
            'id', 'tenant', 'tenant_name', 'report', 'date', 'campaign_name',
            'campaign_id', 'ad_group_name', 'ad_group_id', 'keyword_text',
            'match_type', 'query', 'impressions', 'clicks', 'click_through_rate',
            'cost', 'cost_per_click', 'conversions', 'conversion_rate',
            'sales_7d', 'sales_14d', 'sales_30d', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_tenant_name(self, obj):
        return obj.tenant.name if obj.tenant else None

class ReportScheduleSerializer(serializers.ModelSerializer):
    tenant_name = serializers.SerializerMethodField()
    report_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'tenant', 'tenant_name', 'report_type', 'report_type_name',
            'name', 'frequency', 'hour', 'minute', 'day_of_week', 'day_of_month',
            'lookback_days', 'selected_metrics', 'group_by', 'is_active',
            'last_run', 'next_run', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_run', 'next_run', 'created_at', 'updated_at']
    
    def get_tenant_name(self, obj):
        return obj.tenant.name if obj.tenant else None
    
    def get_report_type_name(self, obj):
        return obj.report_type.name if obj.report_type else None

class ReportRequestSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    report_type_id = serializers.UUIDField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    group_by = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    
    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data

class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data 