from django.db import models
from django.utils import timezone

class AmazonSPApiToken(models.Model):
    """Model to store Amazon SP-API OAuth tokens"""
    client_id = models.CharField(max_length=200)
    client_secret = models.CharField(max_length=200)
    refresh_token = models.TextField()
    access_token = models.TextField(blank=True, null=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    region = models.CharField(max_length=5, default='EU', choices=[
        ('NA', 'North America'),
        ('EU', 'Europe'),
        ('FE', 'Far East'),
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SP-API Token: {self.client_id[:8]}..."

    @property
    def is_expired(self):
        """Check if the token is expired"""
        if not self.token_expires_at:
            return True
        return self.token_expires_at <= timezone.now() 