from rest_framework import serializers
from .models import ErrorLog

class ErrorLogSerializer(serializers.ModelSerializer):
    """
    Serializer for the ErrorLog model.
    """
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = ErrorLog
        fields = '__all__'
        read_only_fields = ['id', 'timestamp'] 