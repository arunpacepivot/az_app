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
import zipfile
import numpy as np

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
    
    # Token endpoint - updated to match working implementation
    TOKEN_URL = 'https://api.amazon.co.uk/auth/o2/token'
    
    @classmethod
    def get_access_token(cls, credential):
        """
        Get a valid access token for a credential
        
        Args:
            credential: AmazonAdsCredential instance
            
        Returns:
            String access token
        """
        # Always refresh token on each call to match the drive implementation
        logger.info(f"Getting access token for credential {credential.id}")
        
        try:
            url = "https://api.amazon.co.uk/auth/o2/token"
            form_data = {
                "grant_type": "refresh_token",
                "client_id": credential.client_id,
                "client_secret": credential.client_secret,
                "refresh_token": credential.refresh_token,
                "scope": "profile"  # Using exact same scope as working implementation
            }
            
            logger.debug(f"Token refresh request: {url}")
            logger.debug(f"Client ID: {credential.client_id}")
            logger.debug(f"Profile ID: {credential.profile_id}")
            
            response = requests.post(url, data=form_data)
            logger.debug(f"Token refresh status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Failed to get access token: {response.text}")
                raise Exception(f"Failed to get access token: {response.text}")
            
            token_data = response.json()
            access_token = token_data['access_token']
            
            # Update credential with new token data
            credential.access_token = access_token
            expiration = timezone.now() + timedelta(seconds=token_data.get('expires_in', 3600))
            credential.token_expires_at = expiration
            credential.save(update_fields=['access_token', 'token_expires_at', 'updated_at'])
            
            logger.info(f"Successfully refreshed token for credential {credential.id}")
            return access_token
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            raise
    
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
        
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Amazon-Advertising-API-ClientId': credential.client_id,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        # Only add profile ID if it's present
        if credential.profile_id:
            headers['Amazon-Advertising-API-Scope'] = credential.profile_id
            
        logger.debug(f"Generated headers: {headers}")
        return headers
    
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
    def request_report(cls, credential, report_type, start_date, end_date, tenant, user=None, group_by=None):
        """
        Request a report from Amazon Ads API
        
        Args:
            credential: AmazonAdsCredential instance
            report_type: ReportType instance
            start_date: Start date (datetime.date)
            end_date: End date (datetime.date)
            tenant: Tenant instance
            user: Optional user requesting the report
            group_by: Optional list of group_by parameters
            
        Returns:
            AdsReport instance
        """
        # Prepare report configuration
        url = "https://advertising-api-eu.amazon.com/reporting/reports"
        
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
        
        # Handle groupBy parameter - use user provided group_by if available
        if group_by and isinstance(group_by, list) and len(group_by) > 0:
            logger.info(f"Using user-provided groupBy: {group_by}")
            request_body["configuration"]["groupBy"] = group_by
        # Otherwise use default groupBy from report_type if available
        elif hasattr(report_type, 'default_group_by') and report_type.default_group_by and isinstance(report_type.default_group_by, list) and len(report_type.default_group_by) > 0:
            logger.info(f"Using default groupBy from report_type: {report_type.default_group_by}")
            request_body["configuration"]["groupBy"] = report_type.default_group_by
        # Otherwise use specific defaults based on report type
        else:
            # For daily product ads specifically, use ["advertiser"]
            if report_type.api_report_type == "spAdvertisedProduct":
                request_body["configuration"]["groupBy"] = ["advertiser"]
                logger.info("Using default groupBy ['advertiser'] for spAdvertisedProduct")
            # For sponsored display reports, also use ["advertiser"]
            elif report_type.api_report_type == "sdAdvertisedProduct":
                request_body["configuration"]["groupBy"] = ["advertiser"]
                logger.info("Using default groupBy ['advertiser'] for sdAdvertisedProduct")
            # For campaign placement reports, also use ["advertiser"]
            elif report_type.api_report_type == "spCampaignPlacement":
                request_body["configuration"]["groupBy"] = ["advertiser"]
                logger.info("Using default groupBy ['advertiser'] for spCampaignPlacement")
        
        # Get a fresh access token
        access_token = AmazonAdsAuth.get_access_token(credential)
        
        # Create headers exactly like in the working implementation
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Amazon-Advertising-API-ClientId": credential.client_id,
            "Amazon-Advertising-API-Scope": credential.profile_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Create report instance
        report = AdsReport.objects.create(
            tenant=tenant,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            selected_metrics=report_type.metrics,
            group_by=group_by if group_by else getattr(report_type, 'default_group_by', None),
            status='PENDING',
            created_by=user
        )
        
        try:
            # Print debug info
            logger.debug(f"Requesting report with URL: {url}")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Request body: {request_body}")
            
            # Make API request
            response = requests.post(url, headers=headers, json=request_body)
            logger.debug(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"Error requesting report: {response.status_code} - {response.text}"
                logger.error(error_msg)
                report.status = 'FAILED'
                report.error_message = error_msg
                report.save()
                raise Exception(error_msg)
            
            result = response.json()
            logger.debug(f"Response: {result}")
            
            if 'reportId' not in result:
                error_msg = f"Failed to get reportId: {result}"
                logger.error(error_msg)
                report.status = 'FAILED'
                report.error_message = error_msg
                report.save()
                raise Exception(error_msg)
            
            # Update report with Amazon report ID
            report.amazon_report_id = result.get('reportId')
            report.status = 'IN_PROGRESS'
            report.save()
            
            logger.info(f"Successfully requested report: {report.amazon_report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error requesting report: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            
            report.status = 'FAILED'
            report.error_message = str(e)
            report.save()
            
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
        
        url = f"https://advertising-api-eu.amazon.com/reporting/reports/{report.amazon_report_id}"
        
        # Get fresh access token
        access_token = AmazonAdsAuth.get_access_token(credential)
        
        # Create headers exactly like in the working implementation
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Amazon-Advertising-API-ClientId": credential.client_id,
            "Amazon-Advertising-API-Scope": credential.profile_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        try:
            response = requests.get(url, headers=headers)
            logger.debug(f"Status check response code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Error checking report status: {response.status_code} - {response.text}")
                return report
            
            result = response.json()
            logger.debug(f"Status check response: {result}")
            
            status = result.get('status')
            
            # Update report
            report.status = status
            
            if status == 'COMPLETED':
                # Look for download URL in various locations in the response
                download_url = None
                if 'location' in result:
                    download_url = result.get('location')
                elif 'url' in result:
                    download_url = result.get('url')
                
                # If we have a URL, save it
                if download_url:
                    report.download_url = download_url
                    logger.debug(f"Download URL found: {download_url}")
                else:
                    logger.error(f"Report is completed but no download URL found in response: {result}")
                
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
            logger.info(f"Starting download for report {report.id}")
            logger.info(f"Download URL: {report.download_url[:100]}...{report.download_url[-50:] if len(report.download_url) > 150 else ''}")
            
            # Download report with retry logic
            MAX_RETRIES = 3
            RETRY_BACKOFF = 2  # seconds
            retries = 0
            
            while retries < MAX_RETRIES:
                try:
                    # Set reasonable timeouts (connect_timeout, read_timeout)
                    logger.info(f"Download attempt {retries+1}/{MAX_RETRIES}")
                    response = requests.get(
                        report.download_url, 
                        timeout=(10, 300),  # 10s connect, 300s read
                        stream=True  # Use streaming to handle large files
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Failed to download report: {response.status_code} - {response.text}")
                        retries += 1
                        if retries >= MAX_RETRIES:
                            report.error_message = f"Download failed after {MAX_RETRIES} attempts: HTTP {response.status_code}"
                            report.save(update_fields=['error_message', 'updated_at'])
                            return False
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
                    logger.info(f"Successfully downloaded report: {total_size} bytes")
                    
                    # Check if we actually got any data
                    if total_size == 0:
                        report.error_message = "Downloaded file is empty (0 bytes)"
                        report.save(update_fields=['error_message', 'updated_at'])
                        return False
                    
                    # We've successfully downloaded the file, break out of retry loop
                    break
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, 
                        ConnectionResetError, ConnectionAbortedError) as conn_error:
                    retries += 1
                    logger.warning(f"Connection error during download (attempt {retries}/{MAX_RETRIES}): {str(conn_error)}")
                    if retries >= MAX_RETRIES:
                        logger.error(f"Max retries exceeded for downloading report")
                        report.error_message = f"Connection error: {str(conn_error)}"
                        report.save(update_fields=['error_message', 'updated_at'])
                        raise
                    time.sleep(RETRY_BACKOFF * retries)
            
            # Decompress and parse the report
            try:
                logger.info(f"Starting decompression for report {report.id}")
                compressed_data = content  # Use the streamed content
                # Try GZIP first
                try:
                    logger.debug("Attempting to decompress as GZIP")
                    # Use direct gzip decompression like in the working implementation
                    decompressed_data = gzip.decompress(compressed_data.getvalue()).decode('utf-8')
                    report_data = json.loads(decompressed_data)
                    logger.info(f"Successfully decompressed as GZIP and parsed report data: {len(report_data)} records")
                except Exception as gzip_error:
                    logger.debug(f"GZIP decompression failed: {str(gzip_error)}, trying ZIP format")
                    # Reset the file pointer
                    compressed_data.seek(0)
                    # Try regular ZIP
                    try:
                        logger.debug("Attempting to decompress as ZIP")
                        # Save content to temp file for debugging
                        with open("report_debug.zip", "wb") as f:
                            f.write(compressed_data.getvalue())
                        logger.debug("Saved compressed data to report_debug.zip for inspection")
                        
                        compressed_data.seek(0)
                        with zipfile.ZipFile(compressed_data) as zip_ref:
                            # Get the first file in the ZIP archive
                            file_name = zip_ref.namelist()[0]
                            logger.debug(f"Found file in ZIP: {file_name}")
                            with zip_ref.open(file_name) as file:
                                decompressed_data = file.read()
                                # Log the first part of the decompressed data
                                logger.debug(f"ZIP content preview: {decompressed_data[:200]}")
                                try:
                                    report_data = json.loads(decompressed_data)
                                    # Check if report_data is empty
                                    if isinstance(report_data, list) and len(report_data) == 0:
                                        logger.warning("ZIP contains valid JSON but the data array is empty")
                                    elif isinstance(report_data, dict) and len(report_data) == 0:
                                        logger.warning("ZIP contains valid JSON but the data object is empty")
                                    else:
                                        # Log data structure for debugging
                                        data_type = type(report_data).__name__
                                        if isinstance(report_data, list):
                                            logger.info(f"ZIP contains JSON array with {len(report_data)} items")
                                            if len(report_data) > 0:
                                                logger.info(f"First item structure: {json.dumps(report_data[0], indent=2)[:500]}...")
                                                logger.info(f"Keys in first item: {list(report_data[0].keys()) if isinstance(report_data[0], dict) else 'Not a dict'}")
                                        elif isinstance(report_data, dict):
                                            logger.info(f"ZIP contains JSON object with keys: {list(report_data.keys())}")
                                            # If 'data' field exists, log its structure
                                            if 'data' in report_data:
                                                data = report_data['data']
                                                logger.info(f"'data' field contains: {type(data).__name__}")
                                                if isinstance(data, list):
                                                    logger.info(f"'data' array length: {len(data)}")
                                                    if len(data) > 0:
                                                        logger.info(f"First item in 'data': {json.dumps(data[0], indent=2)[:500]}...")
                                    logger.info(f"Successfully decompressed as ZIP and parsed report data: {data_type} with {len(report_data) if isinstance(report_data, (list, dict)) else 'N/A'} items/keys")
                                except json.JSONDecodeError as json_error:
                                    logger.error(f"Error decoding JSON from ZIP: {str(json_error)}")
                                    logger.error(f"First 500 bytes of content: {decompressed_data[:500]}")
                                    report.error_message = f"JSON parsing error: {str(json_error)}"
                                    report.save(update_fields=['error_message', 'updated_at'])
                                    raise
                    except Exception as zip_error:
                        logger.error(f"ZIP decompression failed: {str(zip_error)}")
                        report.error_message = f"Decompression error: {str(zip_error)}"
                        report.save(update_fields=['error_message', 'updated_at'])
                        # Try direct JSON as last resort
                        try:
                            logger.debug("Attempting to parse as direct JSON")
                            compressed_data.seek(0)
                            raw_content = compressed_data.read().decode('utf-8')
                            report_data = json.loads(raw_content)
                            logger.info(f"Successfully parsed as direct JSON: {type(report_data).__name__}")
                        except Exception as json_error:
                            logger.error(f"Direct JSON parsing failed: {str(json_error)}")
                            report.error_message = f"All decompression methods failed. Last error: {str(json_error)}"
                            report.save(update_fields=['error_message', 'updated_at'])
                            raise Exception(f"Failed to decompress: GZIP error: {str(gzip_error)}, ZIP error: {str(zip_error)}, JSON error: {str(json_error)}")
            except Exception as e:
                logger.error(f"Error decompressing or parsing report data: {str(e)}")
                report.error_message = f"Processing error: {str(e)}"
                report.save(update_fields=['error_message', 'updated_at'])
                return False
            
            # Process based on report type
            logger.info(f"Starting data processing for report {report.id}")
            report_type_slug = report.report_type.slug
            logger.info(f"Processing report of type: {report_type_slug}")
            
            try:
                rows = 0
                if report_type_slug == 'daily-product-ads':
                    rows = cls._process_daily_product_ads_report(report, report_data)
                    logger.info(f"Processed {rows} rows for daily product ads report")
                elif report_type_slug == 'search-term':
                    rows = cls._process_search_term_report(report, report_data)
                    logger.info(f"Processed {rows} rows for search term report")
                else:
                    # Store raw data for report types without specific processors
                    rows = cls._process_generic_report(report, report_data)
                    logger.info(f"Stored raw data for {report_type_slug} report with {rows} records")
                
                if rows == 0:
                    logger.warning(f"Processed 0 rows for report {report.id}")
                
                # Mark report as stored
                report.is_stored = True
                report.save(update_fields=['is_stored', 'updated_at'])
                
                return True
                
            except Exception as e:
                logger.error(f"Error in report processing: {str(e)}")
                report.error_message = f"Data processing error: {str(e)}"
                report.save(update_fields=['error_message', 'updated_at'])
                return False
            
        except Exception as e:
            logger.error(f"Error downloading and processing report: {str(e)}")
            report.error_message = f"General error: {str(e)}"
            report.save(update_fields=['error_message', 'updated_at'])
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
        
        # Log detailed info about the input data
        logger.info(f"Processing data type: {type(report_data).__name__}")
        if isinstance(report_data, list):
            logger.info(f"Input data is a list with {len(report_data)} items")
        elif isinstance(report_data, dict):
            logger.info(f"Input data is a dict with keys: {list(report_data.keys())}")
        else:
            logger.info(f"Input data is of type {type(report_data).__name__}")
        
        # Handle different report data formats
        # Sometimes Amazon wraps the data in a 'result' field
        if isinstance(report_data, dict) and 'result' in report_data:
            logger.info(f"Unwrapping data from 'result' field: {type(report_data['result'])}")
            report_data = report_data['result']
            
        # Some API versions return a dictionary with a data array
        if isinstance(report_data, dict) and 'data' in report_data and isinstance(report_data['data'], list):
            logger.info(f"Unwrapping data from 'data' field: {len(report_data['data'])} records")
            report_data = report_data['data']
            
        # Handle case where report might contain a 'reports' array
        if isinstance(report_data, dict) and 'reports' in report_data and isinstance(report_data['reports'], list):
            logger.info(f"Unwrapping data from 'reports' field: {len(report_data['reports'])} reports")
            report_data = report_data['reports']

        # Handle case where data is in 'rows' field
        if isinstance(report_data, dict) and 'rows' in report_data and isinstance(report_data['rows'], list):
            logger.info(f"Unwrapping data from 'rows' field: {len(report_data['rows'])} rows")
            report_data = report_data['rows']
        
        # Handle case where data might be under 'response' and then 'data'
        if isinstance(report_data, dict) and 'response' in report_data and isinstance(report_data['response'], dict):
            logger.info("Found 'response' field in data")
            if 'data' in report_data['response'] and isinstance(report_data['response']['data'], list):
                logger.info(f"Unwrapping data from 'response.data' field: {len(report_data['response']['data'])} records")
                report_data = report_data['response']['data']
            
        # Handle empty data case
        if isinstance(report_data, list) and len(report_data) == 0:
            logger.info(f"Report data is an empty list")
            report.rows_processed = 0
            report.is_stored = True
            report.save(update_fields=['rows_processed', 'is_stored', 'updated_at'])
            return 0
            
        # Check report data format
        if not isinstance(report_data, list):
            logger.error(f"Unexpected report data format: {type(report_data)}, expected list")
            logger.error(f"Report data (truncated): {str(report_data)[:1000]}")
            report.error_message = f"Unexpected report data format: {type(report_data)}, expected list"
            report.save(update_fields=['error_message', 'updated_at'])
            return 0
            
        # Convert to DataFrame for easier processing
        try:
            df = pd.DataFrame(report_data)
            
            # Handle NaN values before database insertion
            # Replace NaN values with None for all numeric columns
            numeric_columns = df.select_dtypes(include=['float64', 'float32', 'int64', 'int32']).columns
            for col in numeric_columns:
                df[col] = df[col].replace([np.nan, np.inf, -np.inf], None)
            
            # Convert all numeric columns with NaN to appropriate values
            # For rate columns (percentages, etc.)
            rate_columns = [col for col in df.columns if 'rate' in col.lower() or col.lower().endswith('rate')]
            for col in rate_columns:
                if col in df.columns:
                    df[col] = df[col].fillna(0)
                    
            # For cost per click specifically which frequently has NaN
            if 'costPerClick' in df.columns:
                df['costPerClick'] = df['costPerClick'].fillna(0)
            
            if df.empty:
                logger.info(f"No data in report {report.id}")
                return 0
                
            logger.info(f"Report data has {len(df)} rows and {len(df.columns)} columns")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Show sample data (first row)
            if len(df) > 0:
                sample_row = df.iloc[0].to_dict()
                logger.info(f"Sample data: {sample_row}")
                
                # Special handling for potential nested data formats
                for key, value in sample_row.items():
                    if isinstance(value, (dict, list)):
                        logger.info(f"Found nested data in column '{key}': {value}")
                        
                # Convert nested 'metrics' dictionary if present
                if 'metrics' in df.columns and isinstance(df.iloc[0]['metrics'], dict):
                    logger.info("Unpacking nested metrics dictionary")
                    metrics_df = pd.json_normalize(df['metrics'])
                    df = pd.concat([df.drop('metrics', axis=1), metrics_df], axis=1)
                    logger.info(f"After unpacking: {len(df.columns)} columns: {list(df.columns)}")
        except Exception as e:
            logger.error(f"Error converting report data to DataFrame: {str(e)}")
            report.error_message = f"Error converting report data to DataFrame: {str(e)}"
            report.save(update_fields=['error_message', 'updated_at'])
            return 0
        
        # Track processing
        count = 0
        
        try:
            # Process in chunks to avoid memory issues with large reports
            chunk_size = 1000
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i:i+chunk_size]
                
                # Process each record in the chunk
                records = []
                for _, row in chunk.iterrows():
                    try:
                        # Get values, handling different possible column names
                        date_value = cls._get_value_with_fallbacks(row, ['date', 'reportDate', 'DATE'])
                        if date_value:
                            # Use the safe date parsing method
                            date_obj = cls._safe_parse_date(date_value)
                            if not date_obj:
                                logger.error(f"Could not parse date: {date_value}")
                                continue
                        else:
                            logger.error("No date field found in row")
                            continue
                            
                        # Create model instances but don't save yet
                        record = DailyProductAdsData(
                            tenant=tenant,
                            report=report,
                            date=date_obj,
                            portfolio_id=cls._get_value_with_fallbacks(row, ['portfolioId', 'portfolio_id', 'PORTFOLIO_ID']),
                            campaign_name=cls._get_value_with_fallbacks(row, ['campaignName', 'campaign_name', 'CAMPAIGN_NAME']),
                            campaign_id=cls._get_value_with_fallbacks(row, ['campaignId', 'campaign_id', 'CAMPAIGN_ID']),
                            ad_group_name=cls._get_value_with_fallbacks(row, ['adGroupName', 'ad_group_name', 'AD_GROUP_NAME']),
                            ad_group_id=cls._get_value_with_fallbacks(row, ['adGroupId', 'ad_group_id', 'AD_GROUP_ID']),
                            ad_id=cls._get_value_with_fallbacks(row, ['adId', 'ad_id', 'AD_ID']),
                            campaign_budget_type=cls._get_value_with_fallbacks(row, ['campaignBudgetType', 'campaign_budget_type']),
                            campaign_budget_amount=cls._get_value_with_fallbacks(row, ['campaignBudgetAmount', 'campaign_budget_amount']),
                            campaign_budget_currency_code=cls._get_value_with_fallbacks(row, ['campaignBudgetCurrencyCode', 'campaign_budget_currency_code']),
                            campaign_status=cls._get_value_with_fallbacks(row, ['campaignStatus', 'campaign_status']),
                            advertised_asin=cls._get_value_with_fallbacks(row, ['advertisedAsin', 'advertised_asin', 'ASIN']),
                            advertised_sku=cls._get_value_with_fallbacks(row, ['advertisedSku', 'advertised_sku', 'SKU']),
                            impressions=cls._get_value_with_fallbacks(row, ['impressions', 'IMPRESSIONS'], 0),
                            clicks=cls._get_value_with_fallbacks(row, ['clicks', 'CLICKS'], 0),
                            click_through_rate=cls._get_value_with_fallbacks(row, ['clickThroughRate', 'click_through_rate', 'CTR'], 0),
                            cost=cls._get_value_with_fallbacks(row, ['cost', 'COST'], 0),
                            # Handle NaN values that are particularly problematic
                            cost_per_click=0 if pd.isna(cls._get_value_with_fallbacks(row, ['costPerClick', 'cost_per_click', 'CPC'])) else cls._get_value_with_fallbacks(row, ['costPerClick', 'cost_per_click', 'CPC'], 0),
                            spend=cls._get_value_with_fallbacks(row, ['spend', 'SPEND'], 0),
                            units_sold_clicks_30d=cls._get_value_with_fallbacks(row, ['unitsSoldClicks30d', 'units_sold_clicks_30d'], 0),
                            units_sold_same_sku_30d=cls._get_value_with_fallbacks(row, ['unitsSoldSameSku30d', 'units_sold_same_sku_30d'], 0),
                            sales_1d=cls._get_value_with_fallbacks(row, ['sales1d', 'sales_1d', 'SALES_1D'], 0),
                            sales_7d=cls._get_value_with_fallbacks(row, ['sales7d', 'sales_7d', 'SALES_7D'], 0),
                            sales_14d=cls._get_value_with_fallbacks(row, ['sales14d', 'sales_14d', 'SALES_14D'], 0),
                            sales_30d=cls._get_value_with_fallbacks(row, ['sales30d', 'sales_30d', 'SALES_30D'], 0),
                            attributed_sales_same_sku_30d=cls._get_value_with_fallbacks(row, ['attributedSalesSameSku30d', 'attributed_sales_same_sku_30d'], 0),
                            purchases_1d=cls._get_value_with_fallbacks(row, ['purchases1d', 'purchases_1d'], 0),
                            purchases_7d=cls._get_value_with_fallbacks(row, ['purchases7d', 'purchases_7d'], 0),
                            purchases_14d=cls._get_value_with_fallbacks(row, ['purchases14d', 'purchases_14d'], 0),
                            purchases_30d=cls._get_value_with_fallbacks(row, ['purchases30d', 'purchases_30d'], 0),
                            purchases_same_sku_30d=cls._get_value_with_fallbacks(row, ['purchasesSameSku30d', 'purchases_same_sku_30d'], 0),
                            units_sold_other_sku_7d=cls._get_value_with_fallbacks(row, ['unitsSoldOtherSku7d', 'units_sold_other_sku_7d'], 0),
                            sales_other_sku_7d=cls._get_value_with_fallbacks(row, ['salesOtherSku7d', 'sales_other_sku_7d'], 0),
                        )
                        records.append(record)
                    except Exception as e:
                        logger.error(f"Error processing record: {str(e)}, row: {row}")
                
                if records:
                    # Bulk create records
                    with transaction.atomic():
                        try:
                            DailyProductAdsData.objects.bulk_create(
                                records, 
                                ignore_conflicts=True,  # Skip duplicates based on unique constraint
                                batch_size=100
                            )
                            
                            count += len(records)
                            logger.info(f"Processed {len(records)} daily product ads records for tenant {tenant.name}")
                        except Exception as e:
                            logger.error(f"Error bulk creating records: {str(e)}")
                            if 'records' in locals() and len(records) > 0:
                                logger.error(f"Sample record that failed: {records[0].__dict__}")
                                
                            # Fallback: Try to save records one by one to identify problematic records
                            logger.info("Attempting to save records individually as a fallback")
                            success_count = 0
                            for i, record in enumerate(records):
                                try:
                                    # Replace any problematic values with safe defaults
                                    # Specifically handle NaN in Decimal fields
                                    for field in ['cost_per_click', 'click_through_rate']:
                                        if hasattr(record, field) and pd.isna(getattr(record, field)):
                                            setattr(record, field, 0)
                                            
                                    record.save()
                                    success_count += 1
                                except Exception as single_error:
                                    logger.error(f"Error saving record {i}: {str(single_error)}")
                                    # Continue with next record
                            
                            count += success_count
                            logger.info(f"Saved {success_count} out of {len(records)} records individually")
            
            # Update report with count
            report.rows_processed = count
            report.save(update_fields=['rows_processed', 'updated_at'])
            
            return count
            
        except Exception as e:
            logger.error(f"Error in _process_daily_product_ads_report: {str(e)}")
            report.error_message = f"Error processing report: {str(e)}"
            report.save(update_fields=['error_message', 'updated_at'])
            return 0
    
    @staticmethod
    def _get_value_with_fallbacks(row, column_names, default=None):
        """Helper to get a value from a row with multiple possible column names"""
        for col in column_names:
            if col in row:
                # Return the value if it exists and is not None
                value = row[col]
                if value is not None:
                    return value
        return default
    
    @staticmethod
    def _safe_parse_date(date_value):
        """Safely parse date from various formats"""
        if not date_value:
            return None
            
        if isinstance(date_value, datetime):
            return date_value.date()
            
        if not isinstance(date_value, str):
            return None
            
        # Try different date formats
        date_formats = [
            '%Y-%m-%d',          # 2025-05-16
            '%Y-%m-%dT%H:%M:%S', # 2025-05-16T00:00:00
            '%Y-%m-%dT%H:%M:%SZ',# 2025-05-16T00:00:00Z
            '%Y%m%d',            # 20250516
            '%m/%d/%Y',          # 05/16/2025
            '%d/%m/%Y',          # 16/05/2025
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_value.split('.')[0], date_format).date()
            except (ValueError, AttributeError):
                continue
                
        return None
    
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
        
        # Check report data format
        if not isinstance(report_data, list):
            logger.error(f"Unexpected report data format: {type(report_data)}, expected list")
            report.error_message = f"Unexpected report data format: {type(report_data)}, expected list"
            report.save(update_fields=['error_message', 'updated_at'])
            return 0
            
        # Convert to DataFrame for easier processing
        try:
            df = pd.DataFrame(report_data)
            if df.empty:
                logger.info(f"No data in report {report.id}")
                return 0
                
            logger.info(f"Search term report data has {len(df)} rows and {len(df.columns)} columns")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Show sample data (first row)
            if len(df) > 0:
                sample_row = df.iloc[0].to_dict()
                logger.info(f"Sample data: {sample_row}")
        except Exception as e:
            logger.error(f"Error converting report data to DataFrame: {str(e)}")
            report.error_message = f"Error converting report data to DataFrame: {str(e)}"
            report.save(update_fields=['error_message', 'updated_at'])
            return 0
        
        # Track processing
        count = 0
        
        try:
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
                        logger.error(f"Error processing search term record: {str(e)}, row: {row}")
                
                if records:
                    # Bulk create records
                    with transaction.atomic():
                        try:
                            SearchTermReportData.objects.bulk_create(
                                records,
                                ignore_conflicts=True,  # Skip duplicates based on unique constraint
                                batch_size=100
                            )
                            
                            count += len(records)
                            logger.info(f"Processed {len(records)} search term records for tenant {tenant.name}")
                        except Exception as e:
                            logger.error(f"Error bulk creating search term records: {str(e)}")
                            if 'records' in locals() and len(records) > 0:
                                logger.error(f"Sample record that failed: {records[0].__dict__}")
            
            # Update report with count
            report.rows_processed = count
            report.save(update_fields=['rows_processed', 'updated_at'])
            
            return count
            
        except Exception as e:
            logger.error(f"Error in _process_search_term_report: {str(e)}")
            report.error_message = f"Error processing search term report: {str(e)}"
            report.save(update_fields=['error_message', 'updated_at'])
            return 0
    
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
    
    @classmethod
    def get_report_url(cls, credential, report_id):
        """
        Get report download URL with retries
        
        Args:
            credential: AmazonAdsCredential instance
            report_id: Amazon report ID
            
        Returns:
            Report download URL or None
        """
        url = f"https://advertising-api-eu.amazon.com/reporting/reports/{report_id}"
        
        # Get fresh access token
        access_token = AmazonAdsAuth.get_access_token(credential)
        
        # Create headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Amazon-Advertising-API-ClientId": credential.client_id,
            "Amazon-Advertising-API-Scope": credential.profile_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        report_url = None
        retry_count = 0
        max_retries = 5
        backoff_factor = 2
        
        while report_url is None and retry_count < max_retries:
            try:
                response = requests.get(url, headers=headers)
                logger.debug(f"Report URL fetch status code: {response.status_code}")
                
                if response.status_code == 429:  # Too Many Requests
                    retry_count += 1
                    wait_time = backoff_factor ** retry_count
                    logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                if response.status_code != 200:
                    logger.error(f"Failed to get report URL: {response.status_code} - {response.text}")
                    return None
                
                response_json = response.json()
                logger.debug(f"Report URL response: {response_json}")
                
                # Check for URL in different possible fields
                if 'location' in response_json:
                    report_url = response_json['location']
                elif 'url' in response_json:
                    report_url = response_json['url']
                
                if not report_url:
                    logger.warning("Report URL not found in response, waiting 60 seconds")
                    time.sleep(60)
            except Exception as e:
                logger.error(f"Error fetching report URL: {str(e)}")
                return None
        
        if report_url is None:
            logger.error("Max retries exceeded when fetching report URL")
        
        return report_url

    @classmethod
    def _process_generic_report(cls, report, report_data):
        """
        Process a generic report by storing its raw data
        
        Args:
            report: AdsReport instance
            report_data: JSON data from the report
            
        Returns:
            Number of records processed
        """
        # Log detailed info about the input data
        logger.info(f"Processing generic report data type: {type(report_data).__name__}")
        
        # Handle different data structures
        rows = 0
        if isinstance(report_data, list):
            rows = len(report_data)
            logger.info(f"Report contains a list with {rows} items")
            if rows > 0 and isinstance(report_data[0], dict):
                logger.info(f"Sample keys: {list(report_data[0].keys())}")
        elif isinstance(report_data, dict):
            logger.info(f"Report contains a dictionary with keys: {list(report_data.keys())}")
            # Check for data field which is common in some report formats
            if 'data' in report_data and isinstance(report_data['data'], list):
                rows = len(report_data['data'])
                logger.info(f"Found 'data' array with {rows} items")
        
        # Store statistics in the report model
        report.rows_processed = rows
        
        # We could store the raw data in a separate table if needed, but for now
        # we'll just mark it as stored
        report.is_stored = True
        report.save(update_fields=['rows_processed', 'is_stored', 'updated_at'])
        
        return rows 