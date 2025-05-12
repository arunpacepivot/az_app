"""
Amazon SP API Authentication Service
"""
import requests
import datetime
import logging
from django.conf import settings
from django.utils import timezone

from .models import AmazonSPApiToken

logger = logging.getLogger(__name__)

class SPApiAuthService:
    """Service for handling Amazon SP API authentication"""
    
    # Token endpoints for different regions
    TOKEN_ENDPOINTS = {
        'NA': 'https://api.amazon.com/auth/o2/token',
        'EU': 'https://api.amazon.co.uk/auth/o2/token',
        'FE': 'https://api.amazon.co.jp/auth/o2/token',
    }
    
    @classmethod
    def get_access_token(cls, client_id=None, client_secret=None, refresh_token=None, region='EU'):
        """
        Get or refresh an access token using the refresh token
        
        Args:
            client_id: The LWA client ID (optional if using token from DB)
            client_secret: The LWA client secret (optional if using token from DB)
            refresh_token: The refresh token (optional if using token from DB)
            region: The Amazon region (NA, EU, FE)
            
        Returns:
            The access token
        """
        # If no token info provided, try to get from database
        if not (client_id and client_secret and refresh_token):
            token_obj = AmazonSPApiToken.objects.filter(is_active=True).first()
            if token_obj:
                client_id = token_obj.client_id
                client_secret = token_obj.client_secret
                refresh_token = token_obj.refresh_token
                region = token_obj.region
                
                # Check if token is still valid
                if token_obj.access_token and not token_obj.is_expired:
                    logger.info(f"Using existing token that expires at {token_obj.token_expires_at}")
                    return token_obj.access_token
            else:
                raise ValueError("No token info provided and no active token found in database")
        
        # If we get here, we need to refresh the token
        url = cls.TOKEN_ENDPOINTS.get(region)
        if not url:
            raise ValueError(f"Invalid region: {region}")
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            # Calculate token expiration (typically 1 hour)
            expires_in = token_data.get('expires_in', 3600)
            token_expires_at = timezone.now() + datetime.timedelta(seconds=expires_in)
            
            access_token = token_data['access_token']
            
            # Update or create token record in database
            token_obj, created = AmazonSPApiToken.objects.update_or_create(
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token,
                defaults={
                    'access_token': access_token,
                    'token_expires_at': token_expires_at,
                    'region': region,
                    'is_active': True
                }
            )
            
            logger.info(f"{'Created' if created else 'Updated'} SP-API token that expires at {token_expires_at}")
            
            return access_token
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing token: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    @classmethod
    def get_restricted_data_token(cls, access_token, restricted_resources):
        """
        Get a Restricted Data Token (RDT) for accessing restricted resources
        
        Args:
            access_token: The LWA access token
            restricted_resources: List of restricted resource objects
            
        Returns:
            The restricted data token
        """
        url = "https://sellingpartnerapi-eu.amazon.com/tokens/2021-03-01/restrictedDataToken"
        
        headers = {
            "Content-Type": "application/json",
            "x-amz-access-token": access_token
        }
        
        data = {
            "restrictedResources": restricted_resources
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            token_data = response.json()
            
            logger.info(f"Successfully obtained restricted data token")
            
            return token_data.get('restrictedDataToken')
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting restricted data token: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise 