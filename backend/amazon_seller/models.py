from django.db import models
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

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
    
    # User relationship (optional)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='amazon_seller_accounts', null=True, blank=True)
    
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

class AmazonAdvertisingAccount(models.Model):
    """Model for tracking Amazon Advertising accounts and their OAuth credentials"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_id = models.CharField(max_length=255, unique=True)
    
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
    
    # Scopes (permissions) granted during authorization
    scopes = models.TextField(blank=True, null=True, help_text="Space-separated list of authorized scopes")
    
    # User relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='amazon_advertising_accounts', null=True, blank=True)
    
    # Optional relationship to seller account
    seller_account = models.ForeignKey(AmazonSellerAccount, on_delete=models.SET_NULL, related_name='advertising_accounts', null=True, blank=True)
    
    class Meta:
        verbose_name = "Amazon Advertising Account"
        verbose_name_plural = "Amazon Advertising Accounts"
        indexes = [
            models.Index(fields=['profile_id']),
            models.Index(fields=['token_expires_at']),
        ]
    
    def __str__(self):
        return f"Advertising Profile: {self.profile_id}"
    
    def is_token_expired(self):
        """Check if the access token is expired or about to expire (within 5 minutes)"""
        buffer_time = timezone.timedelta(minutes=5)
        return self.token_expires_at <= timezone.now() + buffer_time

class AdvertisingReport(models.Model):
    """Model for storing Amazon Advertising API reports"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Report identification
    report_id = models.CharField(max_length=255, unique=True, help_text="Report ID from Amazon API")
    
    # Report metadata
    report_type = models.CharField(max_length=100, help_text="Type of report (campaigns, adGroups, etc.)")
    status = models.CharField(max_length=50, default="PENDING", help_text="Report generation status")
    
    # Report parameters
    metrics = models.TextField(help_text="Comma-separated list of metrics included in the report")
    start_date = models.DateField(null=True, blank=True, help_text="Report start date")
    end_date = models.DateField(help_text="Report end date")
    segment = models.CharField(max_length=100, null=True, blank=True, help_text="Optional segment for grouping data")
    
    # Report content
    download_url = models.URLField(max_length=1024, null=True, blank=True, help_text="URL to download the report")
    report_data = models.JSONField(null=True, blank=True, help_text="Report data if stored directly")
    
    # Relationship to an advertising account
    advertising_account = models.ForeignKey(
        AmazonAdvertisingAccount, 
        on_delete=models.CASCADE, 
        related_name='reports'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Optional user relationship for reports not tied to a specific advertising account
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='advertising_reports', null=True, blank=True)
    
    class Meta:
        verbose_name = "Advertising Report"
        verbose_name_plural = "Advertising Reports"
        indexes = [
            models.Index(fields=['report_id']),
            models.Index(fields=['status']),
            models.Index(fields=['report_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.report_type} Report: {self.report_id}"

class ReportSchedule(models.Model):
    """Model for scheduling recurring report generation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Schedule name and description
    name = models.CharField(max_length=255, help_text="Name for this report schedule")
    description = models.TextField(null=True, blank=True, help_text="Description of this scheduled report")
    
    # Report parameters (same as AdvertisingReport model)
    report_type = models.CharField(max_length=100, help_text="Type of report (campaigns, adGroups, etc.)")
    metrics = models.TextField(help_text="Comma-separated list of metrics to include in the report")
    segment = models.CharField(max_length=100, null=True, blank=True, help_text="Optional segment for grouping data")
    
    # Date range options
    RANGE_CHOICES = [
        ('last_7_days', 'Last 7 Days'),
        ('last_30_days', 'Last 30 Days'),
        ('month_to_date', 'Month to Date'),
        ('previous_month', 'Previous Month'),
        ('custom', 'Custom Range'),
    ]
    date_range = models.CharField(max_length=20, choices=RANGE_CHOICES, default='last_7_days')
    custom_start_date = models.DateField(null=True, blank=True, help_text="Start date for custom range")
    custom_end_date = models.DateField(null=True, blank=True, help_text="End date for custom range")
    
    # Schedule frequency
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    
    # For weekly, which day of the week
    DAY_OF_WEEK_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    day_of_week = models.IntegerField(choices=DAY_OF_WEEK_CHOICES, null=True, blank=True)
    
    # For monthly, which day of the month
    day_of_month = models.IntegerField(null=True, blank=True, help_text="Day of month for monthly schedules (1-31)")
    
    # Time of day to run (in UTC)
    hour = models.IntegerField(default=0, help_text="Hour of day (0-23)")
    minute = models.IntegerField(default=0, help_text="Minute of hour (0-59)")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Whether this schedule is active")
    last_run = models.DateTimeField(null=True, blank=True, help_text="When this schedule last generated a report")
    next_run = models.DateTimeField(help_text="When this schedule will next generate a report")
    
    # Relationship to an advertising account
    advertising_account = models.ForeignKey(
        AmazonAdvertisingAccount, 
        on_delete=models.CASCADE, 
        related_name='report_schedules'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # User relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_schedules')
    
    class Meta:
        verbose_name = "Report Schedule"
        verbose_name_plural = "Report Schedules"
        indexes = [
            models.Index(fields=['next_run']),
            models.Index(fields=['is_active']),
            models.Index(fields=['frequency']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.frequency})"
    
    def calculate_next_run(self):
        """Calculate the next run time based on frequency and last run"""
        now = timezone.now()
        if not self.last_run:
            # First run - start from now
            base_time = now
        else:
            base_time = self.last_run
        
        if self.frequency == 'daily':
            next_run = timezone.datetime(
                base_time.year, base_time.month, base_time.day,
                self.hour, self.minute, 0, tzinfo=timezone.utc
            ) + timezone.timedelta(days=1)
        elif self.frequency == 'weekly':
            # Calculate days until next day_of_week
            current_weekday = base_time.weekday()
            days_ahead = self.day_of_week - current_weekday
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
                
            next_run = timezone.datetime(
                base_time.year, base_time.month, base_time.day,
                self.hour, self.minute, 0, tzinfo=timezone.utc
            ) + timezone.timedelta(days=days_ahead)
        elif self.frequency == 'monthly':
            # Move to next month
            if base_time.month == 12:
                next_month = 1
                next_year = base_time.year + 1
            else:
                next_month = base_time.month + 1
                next_year = base_time.year
                
            # Handle month end cases
            import calendar
            last_day = calendar.monthrange(next_year, next_month)[1]
            day = min(self.day_of_month, last_day)
            
            next_run = timezone.datetime(
                next_year, next_month, day,
                self.hour, self.minute, 0, tzinfo=timezone.utc
            )
        
        # If calculated time is in the past, move it to the future
        while next_run < now:
            if self.frequency == 'daily':
                next_run += timezone.timedelta(days=1)
            elif self.frequency == 'weekly':
                next_run += timezone.timedelta(days=7)
            elif self.frequency == 'monthly':
                # Move to next month
                if next_run.month == 12:
                    next_month = 1
                    next_year = next_run.year + 1
                else:
                    next_month = next_run.month + 1
                    next_year = next_run.year
                    
                # Handle month end cases
                import calendar
                last_day = calendar.monthrange(next_year, next_month)[1]
                day = min(self.day_of_month, last_day)
                
                next_run = timezone.datetime(
                    next_year, next_month, day,
                    self.hour, self.minute, 0, tzinfo=timezone.utc
                )
        
        self.next_run = next_run
        return next_run
    
    def save(self, *args, **kwargs):
        """Override save to calculate next_run if it's not set"""
        if not self.next_run:
            self.calculate_next_run()
        super().save(*args, **kwargs)
