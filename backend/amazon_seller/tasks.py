"""
Celery tasks for Amazon Seller OAuth
"""
import logging
from celery import shared_task
from .services.token_manager import TokenManager

logger = logging.getLogger(__name__)

@shared_task
def refresh_amazon_tokens():
    """
    Task to refresh all Amazon Seller tokens that will expire soon
    Should be scheduled to run periodically (e.g., every 15 minutes)
    """
    logger.info("Starting scheduled Amazon token refresh task")
    results = TokenManager.refresh_all_expiring_tokens()
    logger.info(f"Completed token refresh task: {results}")
    return results 