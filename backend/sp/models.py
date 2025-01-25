from django.db import models

class UploadedFile(models.Model):
    """Model to store the uploaded Excel file and metadata."""
    file = models.FileField(upload_to='uploads/')  # Path to store uploaded files
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Timestamp of the upload
    target_acos = models.FloatField()  # Target ACOS value provided by the user
    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')],
        default='PENDING'
    )  # Status of the file processing
    error_message = models.TextField(blank=True, null=True)  # Store error messages if processing fails

    def __str__(self):
        return f"File {self.id}: {self.file.name} (Status: {self.status})"


class ProcessedData(models.Model):
    """Model to store summary or result of the processed Excel file."""
    uploaded_file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE, related_name='processed_data')
    combined_df_summary = models.JSONField(blank=True, null=True)  # JSON summary of combined_df
    pt_combined_df_summary = models.JSONField(blank=True, null=True)  # JSON summary of pt_combined_df
    kw_combined_df_summary = models.JSONField(blank=True, null=True)  # JSON summary of kw_combined_df
    placement_combined_df_summary = models.JSONField(blank=True, null=True)  # JSON summary of placement_combined_df
    rpc_combined_df_summary = models.JSONField(blank=True, null=True)  # JSON summary of RPC_combined_df
    bulk_summary_combined_df_summary = models.JSONField(blank=True, null=True)  # JSON summary of bulk_summary_combined_df
    processed_at = models.DateTimeField(auto_now_add=True)  # Timestamp of when the processing was completed

    def __str__(self):
        return f"Processed Data for File {self.uploaded_file.id}"
