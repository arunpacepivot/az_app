"""
Utility functions for Amazon SP API
"""
import logging
from .auth_service import SPApiAuthService
from .sp_api_client import SPApiClient

logger = logging.getLogger(__name__)

def get_access_token():
    """
    Simple utility function to get an access token
    
    Returns:
        str: The access token
    """
    return SPApiAuthService.get_access_token()

def get_restricted_data_token(restricted_resources):
    """
    Get a Restricted Data Token for accessing protected resources
    
    Args:
        restricted_resources (list): List of restricted resource objects
            Example: [
                {
                    "method": "GET",
                    "path": "/orders/v0/orders"
                }
            ]
    
    Returns:
        str: The restricted data token
    """
    access_token = get_access_token()
    return SPApiAuthService.get_restricted_data_token(access_token, restricted_resources)

def get_client(region='EU'):
    """
    Get a configured SP API client
    
    Args:
        region (str): The Amazon region (NA, EU, FE)
    
    Returns:
        SPApiClient: The configured client
    """
    return SPApiClient(region=region)

# Simple convenience functions for common API operations

def get_orders(marketplace_ids=None, created_after=None, created_before=None, 
               order_statuses=None, region='EU'):
    """
    Get orders from the Orders API
    
    Args:
        marketplace_ids (list): List of marketplace IDs
        created_after (str): ISO 8601 timestamp for order creation date lower bound
        created_before (str): ISO 8601 timestamp for order creation date upper bound
        order_statuses (list): List of order statuses to filter by
        region (str): The Amazon region (NA, EU, FE)
    
    Returns:
        dict: The API response with orders
    """
    client = get_client(region)
    
    # Set up query parameters
    params = {}
    if marketplace_ids:
        params['MarketplaceIds'] = ','.join(marketplace_ids)
    if created_after:
        params['CreatedAfter'] = created_after
    if created_before:
        params['CreatedBefore'] = created_before
    if order_statuses:
        params['OrderStatuses'] = ','.join(order_statuses)
    
    # Define restricted resources for RDT
    restricted_resources = [
        {
            "method": "GET",
            "path": "/orders/v0/orders"
        }
    ]
    
    # Make the API call with RDT
    return client.get(
        '/orders/v0/orders', 
        params=params, 
        use_rdt=True, 
        restricted_resources=restricted_resources
    )

def get_order_items(order_id, region='EU'):
    """
    Get order items for a specific order
    
    Args:
        order_id (str): The Amazon order ID
        region (str): The Amazon region (NA, EU, FE)
    
    Returns:
        dict: The API response with order items
    """
    client = get_client(region)
    
    # Define restricted resources for RDT
    restricted_resources = [
        {
            "method": "GET",
            "path": f"/orders/v0/orders/{order_id}/orderItems"
        }
    ]
    
    # Make the API call with RDT
    return client.get(
        f'/orders/v0/orders/{order_id}/orderItems', 
        use_rdt=True, 
        restricted_resources=restricted_resources
    ) 