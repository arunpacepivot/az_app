"""
Serializers for Amazon SP API authentication models
"""
from rest_framework import serializers
from .models import AmazonSPApiToken

class AmazonSPApiTokenSerializer(serializers.ModelSerializer):
    """Serializer for AmazonSPApiToken model"""
    class Meta:
        model = AmazonSPApiToken
        fields = [
            'id', 'client_id', 'client_secret', 'refresh_token', 
            'access_token', 'token_expires_at', 'region', 
            'is_active', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'client_secret': {'write_only': True},
            'refresh_token': {'write_only': True},
            'access_token': {'read_only': True},
            'token_expires_at': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        } 