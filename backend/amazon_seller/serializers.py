from rest_framework import serializers
from .models import (
    AmazonSellerAccount,
    AmazonAdvertisingAccount,
    ReportSchedule,
    AdvertisingReport
)

class ReportScheduleSerializer(serializers.ModelSerializer):
    """Serializer for report schedules"""
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'name', 'report_type', 'metrics', 'date_range',
            'custom_start_date', 'custom_end_date', 'segment',
            'frequency', 'next_run', 'last_run', 'is_active',
            'advertising_account', 'user', 'created_at', 'updated_at'
        ]
        read_only_fields = ['next_run', 'last_run', 'user', 'created_at', 'updated_at']

class ReportScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating report schedules"""
    class Meta:
        model = ReportSchedule
        fields = [
            'name', 'report_type', 'metrics', 'date_range',
            'custom_start_date', 'custom_end_date', 'segment',
            'frequency', 'is_active', 'advertising_account'
        ]

class AdvertisingReportSerializer(serializers.ModelSerializer):
    """Serializer for advertising reports"""
    class Meta:
        model = AdvertisingReport
        fields = [
            'id', 'report_id', 'report_type', 'status',
            'metrics', 'start_date', 'end_date', 'segment',
            'advertising_account', 'user', 'created_at',
            'completed_at', 'report_data'
        ]
        read_only_fields = [
            'report_id', 'status', 'user', 'created_at',
            'completed_at', 'report_data'
        ] 