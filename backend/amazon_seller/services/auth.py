"""
Amazon Seller OAuth authentication service
"""
import requests
import datetime
import logging
import uuid

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class AmazonAuthService:
    """Service for handling Amazon Seller OAuth authentication flow"""
    
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
        'EU': 'https://eu.amazon.com/ap/oa',
        'FE': 'https://apac.amazon.com/ap/oa',
    }
    
    # Advertising API token endpoints (same as regular OAuth)
    ADVERTISING_TOKEN_ENDPOINTS = {
        'NA': 'https://api.amazon.com/auth/o2/token',
        'EU': 'https://api.amazon.co.uk/auth/o2/token',
        'FE': 'https://api.amazon.co.jp/auth/o2/token',
    }
    
    @classmethod
    def get_authorization_url(cls, region='EU', state=None):
        """
        Generate the Amazon LWA authorization URL
        
        Args:
            region: The Amazon region (NA, EU, FE, IN)
            state: State parameter for CSRF protection
            
        Returns:
            The authorization URL
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
        auth_url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        logger.info(f"Generated Amazon authorization URL for region {region}")
        
        return auth_url, state
    
    @classmethod
    def get_advertising_authorization_url(cls, region='EU', state=None, scopes=None):
        """
        Generate the Amazon Advertising API authorization URL
        
        Args:
            region: The Amazon region (NA, EU, FE)
            state: State parameter for CSRF protection
            scopes: List of advertising API scopes to request
            
        Returns:
            The authorization URL and state
        """
        base_url = cls.ADVERTISING_AUTH_ENDPOINTS.get(region)
        
        if not state:
            state = str(uuid.uuid4())
            
        # Default scopes for advertising if none provided
        if not scopes:
            scopes = ['advertising::campaign_management']
            
        # Join multiple scopes with spaces
        scope_string = ' '.join(scopes)
            
        params = {
            'client_id': settings.AMAZON_CLIENT_ID,
            'scope': scope_string,
            'response_type': 'code',
            'redirect_uri': settings.AMAZON_REDIRECT_URI,
            'state': state
        }
        
        # Create URL with query parameters
        auth_url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        logger.info(f"Generated Amazon Advertising authorization URL for region {region}")
        
        return auth_url, state
    
    @classmethod
    def exchange_code_for_tokens(cls, auth_code, region='EU'):
        """
        Exchange authorization code for access and refresh tokens
        
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
        url = cls.ADVERTISING_TOKEN_ENDPOINTS.get(region)
        
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
            
            logger.info(f"Successfully exchanged Advertising auth code for tokens")
            
            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data['refresh_token'],
                'token_type': token_data['token_type'],
                'token_expires_at': token_expires_at
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exchanging Advertising auth code for tokens: {str(e)}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    @classmethod
    def refresh_access_token(cls, refresh_token, region='EU'):
        """
        Get a new access token using the refresh token
        
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