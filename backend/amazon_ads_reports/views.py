from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound
from django.utils import timezone
from django.db.models import Q, Sum, F, FloatField
from django.db.models.functions import Cast
from datetime import datetime, timedelta
import logging
import requests
import time
from io import BytesIO

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

logger = logging.getLogger(__name__)

class TenantViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tenants"""
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [] # Temporarily removing permissions
    
    def get_queryset(self):
        """Filter tenants based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        # If tenant access permissions were to be implemented, they'd be checked here
        return self.queryset.filter(is_active=True)

class AmazonAdsCredentialViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Amazon Ads API credentials"""
    queryset = AmazonAdsCredential.objects.all().select_related('tenant')
    serializer_class = AmazonAdsCredentialSerializer
    permission_classes = [] # Temporarily removing permissions
    
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
    permission_classes = [] # Temporarily removing permissions

class AdsReportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ads reports"""
    queryset = AdsReport.objects.all().select_related('tenant', 'report_type')
    serializer_class = AdsReportSerializer
    permission_classes = [] # Temporarily removing IsAuthenticated
    
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
            
            # Get credential and log debug info
            credential = AmazonAdsCredential.objects.filter(
                tenant=tenant,
                is_active=True
            ).first()
            
            if not credential:
                return Response({
                    'success': False,
                    'message': f'No active credential found for tenant {tenant.name}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Debug logging
            logger.debug(f"Using credential: ID={credential.id}, Profile={credential.profile_id}, Region={credential.region}")
            logger.debug(f"Report request params: type={report_type.name}, start={start_date}, end={end_date}")
            
            # Request report
            try:
                report = AmazonAdsReportService.request_report(
                    credential=credential,
                    report_type=report_type,
                    start_date=start_date,
                    end_date=end_date,
                    tenant=tenant,
                    user=None, # Removed request.user
                    group_by=group_by  # Pass the group_by parameter
                )
                
                return Response({
                    'success': True,
                    'message': 'Report requested successfully',
                    'report': AdsReportSerializer(report).data
                })
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'API error: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
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
            
            # If download_url is not in the report, try to get it
            if not report.download_url:
                logger.info(f"Report {report.id} is completed but doesn't have a download URL, attempting to get it")
                report_url = AmazonAdsReportService.get_report_url(credential, report.amazon_report_id)
                
                if report_url:
                    logger.info(f"Retrieved download URL for report {report.id}: {report_url}")
                    report.download_url = report_url
                    report.save(update_fields=['download_url', 'updated_at'])
                else:
                    return Response({
                        'success': False,
                        'message': 'Could not retrieve report download URL'
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

    @action(detail=True, methods=['post'])
    def diagnose_report(self, request, pk=None):
        """Diagnose issues with a report by downloading and examining its raw data"""
        report = self.get_object()
        
        if not report.download_url:
            return Response({
                'success': False,
                'message': 'Report has no download URL'
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
            
            # Download report
            logger.info(f"Diagnostic: Downloading report from URL: {report.download_url}")
            
            # Download with retry logic
            MAX_RETRIES = 3
            RETRY_BACKOFF = 2  # seconds
            retries = 0
            response = None
            
            while retries < MAX_RETRIES and not response:
                try:
                    # Set reasonable timeouts (connect_timeout, read_timeout)
                    response = requests.get(
                        report.download_url, 
                        timeout=(10, 300),  # 10s connect, 300s read
                        stream=True  # Use streaming to handle large files
                    )
                    
                    if response.status_code != 200:
                        logger.info(f"Diagnostic: Failed to download report: {response.status_code} - {response.text}")
                        retries += 1
                        if retries >= MAX_RETRIES:
                            return Response({
                                'success': False,
                                'message': f'Failed to download report after {MAX_RETRIES} attempts: {response.status_code} - {response.text}'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        time.sleep(RETRY_BACKOFF * retries)
                        continue
                        
                    # Stream the response content into memory to avoid loading entire file at once
                    content = BytesIO()
                    total_size = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            content.write(chunk)
                            total_size += len(chunk)
                    
                    content.seek(0)
                    logger.info(f"Diagnostic: Successfully downloaded report: {total_size} bytes")
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, 
                        ConnectionResetError, ConnectionAbortedError) as conn_error:
                    retries += 1
                    logger.warning(f"Diagnostic: Connection error during download (attempt {retries}/{MAX_RETRIES}): {str(conn_error)}")
                    if retries >= MAX_RETRIES:
                        return Response({
                            'success': False,
                            'message': f'Connection error during download after {MAX_RETRIES} attempts: {str(conn_error)}',
                            'error_details': str(conn_error)
                        }, status=status.HTTP_400_BAD_REQUEST)
                    time.sleep(RETRY_BACKOFF * retries)
            
            if not response:
                return Response({
                    'success': False,
                    'message': 'Failed to download report after multiple attempts'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Decompress and parse the report
            try:
                import gzip
                import zipfile
                from io import BytesIO
                import json
                
                compressed_data = content  # Use the streamed content
                decompressed_data = None
                format_type = "unknown"
                
                # Try GZIP format
                try:
                    logger.info("Diagnostic: Attempting to decompress as GZIP")
                    decompressed_data = gzip.decompress(compressed_data.getvalue()).decode('utf-8')
                    format_type = "gzip"
                    logger.info(f"Diagnostic: Successfully decompressed as GZIP: {len(decompressed_data)} bytes")
                except Exception as gzip_error:
                    logger.info(f"Diagnostic: GZIP decompression failed: {str(gzip_error)}")
                    
                    # Try ZIP format
                    try:
                        # Reset BytesIO position
                        compressed_data.seek(0)
                        with zipfile.ZipFile(compressed_data) as zip_ref:
                            # Get first file in the archive
                            file_names = zip_ref.namelist()
                            logger.info(f"Diagnostic: ZIP contains files: {file_names}")
                            
                            if file_names:
                                with zip_ref.open(file_names[0]) as file:
                                    decompressed_data = file.read()
                                    format_type = "zip"
                                    logger.info(f"Diagnostic: Successfully decompressed as ZIP: {len(decompressed_data)} bytes")
                    except Exception as zip_error:
                        logger.info(f"Diagnostic: ZIP decompression also failed: {str(zip_error)}")
                        
                        # Try raw JSON (uncompressed)
                        try:
                            compressed_data.seek(0)
                            raw_content = compressed_data.read().decode('utf-8')
                            json.loads(raw_content)  # Just to validate
                            decompressed_data = raw_content.encode()
                            format_type = "uncompressed-json"
                            logger.info("Diagnostic: Content appears to be uncompressed JSON")
                        except Exception as json_error:
                            logger.info(f"Diagnostic: Not uncompressed JSON either: {str(json_error)}")
                
                # If no decompression method worked
                if not decompressed_data:
                    return Response({
                        'success': False,
                        'message': 'Failed to decompress report data',
                        'format_details': {
                            'content_length': len(response.content),
                            'content_type': response.headers.get('Content-Type'),
                            'first_bytes': str(response.content[:100])
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Parse JSON
                report_data = json.loads(decompressed_data)
                
                # Log data format details
                data_type = type(report_data).__name__
                sample_size = min(3, len(report_data) if isinstance(report_data, list) else 0)
                
                logger.info(f"Diagnostic: Report data type: {data_type}")
                logger.info(f"Diagnostic: Report data length: {len(report_data) if isinstance(report_data, list) else 'Not a list'}")
                
                # Details about the content
                if isinstance(report_data, list) and len(report_data) > 0:
                    # Show sample
                    sample = report_data[:sample_size]
                    logger.info(f"Diagnostic: Sample data: {json.dumps(sample, indent=2)}")
                    
                    # Show available fields
                    if len(report_data) > 0:
                        sample_keys = sample[0].keys() if isinstance(sample[0], dict) else "Not a dictionary"
                        logger.info(f"Diagnostic: Available fields: {sample_keys}")
                elif isinstance(report_data, dict):
                    logger.info(f"Diagnostic: Dictionary keys: {report_data.keys()}")
                    logger.info(f"Diagnostic: Report data: {json.dumps(report_data, indent=2)}")
                
                # Return a summary
                return Response({
                    'success': True,
                    'message': 'Report diagnostic completed',
                    'format': {
                        'compression_type': format_type,
                        'data_type': data_type,
                        'length': len(report_data) if isinstance(report_data, list) else 'Not a list',
                        'sample_available': isinstance(report_data, list) and len(report_data) > 0,
                        'sample_keys': list(sample[0].keys()) if isinstance(report_data, list) and len(report_data) > 0 and isinstance(sample[0], dict) else None
                    }
                })
                
            except Exception as e:
                logger.error(f"Diagnostic: Error examining report data: {str(e)}")
                return Response({
                    'success': False,
                    'message': f'Error examining report data: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Diagnostic: Error: {str(e)}")
            return Response({
                'success': False,
                'message': f'Diagnostic error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def examine_raw_data(self, request, pk=None):
        """Examine the raw data structure of a report for debugging purposes"""
        report = self.get_object()
        
        if not report.download_url:
            return Response({
                'success': False,
                'message': 'Report has no download URL'
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
            
            # Download report with retry logic
            MAX_RETRIES = 3
            RETRY_BACKOFF = 2  # seconds
            retries = 0
            response = None
            
            while retries < MAX_RETRIES and not response:
                try:
                    # Set reasonable timeouts (connect_timeout, read_timeout)
                    response = requests.get(
                        report.download_url, 
                        timeout=(10, 300),
                        stream=True
                    )
                    
                    if response.status_code != 200:
                        logger.info(f"Failed to download report: {response.status_code} - {response.text}")
                        retries += 1
                        if retries >= MAX_RETRIES:
                            return Response({
                                'success': False,
                                'message': f'Failed to download report after {MAX_RETRIES} attempts'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        time.sleep(RETRY_BACKOFF * retries)
                        continue
                        
                    # Stream the response content into memory
                    content = BytesIO()
                    total_size = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            content.write(chunk)
                            total_size += len(chunk)
                    
                    content.seek(0)
                    logger.info(f"Successfully downloaded report: {total_size} bytes")
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, 
                        ConnectionResetError, ConnectionAbortedError) as conn_error:
                    retries += 1
                    logger.warning(f"Connection error during download (attempt {retries}/{MAX_RETRIES}): {str(conn_error)}")
                    if retries >= MAX_RETRIES:
                        return Response({
                            'success': False,
                            'message': f'Connection error during download after {MAX_RETRIES} attempts'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    time.sleep(RETRY_BACKOFF * retries)
            
            if not response:
                return Response({
                    'success': False,
                    'message': 'Failed to download report after multiple attempts'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Decompress and parse the report
            try:
                import gzip
                import zipfile
                import json
                
                compressed_data = content
                decompressed_data = None
                format_type = "unknown"
                
                # Try GZIP format
                try:
                    decompressed_data = gzip.decompress(compressed_data.getvalue()).decode('utf-8')
                    format_type = "gzip"
                except Exception:
                    # Try ZIP format
                    try:
                        compressed_data.seek(0)
                        with zipfile.ZipFile(compressed_data) as zip_ref:
                            file_names = zip_ref.namelist()
                            if file_names:
                                with zip_ref.open(file_names[0]) as file:
                                    decompressed_data = file.read()
                                    format_type = "zip"
                    except Exception:
                        # Try direct JSON
                        try:
                            compressed_data.seek(0)
                            raw_content = compressed_data.read().decode('utf-8')
                            json.loads(raw_content)  # Validate it's JSON
                            decompressed_data = raw_content.encode()
                            format_type = "raw_json"
                        except Exception:
                            pass
                
                if not decompressed_data:
                    return Response({
                        'success': False,
                        'message': 'Could not decompress report data'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Parse JSON
                report_data = json.loads(decompressed_data)
                
                # Analyze the structure
                structure_info = {}
                
                if isinstance(report_data, list):
                    structure_info['type'] = 'array'
                    structure_info['length'] = len(report_data)
                    if len(report_data) > 0:
                        structure_info['first_item'] = report_data[0]
                        if isinstance(report_data[0], dict):
                            structure_info['keys'] = list(report_data[0].keys())
                elif isinstance(report_data, dict):
                    structure_info['type'] = 'object'
                    structure_info['keys'] = list(report_data.keys())
                    
                    # Check for common nested data patterns
                    if 'data' in report_data:
                        structure_info['data_field'] = {
                            'type': type(report_data['data']).__name__
                        }
                        if isinstance(report_data['data'], list):
                            structure_info['data_field']['length'] = len(report_data['data'])
                            if len(report_data['data']) > 0:
                                structure_info['data_field']['first_item'] = report_data['data'][0]
                    
                    if 'response' in report_data:
                        structure_info['response_field'] = {
                            'type': type(report_data['response']).__name__
                        }
                        if isinstance(report_data['response'], dict) and 'data' in report_data['response']:
                            structure_info['response_field']['has_data'] = True
                    
                    if 'result' in report_data:
                        structure_info['result_field'] = {
                            'type': type(report_data['result']).__name__
                        }
                
                # Limit the size of the response
                if 'first_item' in structure_info and isinstance(structure_info['first_item'], dict):
                    # Truncate any long string values
                    for key, value in structure_info['first_item'].items():
                        if isinstance(value, str) and len(value) > 100:
                            structure_info['first_item'][key] = value[:100] + "..."
                
                return Response({
                    'success': True,
                    'message': 'Raw data examination completed',
                    'format_type': format_type,
                    'structure': structure_info,
                    'sample': structure_info.get('first_item') or report_data if isinstance(report_data, dict) else None
                })
                
            except Exception as e:
                logger.error(f"Error examining raw data: {str(e)}")
                return Response({
                    'success': False,
                    'message': f'Error examining raw data: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error in examine_raw_data: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def error_details(self, request, pk=None):
        """Get detailed error information for a report"""
        report = self.get_object()
        
        data = {
            'id': str(report.id),
            'amazon_report_id': report.amazon_report_id,
            'status': report.status,
            'error_message': report.error_message,
            'is_stored': report.is_stored,
            'rows_processed': report.rows_processed,
            'created_at': report.created_at,
            'updated_at': report.updated_at,
            'completed_at': report.completed_at,
        }
        
        # Get log entries related to this report (from debug.log)
        try:
            report_logs = []
            with open('backend/debug.log', 'r') as log_file:
                for line in log_file:
                    if str(report.id) in line or (report.amazon_report_id and report.amazon_report_id in line):
                        report_logs.append(line.strip())
            
            # Get the last 50 log entries if there are too many
            if len(report_logs) > 50:
                data['log_entries'] = report_logs[-50:]
                data['log_entries_count'] = len(report_logs)
            else:
                data['log_entries'] = report_logs
                data['log_entries_count'] = len(report_logs)
        except Exception as e:
            data['log_error'] = str(e)
        
        return Response(data)

class DailyProductAdsDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing daily product ads data"""
    queryset = DailyProductAdsData.objects.all().select_related('tenant', 'report')
    serializer_class = DailyProductAdsDataSerializer
    permission_classes = [] # Temporarily removing permissions
    
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
    permission_classes = [] # Temporarily removing permissions
    
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
    permission_classes = [] # Temporarily removing permissions
    
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
