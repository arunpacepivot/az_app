from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound
from django.utils import timezone
from django.db.models import Q, Sum, F, FloatField
from django.db.models.functions import Cast
from datetime import datetime, timedelta

from .models import (
    Tenant, AmazonAdsCredential, ReportType, AdsReport, 
    DailyProductAdsData, SearchTermReportData, ReportSchedule
)
from .serializers import (
    TenantSerializer, AmazonAdsCredentialSerializer, ReportTypeSerializer,
    AdsReportSerializer, DailyProductAdsDataSerializer, SearchTermReportDataSerializer,
    ReportScheduleSerializer, ReportRequestSerializer, DateRangeSerializer
)
from .services import AmazonAdsReportService

class TenantViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tenants"""
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter tenants based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        # If tenant access permissions were to be implemented, they'd be checked here
        return self.queryset.filter(is_active=True)

class AmazonAdsCredentialViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Amazon Ads API credentials"""
    queryset = AmazonAdsCredential.objects.all()
    serializer_class = AmazonAdsCredentialSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter credentials based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        
        # Filter credentials by tenant if specified
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id, is_active=True)
        
        return self.queryset.filter(is_active=True)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test the connection to Amazon Ads API using these credentials"""
        credential = self.get_object()
        
        try:
            from .services import AmazonAdsAuth
            access_token = AmazonAdsAuth.get_access_token(credential)
            return Response({
                'success': True,
                'message': 'Successfully connected to Amazon Ads API'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to connect: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class ReportTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing report types"""
    queryset = ReportType.objects.all()
    serializer_class = ReportTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class AdsReportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ads reports"""
    queryset = AdsReport.objects.all().select_related('tenant', 'report_type')
    serializer_class = AdsReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter reports based on query parameters"""
        queryset = self.queryset
        
        # Filter by tenant
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        # Filter by report type
        report_type_id = self.request.query_params.get('report_type_id')
        if report_type_id:
            queryset = queryset.filter(report_type_id=report_type_id)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    Q(start_date__gte=start_date) & Q(end_date__lte=end_date)
                )
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def request_report(self, request):
        """Request a new report from Amazon Ads API"""
        serializer = ReportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        tenant_id = data['tenant_id']
        report_type_id = data['report_type_id']
        start_date = data['start_date']
        end_date = data['end_date']
        group_by = data.get('group_by', [])
        
        try:
            # Get required objects
            tenant = Tenant.objects.get(id=tenant_id)
            report_type = ReportType.objects.get(id=report_type_id)
            credential = AmazonAdsCredential.objects.filter(
                tenant=tenant,
                is_active=True
            ).first()
            
            if not credential:
                return Response({
                    'success': False,
                    'message': f'No active credential found for tenant {tenant.name}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Request report
            report = AmazonAdsReportService.request_report(
                credential=credential,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                tenant=tenant,
                user=request.user
            )
            
            return Response({
                'success': True,
                'message': 'Report requested successfully',
                'report': AdsReportSerializer(report).data
            })
            
        except Tenant.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Tenant not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except ReportType.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Report type not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to request report: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def refresh_status(self, request, pk=None):
        """Refresh the status of a report"""
        report = self.get_object()
        
        try:
            # Get credential for tenant
            credential = AmazonAdsCredential.objects.filter(
                tenant=report.tenant,
                is_active=True
            ).first()
            
            if not credential:
                return Response({
                    'success': False,
                    'message': f'No active credential found for tenant {report.tenant.name}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check report status
            updated_report = AmazonAdsReportService.get_report_status(credential, report)
            
            return Response({
                'success': True,
                'message': f'Report status: {updated_report.status}',
                'report': AdsReportSerializer(updated_report).data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to refresh status: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def process_report(self, request, pk=None):
        """Download and process a completed report"""
        report = self.get_object()
        
        if report.status != 'COMPLETED':
            return Response({
                'success': False,
                'message': 'Report is not completed yet'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get credential for tenant
            credential = AmazonAdsCredential.objects.filter(
                tenant=report.tenant,
                is_active=True
            ).first()
            
            if not credential:
                return Response({
                    'success': False,
                    'message': f'No active credential found for tenant {report.tenant.name}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process report
            success = AmazonAdsReportService.download_and_process_report(credential, report)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Report processed successfully',
                    'report': AdsReportSerializer(report).data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to process report'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to process report: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class DailyProductAdsDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing daily product ads data"""
    queryset = DailyProductAdsData.objects.all().select_related('tenant', 'report')
    serializer_class = DailyProductAdsDataSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter data based on query parameters"""
        queryset = self.queryset
        
        # Filter by tenant
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__range=[start_date, end_date])
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        # Filter by ad group
        ad_group_id = self.request.query_params.get('ad_group_id')
        if ad_group_id:
            queryset = queryset.filter(ad_group_id=ad_group_id)
        
        # Filter by ASIN
        asin = self.request.query_params.get('asin')
        if asin:
            queryset = queryset.filter(advertised_asin=asin)
        
        # Filter by SKU
        sku = self.request.query_params.get('sku')
        if sku:
            queryset = queryset.filter(advertised_sku=sku)
        
        return queryset.order_by('-date')
    
    @action(detail=False, methods=['post'])
    def campaign_summary(self, request):
        """Get campaign performance summary by date range"""
        serializer = DateRangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        start_date = data['start_date']
        end_date = data['end_date']
        tenant_id = request.query_params.get('tenant_id')
        
        if not tenant_id:
            return Response({
                'success': False,
                'message': 'Tenant ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get aggregated data
            summary = DailyProductAdsData.objects.filter(
                tenant_id=tenant_id,
                date__range=[start_date, end_date]
            ).values('campaign_id', 'campaign_name').annotate(
                impressions=Sum('impressions'),
                clicks=Sum('clicks'),
                spend=Sum('spend'),
                sales_1d=Sum('sales_1d'),
                sales_7d=Sum('sales_7d'),
                sales_30d=Sum('sales_30d'),
                units_sold_clicks_30d=Sum('units_sold_clicks_30d'),
                purchases_30d=Sum('purchases_30d'),
                ctr=Sum(F('clicks') * 100.0, output_field=FloatField()) / Sum('impressions'),
                acos_7d=Sum('spend', output_field=FloatField()) * 100.0 / Sum('sales_7d')
            ).order_by('-spend')
            
            # Fix potential division by zero issues
            for item in summary:
                if item['ctr'] is None or not item['impressions']:
                    item['ctr'] = 0
                if item['acos_7d'] is None or not item['sales_7d']:
                    item['acos_7d'] = 0
            
            return Response({
                'success': True,
                'data': summary
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to get campaign summary: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def asin_performance(self, request):
        """Get ASIN performance summary by date range"""
        serializer = DateRangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        start_date = data['start_date']
        end_date = data['end_date']
        tenant_id = request.query_params.get('tenant_id')
        
        if not tenant_id:
            return Response({
                'success': False,
                'message': 'Tenant ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get aggregated data by ASIN
            summary = DailyProductAdsData.objects.filter(
                tenant_id=tenant_id,
                date__range=[start_date, end_date],
                advertised_asin__isnull=False
            ).values('advertised_asin', 'advertised_sku').annotate(
                impressions=Sum('impressions'),
                clicks=Sum('clicks'),
                spend=Sum('spend'),
                sales_1d=Sum('sales_1d'),
                sales_7d=Sum('sales_7d'),
                sales_30d=Sum('sales_30d'),
                units_sold_clicks_30d=Sum('units_sold_clicks_30d'),
                purchases_30d=Sum('purchases_30d'),
                ctr=Sum(F('clicks') * 100.0, output_field=FloatField()) / Sum('impressions'),
                acos_7d=Sum('spend', output_field=FloatField()) * 100.0 / Sum('sales_7d')
            ).order_by('-sales_7d')
            
            # Fix potential division by zero issues
            for item in summary:
                if item['ctr'] is None or not item['impressions']:
                    item['ctr'] = 0
                if item['acos_7d'] is None or not item['sales_7d']:
                    item['acos_7d'] = 0
            
            return Response({
                'success': True,
                'data': summary
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to get ASIN performance: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class SearchTermReportDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing search term report data"""
    queryset = SearchTermReportData.objects.all().select_related('tenant', 'report')
    serializer_class = SearchTermReportDataSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter data based on query parameters"""
        queryset = self.queryset
        
        # Filter by tenant
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__range=[start_date, end_date])
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        # Filter by ad group
        ad_group_id = self.request.query_params.get('ad_group_id')
        if ad_group_id:
            queryset = queryset.filter(ad_group_id=ad_group_id)
        
        # Filter by query
        query = self.request.query_params.get('query')
        if query:
            queryset = queryset.filter(query__icontains=query)
        
        return queryset.order_by('-clicks')
    
    @action(detail=False, methods=['post'])
    def top_search_terms(self, request):
        """Get top performing search terms by date range"""
        serializer = DateRangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        start_date = data['start_date']
        end_date = data['end_date']
        tenant_id = request.query_params.get('tenant_id')
        
        if not tenant_id:
            return Response({
                'success': False,
                'message': 'Tenant ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get aggregated data by search query
            summary = SearchTermReportData.objects.filter(
                tenant_id=tenant_id,
                date__range=[start_date, end_date]
            ).values('query').annotate(
                impressions=Sum('impressions'),
                clicks=Sum('clicks'),
                cost=Sum('cost'),
                conversions=Sum('conversions'),
                sales_7d=Sum('sales_7d'),
                sales_14d=Sum('sales_14d'),
                sales_30d=Sum('sales_30d'),
                ctr=Sum(F('clicks') * 100.0, output_field=FloatField()) / Sum('impressions'),
                conversion_rate=Sum(F('conversions') * 100.0, output_field=FloatField()) / Sum('clicks'),
                acos_7d=Sum('cost', output_field=FloatField()) * 100.0 / Sum('sales_7d')
            ).order_by('-clicks')[:100]  # Limit to top 100 terms
            
            # Fix potential division by zero issues
            for item in summary:
                if item['ctr'] is None or not item['impressions']:
                    item['ctr'] = 0
                if item['conversion_rate'] is None or not item['clicks']:
                    item['conversion_rate'] = 0
                if item['acos_7d'] is None or not item['sales_7d']:
                    item['acos_7d'] = 0
            
            return Response({
                'success': True,
                'data': summary
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to get top search terms: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class ReportScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing report schedules"""
    queryset = ReportSchedule.objects.all().select_related('tenant', 'report_type')
    serializer_class = ReportScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter schedules based on query parameters"""
        queryset = self.queryset
        
        # Filter by tenant
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        # Filter by report type
        report_type_id = self.request.query_params.get('report_type_id')
        if report_type_id:
            queryset = queryset.filter(report_type_id=report_type_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset.order_by('next_run')
    
    def perform_create(self, serializer):
        """Set created_by and calculate next_run when creating a schedule"""
        # Set the current user
        serializer.save(
            created_by=self.request.user,
            next_run=timezone.now() + timedelta(minutes=5)  # Default to 5 minutes from now
        )
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle the active status of a schedule"""
        schedule = self.get_object()
        schedule.is_active = not schedule.is_active
        schedule.save(update_fields=['is_active', 'updated_at'])
        
        return Response({
            'success': True,
            'is_active': schedule.is_active,
            'message': f"Schedule {'activated' if schedule.is_active else 'deactivated'} successfully"
        })
