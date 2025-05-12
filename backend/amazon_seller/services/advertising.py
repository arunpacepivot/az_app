"""
Amazon Advertising API service
"""
import requests
import logging
import json
from django.conf import settings
from django.utils import timezone

from ..models import AmazonAdvertisingAccount
from .auth import AmazonAuthService

logger = logging.getLogger(__name__)

class AmazonAdvertisingService:
    """Service for interacting with Amazon Advertising API"""
    
    @classmethod
    def _get_headers(cls, account, profile_id=None):
        """
        Construct headers for Amazon Advertising API requests
        
        Args:
            account: AmazonAdvertisingAccount instance
            profile_id: Optional profile ID to include in the headers
            
        Returns:
            Dict with request headers
        """
        headers = {
            'Authorization': f"Bearer {account.access_token}",
            'Content-Type': 'application/json',
            'Amazon-Advertising-API-ClientId': settings.AMAZON_CLIENT_ID
        }
        
        if profile_id:
            headers['Amazon-Advertising-API-Scope'] = profile_id
            
        return headers
    
    @classmethod
    def _ensure_fresh_token(cls, account):
        """
        Ensure the account has a fresh access token
        
        Args:
            account: AmazonAdvertisingAccount instance
            
        Returns:
            AmazonAdvertisingAccount with refreshed token (if needed)
        """
        if account.is_token_expired():
            logger.info(f"Refreshing expired token for advertising account {account.profile_id}")
            
            try:
                token_data = AmazonAuthService.refresh_access_token(
                    account.refresh_token, 
                    region=account.region
                )
                
                # Update account with new token data
                account.access_token = token_data['access_token']
                account.token_expires_at = token_data['token_expires_at']
                account.save(update_fields=['access_token', 'token_expires_at', 'updated_at'])
                
                logger.info(f"Successfully refreshed token for advertising account {account.profile_id}")
            except Exception as e:
                logger.error(f"Failed to refresh token: {str(e)}")
                
        return account
    
    @classmethod
    def _get_api_endpoint(cls, account):
        """
        Get the appropriate API endpoint for the account's region
        
        Args:
            account: AmazonAdvertisingAccount instance
            
        Returns:
            API endpoint URL
        """
        return AmazonAuthService.ADVERTISING_API_ENDPOINTS.get(account.region)
    
    @classmethod
    def get_profiles(cls, account):
        """
        Get available advertising profiles
        
        Args:
            account: AmazonAdvertisingAccount instance
            
        Returns:
            List of advertising profiles
        """
        account = cls._ensure_fresh_token(account)
        
        base_url = cls._get_api_endpoint(account)
        url = f"{base_url}/v2/profiles"
        
        headers = cls._get_headers(account)
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting profiles: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    @classmethod
    def get_campaigns(cls, account, profile_id, state_filter=None, campaign_type=None):
        """
        Get campaigns for a specific profile
        
        Args:
            account: AmazonAdvertisingAccount instance
            profile_id: The advertising profile ID
            state_filter: Optional campaign state filter
            campaign_type: Optional campaign type filter
            
        Returns:
            List of campaigns
        """
        account = cls._ensure_fresh_token(account)
        
        base_url = cls._get_api_endpoint(account)
        url = f"{base_url}/v2/campaigns"
        
        params = {}
        if state_filter:
            params['stateFilter'] = state_filter
        if campaign_type:
            params['campaignType'] = campaign_type
            
        headers = cls._get_headers(account, profile_id)
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting campaigns: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    @classmethod
    def create_campaign(cls, account, profile_id, campaign_data):
        """
        Create a new advertising campaign
        
        Args:
            account: AmazonAdvertisingAccount instance
            profile_id: The advertising profile ID
            campaign_data: Campaign data dictionary
            
        Returns:
            Created campaign data
        """
        account = cls._ensure_fresh_token(account)
        
        base_url = cls._get_api_endpoint(account)
        url = f"{base_url}/v2/campaigns"
        
        headers = cls._get_headers(account, profile_id)
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                data=json.dumps(campaign_data)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating campaign: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    @classmethod
    def update_campaign(cls, account, profile_id, campaign_id, campaign_data):
        """
        Update an existing advertising campaign
        
        Args:
            account: AmazonAdvertisingAccount instance
            profile_id: The advertising profile ID
            campaign_id: The campaign ID to update
            campaign_data: Campaign data dictionary
            
        Returns:
            Update result
        """
        account = cls._ensure_fresh_token(account)
        
        base_url = cls._get_api_endpoint(account)
        url = f"{base_url}/v2/campaigns/{campaign_id}"
        
        headers = cls._get_headers(account, profile_id)
        
        try:
            response = requests.put(
                url, 
                headers=headers, 
                data=json.dumps(campaign_data)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating campaign: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    @classmethod
    def get_ad_groups(cls, account, profile_id, campaign_id=None, state_filter=None):
        """
        Get ad groups for a profile or campaign
        
        Args:
            account: AmazonAdvertisingAccount instance
            profile_id: The advertising profile ID
            campaign_id: Optional campaign ID filter
            state_filter: Optional ad group state filter
            
        Returns:
            List of ad groups
        """
        account = cls._ensure_fresh_token(account)
        
        base_url = cls._get_api_endpoint(account)
        url = f"{base_url}/v2/ad-groups"
        
        params = {}
        if campaign_id:
            params['campaignIdFilter'] = campaign_id
        if state_filter:
            params['stateFilter'] = state_filter
            
        headers = cls._get_headers(account, profile_id)
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting ad groups: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    @classmethod
    def create_ad_group(cls, account, profile_id, ad_group_data):
        """
        Create a new ad group
        
        Args:
            account: AmazonAdvertisingAccount instance
            profile_id: The advertising profile ID
            ad_group_data: Ad group data dictionary
            
        Returns:
            Created ad group data
        """
        account = cls._ensure_fresh_token(account)
        
        base_url = cls._get_api_endpoint(account)
        url = f"{base_url}/v2/ad-groups"
        
        headers = cls._get_headers(account, profile_id)
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                data=json.dumps(ad_group_data)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating ad group: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    @classmethod
    def get_reports(cls, account, profile_id, report_type, metrics, start_date, end_date, segment=None):
        """
        Generate a report from the Advertising API
        
        Args:
            account: AmazonAdvertisingAccount instance
            profile_id: The advertising profile ID
            report_type: The type of report to generate (campaigns, adGroups, etc.)
            metrics: List of metrics to include in the report
            start_date: Report start date (YYYYMMDD format)
            end_date: Report end date (YYYYMMDD format)
            segment: Optional segment to group by
            
        Returns:
            Report data or download URL
        """
        account = cls._ensure_fresh_token(account)
        
        base_url = cls._get_api_endpoint(account)
        url = f"{base_url}/v2/reports"
        
        report_data = {
            "reportDate": end_date,
            "metrics": ",".join(metrics) if isinstance(metrics, list) else metrics
        }
        
        if segment:
            report_data["segment"] = segment
            
        headers = cls._get_headers(account, profile_id)
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                data=json.dumps(report_data)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating report: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise 