"""
Amazon SP API Client
"""
import logging
import requests
import json
from .auth_service import SPApiAuthService

logger = logging.getLogger(__name__)

class SPApiClient:
    """Client for making Amazon SP API requests with automatic authentication"""
    
    # Base endpoints for different regions
    BASE_ENDPOINTS = {
        'NA': 'https://sellingpartnerapi-na.amazon.com',
        'EU': 'https://sellingpartnerapi-eu.amazon.com',
        'FE': 'https://sellingpartnerapi-fe.amazon.com',
    }
    
    def __init__(self, region='EU'):
        """Initialize the client with a region"""
        self.region = region
        self.base_url = self.BASE_ENDPOINTS.get(region)
        if not self.base_url:
            raise ValueError(f"Invalid region: {region}")
    
    def get_headers(self, access_token=None, restricted_data_token=None):
        """Get the headers for API requests"""
        if not access_token:
            access_token = SPApiAuthService.get_access_token()
        
        headers = {
            'Content-Type': 'application/json',
            'x-amz-access-token': restricted_data_token if restricted_data_token else access_token
        }
        
        return headers
    
    def get_url(self, path):
        """Get the full URL for an API path"""
        # Ensure path starts with /
        if not path.startswith('/'):
            path = f"/{path}"
            
        return f"{self.base_url}{path}"
    
    def request(self, method, path, params=None, data=None, json_data=None, 
                access_token=None, use_rdt=False, restricted_resources=None):
        """
        Make a request to the SP API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /orders/v0/orders)
            params: Query parameters
            data: Form data
            json_data: JSON data (for POST/PUT requests)
            access_token: Optional access token (will be fetched if not provided)
            use_rdt: Whether to use a Restricted Data Token
            restricted_resources: List of restricted resources (required if use_rdt=True)
            
        Returns:
            Response object
        """
        # Get the access token if not provided
        if not access_token:
            access_token = SPApiAuthService.get_access_token()
        
        # If Restricted Data Token is needed
        restricted_data_token = None
        if use_rdt:
            if not restricted_resources:
                raise ValueError("Restricted resources required for RDT")
                
            restricted_data_token = SPApiAuthService.get_restricted_data_token(
                access_token, restricted_resources
            )
        
        # Prepare headers and URL
        headers = self.get_headers(access_token, restricted_data_token)
        url = self.get_url(path)
        
        # Log the request
        logger.info(f"Making {method} request to {url}")
        
        # Make the request
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data
            )
            
            # Raise exception for 4XX/5XX responses
            response.raise_for_status()
            
            # Try to parse as JSON
            if response.content:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return response.content
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            raise
    
    def get(self, path, params=None, **kwargs):
        """Make a GET request to the SP API"""
        return self.request('GET', path, params=params, **kwargs)
    
    def post(self, path, json_data=None, **kwargs):
        """Make a POST request to the SP API"""
        return self.request('POST', path, json_data=json_data, **kwargs)
    
    def put(self, path, json_data=None, **kwargs):
        """Make a PUT request to the SP API"""
        return self.request('PUT', path, json_data=json_data, **kwargs)
    
    def delete(self, path, **kwargs):
        """Make a DELETE request to the SP API"""
        return self.request('DELETE', path, **kwargs) 