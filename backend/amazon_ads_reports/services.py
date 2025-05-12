import requests
import logging
import json
import gzip
import time
import random
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Q

from .models import (
    Tenant, AmazonAdsCredential, ReportType, AdsReport, 
    DailyProductAdsData, SearchTermReportData, ReportSchedule
)

logger = logging.getLogger(__name__)

class AmazonAdsAuth:
    """Authentication service for Amazon Ads API"""
    
    # API endpoints by region
    API_ENDPOINTS = {
        'NA': 'https://advertising-api.amazon.com',
        'EU': 'https://advertising-api-eu.amazon.com',
        'FE': 'https://advertising-api-fe.amazon.com',
    }
    
    # Token endpoint
    TOKEN_URL = 'https://api.amazon.com/auth/o2/token'
    
    @classmethod
    def get_access_token(cls, credential):
        """
        Get a valid access token for a credential
        
        Args:
            credential: AmazonAdsCredential instance
            
        Returns:
            String access token
        """
        if credential.is_token_expired():
            logger.info(f"Refreshing expired token for credential {credential.id}")
            
            try:
                payload = {
                    'grant_type': 'refresh_token',
                    'refresh_token': credential.refresh_token,
                    'client_id': credential.client_id,
                    'client_secret': credential.client_secret,
                }
                
                response = requests.post(cls.TOKEN_URL, data=payload)
                response.raise_for_status()
                token_data = response.json()
                
                # Update credential with new token data
                credential.access_token = token_data['access_token']
                # Amazon tokens typically expire in 1 hour
                expiration = timezone.now() + timedelta(seconds=token_data.get('expires_in', 3600))
                credential.token_expires_at = expiration
                credential.save(update_fields=['access_token', 'token_expires_at', 'updated_at'])
                
                logger.info(f"Successfully refreshed token for credential {credential.id}")
            except Exception as e:
                logger.error(f"Failed to refresh token: {str(e)}")
                raise
        
        return credential.access_token
    
    @classmethod
    def get_headers(cls, credential):
        """
        Get headers for API requests
        
        Args:
            credential: AmazonAdsCredential instance
            
        Returns:
            Dict with request headers
        """
        access_token = cls.get_access_token(credential)
        
        return {
            'Authorization': f"Bearer {access_token}",
            'Amazon-Advertising-API-ClientId': credential.client_id,
            'Amazon-Advertising-API-Scope': credential.profile_id,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    @classmethod
    def get_api_endpoint(cls, credential):
        """
        Get the API endpoint for the credential's region
        
        Args:
            credential: AmazonAdsCredential instance
            
        Returns:
            API endpoint URL
        """
        return cls.API_ENDPOINTS.get(credential.region)


class AmazonAdsReportService:
    """Service for managing Amazon Ads reports"""
    
    @classmethod
    def request_report(cls, credential, report_type, start_date, end_date, tenant, user=None):
        """
        Request a report from Amazon Ads API
        
        Args:
            credential: AmazonAdsCredential instance
            report_type: ReportType instance
            start_date: Start date (datetime.date)
            end_date: End date (datetime.date)
            tenant: Tenant instance
            user: Optional user requesting the report
            
        Returns:
            AdsReport instance
        """
        # Prepare report configuration
        api_endpoint = AmazonAdsAuth.get_api_endpoint(credential)
        url = f"{api_endpoint}/reporting/reports"
        
        # Format dates for Amazon API
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Build request body
        request_body = {
            "name": f"{report_type.name} report",
            "startDate": start_date_str,
            "endDate": end_date_str,
            "configuration": {
                "adProduct": report_type.ad_product,
                "columns": report_type.metrics,
                "reportTypeId": report_type.api_report_type,
                "timeUnit": report_type.time_unit,
                "format": "GZIP_JSON"
            }
        }
        
        # Add group_by if specified
        if hasattr(report_type, 'default_group_by') and report_type.default_group_by:
            request_body["configuration"]["groupBy"] = report_type.default_group_by
        
        # Get request headers
        headers = AmazonAdsAuth.get_headers(credential)
        
        try:
            # Create report record
            report = AdsReport.objects.create(
                tenant=tenant,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                selected_metrics=report_type.metrics,
                status='PENDING',
                created_by=user
            )
            
            # Make API request
            response = requests.post(url, headers=headers, json=request_body)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Update report with Amazon report ID
            report.amazon_report_id = result.get('reportId')
            report.status = 'IN_PROGRESS'
            report.save(update_fields=['amazon_report_id', 'status', 'updated_at'])
            
            logger.info(f"Requested report {report.amazon_report_id} for tenant {tenant.name}")
            return report
            
        except Exception as e:
            logger.error(f"Error requesting report: {str(e)}")
            if 'report' in locals():
                report.status = 'FAILED'
                report.error_message = str(e)
                report.save(update_fields=['status', 'error_message', 'updated_at'])
            raise
    
    @classmethod
    def get_report_status(cls, credential, report):
        """
        Check the status of a report
        
        Args:
            credential: AmazonAdsCredential instance
            report: AdsReport instance
            
        Returns:
            Updated report status
        """
        if not report.amazon_report_id:
            logger.error(f"Cannot check status for report {report.id} - no Amazon report ID")
            return report
        
        api_endpoint = AmazonAdsAuth.get_api_endpoint(credential)
        url = f"{api_endpoint}/reporting/reports/{report.amazon_report_id}"
        
        headers = AmazonAdsAuth.get_headers(credential)
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            status = result.get('status')
            
            # Update report
            report.status = status
            
            if status == 'COMPLETED':
                report.download_url = result.get('location')
                report.completed_at = timezone.now()
            elif status == 'FAILED':
                report.error_message = result.get('statusDetails', 'Report generation failed')
                
            report.save()
            
            logger.info(f"Report {report.amazon_report_id} status: {status}")
            return report
            
        except Exception as e:
            logger.error(f"Error checking report status: {str(e)}")
            return report
    
    @classmethod
    def download_and_process_report(cls, credential, report):
        """
        Download and process a completed report
        
        Args:
            credential: AmazonAdsCredential instance
            report: AdsReport instance
            
        Returns:
            True if successful, False otherwise
        """
        if report.status != 'COMPLETED' or not report.download_url:
            logger.error(f"Cannot download report {report.id} - not completed or no URL")
            return False
        
        try:
            # Download report
            response = requests.get(report.download_url)
            response.raise_for_status()
            
            # Decompress and parse the report
            compressed_data = BytesIO(response.content)
            decompressed_data = gzip.GzipFile(fileobj=compressed_data).read()
            report_data = json.loads(decompressed_data)
            
            # Process based on report type
            report_type_slug = report.report_type.slug
            
            if report_type_slug == 'daily-product-ads':
                cls._process_daily_product_ads_report(report, report_data)
            elif report_type_slug == 'search-term':
                cls._process_search_term_report(report, report_data)
            else:
                logger.warning(f"No processor for report type: {report_type_slug}")
                return False
            
            # Mark report as stored
            report.is_stored = True
            report.save(update_fields=['is_stored', 'updated_at'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading and processing report: {str(e)}")
            return False
    
    @classmethod
    def _process_daily_product_ads_report(cls, report, report_data):
        """
        Process daily product ads report data
        
        Args:
            report: AdsReport instance
            report_data: JSON data from the report
            
        Returns:
            Number of records processed
        """
        tenant = report.tenant
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(report_data)
        if df.empty:
            logger.info(f"No data in report {report.id}")
            return 0
        
        # Track processing
        count = 0
        
        # Process in chunks to avoid memory issues with large reports
        chunk_size = 1000
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            
            # Process each record in the chunk
            records = []
            for _, row in chunk.iterrows():
                try:
                    # Create model instances but don't save yet
                    record = DailyProductAdsData(
                        tenant=tenant,
                        report=report,
                        date=datetime.strptime(row.get('date', ''), '%Y-%m-%d').date(),
                        portfolio_id=row.get('portfolioId'),
                        campaign_name=row.get('campaignName'),
                        campaign_id=row.get('campaignId'),
                        ad_group_name=row.get('adGroupName'),
                        ad_group_id=row.get('adGroupId'),
                        ad_id=row.get('adId'),
                        campaign_budget_type=row.get('campaignBudgetType'),
                        campaign_budget_amount=row.get('campaignBudgetAmount'),
                        campaign_budget_currency_code=row.get('campaignBudgetCurrencyCode'),
                        campaign_status=row.get('campaignStatus'),
                        advertised_asin=row.get('advertisedAsin'),
                        advertised_sku=row.get('advertisedSku'),
                        impressions=row.get('impressions', 0),
                        clicks=row.get('clicks', 0),
                        click_through_rate=row.get('clickThroughRate'),
                        cost=row.get('cost', 0),
                        cost_per_click=row.get('costPerClick'),
                        spend=row.get('spend', 0),
                        units_sold_clicks_30d=row.get('unitsSoldClicks30d', 0),
                        units_sold_same_sku_30d=row.get('unitsSoldSameSku30d', 0),
                        sales_1d=row.get('sales1d', 0),
                        sales_7d=row.get('sales7d', 0),
                        sales_14d=row.get('sales14d', 0),
                        sales_30d=row.get('sales30d', 0),
                        attributed_sales_same_sku_30d=row.get('attributedSalesSameSku30d', 0),
                        purchases_1d=row.get('purchases1d', 0),
                        purchases_7d=row.get('purchases7d', 0),
                        purchases_14d=row.get('purchases14d', 0),
                        purchases_30d=row.get('purchases30d', 0),
                        purchases_same_sku_30d=row.get('purchasesSameSku30d', 0),
                        units_sold_other_sku_7d=row.get('unitsSoldOtherSku7d', 0),
                        sales_other_sku_7d=row.get('salesOtherSku7d', 0),
                    )
                    records.append(record)
                except Exception as e:
                    logger.error(f"Error processing record: {str(e)}")
            
            # Bulk create records
            with transaction.atomic():
                DailyProductAdsData.objects.bulk_create(
                    records, 
                    ignore_conflicts=True,  # Skip duplicates based on unique constraint
                    batch_size=100
                )
            
            count += len(records)
            logger.info(f"Processed {len(records)} daily product ads records for tenant {tenant.name}")
        
        # Update report with count
        report.rows_processed = count
        report.save(update_fields=['rows_processed', 'updated_at'])
        
        return count
    
    @classmethod
    def _process_search_term_report(cls, report, report_data):
        """
        Process search term report data
        
        Args:
            report: AdsReport instance
            report_data: JSON data from the report
            
        Returns:
            Number of records processed
        """
        tenant = report.tenant
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(report_data)
        if df.empty:
            logger.info(f"No data in report {report.id}")
            return 0
        
        # Track processing
        count = 0
        
        # Process in chunks to avoid memory issues with large reports
        chunk_size = 1000
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            
            # Process each record in the chunk
            records = []
            for _, row in chunk.iterrows():
                try:
                    # Create model instances but don't save yet
                    record = SearchTermReportData(
                        tenant=tenant,
                        report=report,
                        date=datetime.strptime(row.get('date', ''), '%Y-%m-%d').date(),
                        campaign_name=row.get('campaignName'),
                        campaign_id=row.get('campaignId'),
                        ad_group_name=row.get('adGroupName'),
                        ad_group_id=row.get('adGroupId'),
                        keyword_text=row.get('keywordText'),
                        match_type=row.get('matchType'),
                        query=row.get('query', ''),
                        impressions=row.get('impressions', 0),
                        clicks=row.get('clicks', 0),
                        click_through_rate=row.get('clickThroughRate'),
                        cost=row.get('cost', 0),
                        cost_per_click=row.get('costPerClick'),
                        conversions=row.get('conversions', 0),
                        conversion_rate=row.get('conversionRate'),
                        sales_7d=row.get('sales7d', 0),
                        sales_14d=row.get('sales14d', 0),
                        sales_30d=row.get('sales30d', 0),
                    )
                    records.append(record)
                except Exception as e:
                    logger.error(f"Error processing record: {str(e)}")
            
            # Bulk create records
            with transaction.atomic():
                SearchTermReportData.objects.bulk_create(
                    records,
                    ignore_conflicts=True,  # Skip duplicates based on unique constraint
                    batch_size=100
                )
            
            count += len(records)
            logger.info(f"Processed {len(records)} search term records for tenant {tenant.name}")
        
        # Update report with count
        report.rows_processed = count
        report.save(update_fields=['rows_processed', 'updated_at'])
        
        return count
    
    @classmethod
    def process_scheduled_reports(cls):
        """
        Process reports due to be generated based on schedule
        This method is designed to be called from a cron job
        
        Returns:
            Number of reports generated
        """
        now = timezone.now()
        count = 0
        
        # Get all active schedules that are due to run (next_run <= now)
        due_schedules = ReportSchedule.objects.filter(
            is_active=True,
            next_run__lte=now
        )
        
        logger.info(f"Processing {due_schedules.count()} scheduled reports")
        
        for schedule in due_schedules:
            try:
                # Get credential for tenant
                credential = AmazonAdsCredential.objects.filter(
                    tenant=schedule.tenant,
                    is_active=True
                ).first()
                
                if not credential:
                    logger.warning(f"No active credential found for tenant {schedule.tenant.name}")
                    continue
                
                # Calculate date range
                end_date = now.date() - timedelta(days=1)  # Yesterday
                start_date = end_date - timedelta(days=schedule.lookback_days)
                
                # Request the report
                report = cls.request_report(
                    credential=credential,
                    report_type=schedule.report_type,
                    start_date=start_date,
                    end_date=end_date,
                    tenant=schedule.tenant,
                    user=schedule.created_by
                )
                
                # Update schedule
                schedule.last_run = now
                schedule.next_run = schedule.calculate_next_run()
                schedule.save(update_fields=['last_run', 'next_run', 'updated_at'])
                
                count += 1
                logger.info(f"Generated scheduled report {report.id} for schedule {schedule.name}")
                
                # Add random delay to avoid hitting API rate limits
                sleep_time = random.uniform(1, 5)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error processing scheduled report {schedule.id}: {str(e)}")
                
                # Update next_run even if there was an error to prevent retrying too frequently
                try:
                    schedule.last_run = now
                    schedule.next_run = schedule.calculate_next_run()
                    schedule.save(update_fields=['last_run', 'next_run', 'updated_at'])
                except Exception as save_error:
                    logger.error(f"Error updating schedule after failure: {str(save_error)}")
        
        return count
    
    @classmethod
    def process_pending_reports(cls):
        """
        Process pending reports - check status, download and process completed reports
        This method is designed to be called from a cron job
        
        Returns:
            Number of reports processed
        """
        count = 0
        
        # Get reports that are in progress or pending
        pending_reports = AdsReport.objects.filter(
            Q(status='PENDING') | Q(status='IN_PROGRESS')
        ).select_related('tenant').order_by('created_at')
        
        logger.info(f"Processing {pending_reports.count()} pending reports")
        
        for report in pending_reports:
            try:
                # Get credential for tenant
                credential = AmazonAdsCredential.objects.filter(
                    tenant=report.tenant,
                    is_active=True
                ).first()
                
                if not credential:
                    logger.warning(f"No active credential found for tenant {report.tenant.name}")
                    continue
                
                # Check report status
                updated_report = cls.get_report_status(credential, report)
                
                # If completed, download and process
                if updated_report.status == 'COMPLETED':
                    success = cls.download_and_process_report(credential, updated_report)
                    if success:
                        count += 1
                
                # Add random delay to avoid hitting API rate limits
                sleep_time = random.uniform(1, 3)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error processing report {report.id}: {str(e)}")
        
        return count 