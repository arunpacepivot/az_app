from django.db import models

class ProcessedFile(models.Model):
    file_name = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)
    file_path = models.FileField(upload_to="processed_files/")

    def __str__(self):
        return f"{self.file_name} ({self.processed_at})" 
