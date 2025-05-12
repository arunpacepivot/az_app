"""
Amazon OAuth authentication service for Seller and Advertising APIs
"""
import requests
import datetime
import logging
import uuid
import json
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone

from ..models import AmazonSellerAccount, AmazonAdvertisingAccount

logger = logging.getLogger(__name__)

class AmazonAuthService:
    """Service for handling Amazon OAuth authentication flows for both Seller and Advertising APIs"""
    
    # Token endpoints for different regions
    TOKEN_ENDPOINTS = {
        'NA': 'https://api.amazon.com/auth/o2/token',
        'EU': 'https://api.amazon.co.uk/auth/o2/token',
        'FE': 'https://api.amazon.co.jp/auth/o2/token',
        'IN': 'https://api.amazon.in/auth/o2/token'  # India-specific token endpoint
    }
    
    # Authorization endpoints for different regions
    AUTH_ENDPOINTS = {
        'NA': 'https://sellercentral.amazon.com/apps/authorize/consent',
        'EU': 'https://sellercentral-europe.amazon.com/apps/authorize/consent',
        'FE': 'https://sellercentral-japan.amazon.com/apps/authorize/consent',
        'IN': 'https://sellercentral.amazon.in/apps/authorize/consent'  # India-specific auth endpoint
    }
    
    # Advertising API authorization endpoints
    ADVERTISING_AUTH_ENDPOINTS = {
        'NA': 'https://www.amazon.com/ap/oa',
        'EU': 'https://eu.account.amazon.com/ap/oa',
        'FE': 'https://apac.account.amazon.com/ap/oa',
    }
    
    # Amazon Advertising API endpoints
    ADVERTISING_API_ENDPOINTS = {
        'NA': 'https://advertising-api.amazon.com',
        'EU': 'https://advertising-api-eu.amazon.com',
        'FE': 'https://advertising-api-fe.amazon.com',
    }
    
    # Default advertising API scopes
    DEFAULT_ADVERTISING_SCOPES = [
        'advertising::campaign_management',
        'advertising::sponsored_ads'
    ]
    
    @classmethod
    def get_authorization_url(cls, region='EU', state=None):
        """
        Generate the Amazon LWA authorization URL for Seller API
        
        Args:
            region: The Amazon region (NA, EU, FE, IN)
            state: State parameter for CSRF protection
            
        Returns:
            The authorization URL and state
        """
        base_url = cls.AUTH_ENDPOINTS.get(region)
        
        if not state:
            state = str(uuid.uuid4())
            
        params = {
            'application_id': settings.AMAZON_CLIENT_ID,
            'redirect_uri': settings.AMAZON_REDIRECT_URI,
            'state': state,
            'version': 'beta'  # Add version=beta for draft applications
        }
        
        # Create URL with query parameters
        logger.info(f"Params: {params}")
        auth_url = f"{base_url}?{urlencode(params)}"
        logger.info(f"Generated Amazon authorization URL for region {region}")
        logger.info(f"Auth URL: {auth_url}")
        return auth_url, state
    
    @classmethod
    def get_advertising_authorization_url(cls, region='EU', state=None, scopes=None, user_id=None):
        """
        Generate the Amazon Advertising API authorization URL
        
        Args:
            region: The Amazon region (NA, EU, FE)
            state: State parameter for CSRF protection
            scopes: List of advertising API scopes to request
            user_id: Optional user ID to include in state parameter for mapping user on callback
            
        Returns:
            The authorization URL and state
        """
        base_url = cls.ADVERTISING_AUTH_ENDPOINTS.get(region)
        
        if not state:
            # If user_id is provided, include it in the state for mapping
            if user_id:
                state_data = {
                    'uuid': str(uuid.uuid4()),
                    'user_id': str(user_id)
                }
                state = json.dumps(state_data)
            else:
                state = str(uuid.uuid4())
            
        # Default scopes for advertising if none provided
        if not scopes:
            scopes = cls.DEFAULT_ADVERTISING_SCOPES
            
        # Join multiple scopes with spaces
        scope_string = ' '.join(scopes)
            
        params = {
            'client_id': settings.AMAZON_CLIENT_ID,
            'scope': scope_string,
            'response_type': 'code',
            'redirect_uri': settings.AMAZON_ADVERTISING_REDIRECT_URI,
            'state': state
        }
        
        # Create URL with query parameters
        logger.info(f"Params Advertising: {params}")
        auth_url = f"{base_url}?{urlencode(params)}"
        logger.info(f"Generated Amazon Advertising authorization URL for region {region}")
        logger.info(f"Auth URL Advertising: {auth_url}")
        return auth_url, state
    
    @classmethod
    def exchange_code_for_tokens(cls, auth_code, region='EU'):
        """
        Exchange authorization code for access and refresh tokens for Seller API
        
        Args:
            auth_code: The authorization code from callback
            region: The Amazon region (NA, EU, FE, IN)
            
        Returns:
            Dict with token information
        """
        url = cls.TOKEN_ENDPOINTS.get(region)
        
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': settings.AMAZON_REDIRECT_URI,
            'client_id': settings.AMAZON_CLIENT_ID,
            'client_secret': settings.AMAZON_CLIENT_SECRET
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            # Calculate token expiration
            expires_in = token_data.get('expires_in', 3600)
            token_expires_at = timezone.now() + datetime.timedelta(seconds=expires_in)
            
            logger.info(f"Successfully exchanged auth code for tokens")
            
            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data['refresh_token'],
                'token_type': token_data['token_type'],
                'token_expires_at': token_expires_at
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exchanging auth code for tokens: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    @classmethod
    def exchange_advertising_code_for_tokens(cls, auth_code, region='EU'):
        """
        Exchange authorization code for access and refresh tokens for Advertising API
        
        Args:
            auth_code: The authorization code from callback
            region: The Amazon region (NA, EU, FE)
            
        Returns:
            Dict with token information
        """
        url = cls.TOKEN_ENDPOINTS.get(region)
        
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': settings.AMAZON_ADVERTISING_REDIRECT_URI,
            'client_id': settings.AMAZON_CLIENT_ID,
            'client_secret': settings.AMAZON_CLIENT_SECRET
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            # Calculate token expiration
            expires_in = token_data.get('expires_in', 3600)
            token_expires_at = timezone.now() + datetime.timedelta(seconds=expires_in)
            
            # Store the actual scope that was granted
            granted_scopes = token_data.get('scope', '')
            
            logger.info(f"Successfully exchanged Advertising auth code for tokens")
            
            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data['refresh_token'],
                'token_type': token_data['token_type'],
                'token_expires_at': token_expires_at,
                'scopes': granted_scopes
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exchanging Advertising auth code for tokens: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    @classmethod
    def refresh_access_token(cls, refresh_token, region='EU'):
        """
        Get a new access token using the refresh token (works for both Seller and Advertising APIs)
        
        Args:
            refresh_token: The refresh token
            region: The Amazon region (NA, EU, FE, IN)
            
        Returns:
            Dict with new token information
        """
        url = cls.TOKEN_ENDPOINTS.get(region)
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': settings.AMAZON_CLIENT_ID,
            'client_secret': settings.AMAZON_CLIENT_SECRET
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            # Calculate token expiration
            expires_in = token_data.get('expires_in', 3600)
            token_expires_at = timezone.now() + datetime.timedelta(seconds=expires_in)
            
            logger.info(f"Successfully refreshed access token")
            
            return {
                'access_token': token_data['access_token'],
                'token_type': token_data['token_type'],
                'token_expires_at': token_expires_at
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    @classmethod
    def get_advertising_profiles(cls, access_token, region='EU'):
        """
        Get Amazon Advertising API profiles
        
        Args:
            access_token: The access token
            region: The Amazon region (NA, EU, FE)
            
        Returns:
            List of profile objects
        """
        base_url = cls.ADVERTISING_API_ENDPOINTS.get(region)
        url = f"{base_url}/v2/profiles"
        
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Content-Type': 'application/json',
            'Amazon-Advertising-API-ClientId': settings.AMAZON_CLIENT_ID
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            profiles = response.json()
            
            logger.info(f"Successfully retrieved {len(profiles)} advertising profiles")
            return profiles
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting advertising profiles: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise 