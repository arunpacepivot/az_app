from django.db import models
import uuid
from django.utils import timezone

class AmazonSellerAccount(models.Model):
    """Model for tracking Amazon Seller accounts and their OAuth credentials"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller_id = models.CharField(max_length=255, unique=True)
    marketplace_id = models.CharField(max_length=50, null=True, blank=True)
    
    # Authentication
    auth_code = models.CharField(max_length=512, null=True, blank=True)
    access_token = models.CharField(max_length=2048)
    refresh_token = models.CharField(max_length=2048)
    token_type = models.CharField(max_length=50, default="bearer")
    
    # Token lifecycle management
    token_expires_at = models.DateTimeField()
    last_refreshed_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Region selection for API endpoints
    REGION_CHOICES = [
        ('NA', 'North America'),
        ('EU', 'Europe'),
        ('FE', 'Far East'),
    ]
    region = models.CharField(max_length=2, choices=REGION_CHOICES, default='FE')  # Default to FE for India
    
    class Meta:
        verbose_name = "Amazon Seller Account"
        verbose_name_plural = "Amazon Seller Accounts"
        indexes = [
            models.Index(fields=['seller_id']),
            models.Index(fields=['token_expires_at']),
        ]
    
    def __str__(self):
        return f"Seller: {self.seller_id}"
    
    def is_token_expired(self):
        """Check if the access token is expired or about to expire (within 5 minutes)"""
        buffer_time = timezone.timedelta(minutes=5)
        return self.token_expires_at <= timezone.now() + buffer_time
