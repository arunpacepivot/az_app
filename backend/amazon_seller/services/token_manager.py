"""
Service for managing Amazon Seller OAuth tokens
"""
import logging
from django.utils import timezone
from ..models import AmazonSellerAccount
from .auth import AmazonAuthService

logger = logging.getLogger(__name__)

class TokenManager:
    """Manages the lifecycle of Amazon Seller OAuth tokens"""
    
    @classmethod
    def get_valid_token(cls, seller_id):
        """
        Get a valid access token for the given seller ID.
        If token is expired, automatically refresh it.
        
        Args:
            seller_id: The Amazon seller ID
            
        Returns:
            Valid access token
            
        Raises:
            ValueError: If no active seller account found
        """
        try:
            account = AmazonSellerAccount.objects.get(seller_id=seller_id, is_active=True)
            
            # Check if token is expired or about to expire
            if account.is_token_expired():
                cls.refresh_token(account)
                
            return account.access_token
            
        except AmazonSellerAccount.DoesNotExist:
            logger.error(f"No active Amazon seller account found for seller ID: {seller_id}")
            raise ValueError(f"No active Amazon seller account found for seller ID: {seller_id}")
    
    @classmethod
    def refresh_token(cls, account):
        """
        Refresh access token for an account and update the database
        
        Args:
            account: AmazonSellerAccount instance
            
        Returns:
            bool: Success or failure
        """
        try:
            token_data = AmazonAuthService.refresh_access_token(
                account.refresh_token, 
                region=account.region
            )
            
            # Update the account with new token information
            account.access_token = token_data['access_token']
            account.token_type = token_data['token_type']
            account.token_expires_at = token_data['token_expires_at']
            account.save()
            
            logger.info(f"Token refreshed for seller {account.seller_id}")
            return True
        except Exception as e:
            logger.error(f"Error refreshing token for seller {account.seller_id}: {str(e)}")
            return False
    
    @classmethod
    def refresh_all_expiring_tokens(cls):
        """
        Refresh all tokens that will expire within 30 minutes
        
        Returns:
            Dict with refresh statistics
        """
        expiry_threshold = timezone.now() + timezone.timedelta(minutes=30)
        expiring_accounts = AmazonSellerAccount.objects.filter(
            token_expires_at__lte=expiry_threshold,
            is_active=True
        )
        
        logger.info(f"Found {expiring_accounts.count()} accounts with expiring tokens")
        
        success_count = 0
        for account in expiring_accounts:
            if cls.refresh_token(account):
                success_count += 1
                
        results = {
            'total': expiring_accounts.count(),
            'success': success_count,
            'failed': expiring_accounts.count() - success_count
        }
        
        logger.info(f"Token refresh results: {results}")
        return results 