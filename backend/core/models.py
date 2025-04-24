from django.db import models

class StoredFile(models.Model):
    """Model for tracking files stored in local storage or Azure Blob Storage"""
    file_id = models.CharField(max_length=64, primary_key=True)
    filename = models.CharField(max_length=255)
    blob_name = models.CharField(max_length=255, null=True, blank=True)
    blob_url = models.URLField(max_length=500, null=True, blank=True)
    local_path = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    access_count = models.IntegerField(default=0)
    is_blob = models.BooleanField(default=False)

    class Meta:
        app_label = 'core'
        indexes = [
            models.Index(fields=['expires_at'], name='core_sf_expires_idx'),
            models.Index(fields=['filename'], name='core_sf_filename_idx'),
        ]
        
    def __str__(self):
        return f"{self.filename} ({self.file_id})" 