from django.db import models
import uuid

class ErrorLog(models.Model):
    """
    Model for storing error logs from various components of the application.
    """
    ERROR_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]

    SOURCE_TYPES = [
        ('SP', 'Sponsored Products'),
        ('SB', 'Sponsored Brands'),
        ('SD', 'Sponsored Display'),
        ('SQP', 'SQP'),
        ('LISTENER', 'Listener'),
        ('SYSTEM', 'System'),
        ('OTHER', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10, choices=ERROR_LEVELS, default='ERROR')
    source = models.CharField(max_length=20, choices=SOURCE_TYPES, default='SYSTEM')
    component = models.CharField(max_length=100, help_text="Specific component or function where error occurred")
    message = models.TextField()
    traceback = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True, help_text="Additional contextual information about the error")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['level']),
            models.Index(fields=['source']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.source} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
