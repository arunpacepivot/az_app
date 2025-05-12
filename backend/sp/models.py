from django.db import models

class UserPreference(models.Model):
    file_name = models.CharField(max_length=255)
    target_acos = models.FloatField(default=0.30)
    input_file = models.FileField(upload_to="input_files/")

    def __str__(self):
        return f"{self.file_name} - ACOS: {self.target_acos}"

class ProcessedFile(models.Model):
    file_name = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)
    file_path = models.FileField(upload_to="processed_files/")

    def __str__(self):
        return f"{self.file_name} ({self.processed_at})"

