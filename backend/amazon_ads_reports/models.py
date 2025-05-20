from django.db import models
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Tenant(models.Model):
    """Model for multi-tenancy support"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    identifier = models.SlugField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class AmazonAdsCredential(models.Model):
    """Model for storing Amazon Ads API credentials by tenant"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='amazon_ads_credentials')
    
    # Credentials
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=2048)
    profile_id = models.CharField(max_length=255)
    
    # Token lifecycle
    access_token = models.CharField(max_length=2048, blank=True, null=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Region selection for API endpoints
    REGION_CHOICES = [
        ('NA', 'North America'),
        ('EU', 'Europe'),
        ('FE', 'Far East'),
    ]
    region = models.CharField(max_length=2, choices=REGION_CHOICES, default='EU')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('tenant', 'profile_id')
        indexes = [
            models.Index(fields=['profile_id']),
            models.Index(fields=['tenant', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - Profile: {self.profile_id}"
    
    def is_token_expired(self):
        """Check if the access token is expired or about to expire (within 5 minutes)"""
        if not self.token_expires_at:
            return True
        buffer_time = timezone.timedelta(minutes=5)
        return self.token_expires_at <= timezone.now() + buffer_time

class ReportType(models.Model):
    """Model for defining different types of Amazon Ads reports"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # API configuration
    api_report_type = models.CharField(max_length=100, help_text="Report type identifier used in Amazon Ads API")
    ad_product = models.CharField(max_length=50, help_text="Ad product type (e.g., SPONSORED_PRODUCTS)")
    metrics = models.JSONField(help_text="List of available metrics for this report type")
    time_unit = models.CharField(max_length=20, default="DAILY", help_text="Time unit for report data")
    default_group_by = models.JSONField(null=True, blank=True, help_text="Default groupBy dimensions for the report")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class AdsReport(models.Model):
    """Model for tracking Amazon Ads report requests and metadata"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='ads_reports')
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='reports')
    
    # Report request details
    amazon_report_id = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    selected_metrics = models.JSONField(help_text="List of metrics selected for this report")
    group_by = models.JSONField(default=list, blank=True, help_text="Grouping dimensions for the report")
    
    # Processing status
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    download_url = models.TextField(null=True, blank=True, help_text="Amazon S3 pre-signed URL to download the report")
    error_message = models.TextField(null=True, blank=True)
    
    # Data storage status
    is_stored = models.BooleanField(default=False, help_text="Whether the report data has been stored in the database")
    rows_processed = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # User relationship
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ads_reports')
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['amazon_report_id']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.report_type.name} ({self.start_date} to {self.end_date})"

class DailyProductAdsData(models.Model):
    """Model for storing daily product advertising report data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='daily_product_ads_data')
    report = models.ForeignKey(AdsReport, on_delete=models.CASCADE, related_name='daily_product_ads_data')
    
    # Report data fields
    date = models.DateField(db_index=True)
    portfolio_id = models.CharField(max_length=255, null=True, blank=True)
    campaign_name = models.CharField(max_length=255, null=True, blank=True)
    campaign_id = models.CharField(max_length=255, db_index=True)
    ad_group_name = models.CharField(max_length=255, null=True, blank=True)
    ad_group_id = models.CharField(max_length=255, null=True, blank=True)
    ad_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Budget fields
    campaign_budget_type = models.CharField(max_length=50, null=True, blank=True)
    campaign_budget_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    campaign_budget_currency_code = models.CharField(max_length=10, null=True, blank=True)
    campaign_status = models.CharField(max_length=50, null=True, blank=True)
    
    # Product fields
    advertised_asin = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    advertised_sku = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    
    # Metrics
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    click_through_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cost_per_click = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    spend = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Conversion metrics
    units_sold_clicks_30d = models.IntegerField(default=0)
    units_sold_same_sku_30d = models.IntegerField(default=0)
    
    # Sales metrics
    sales_1d = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sales_7d = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sales_14d = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sales_30d = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    attributed_sales_same_sku_30d = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Purchase metrics
    purchases_1d = models.IntegerField(default=0)
    purchases_7d = models.IntegerField(default=0)
    purchases_14d = models.IntegerField(default=0)
    purchases_30d = models.IntegerField(default=0)
    purchases_same_sku_30d = models.IntegerField(default=0)
    
    # Cross-sell metrics
    units_sold_other_sku_7d = models.IntegerField(default=0)
    sales_other_sku_7d = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('tenant', 'date', 'campaign_id', 'advertised_asin')
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['tenant', 'campaign_id']),
            models.Index(fields=['tenant', 'advertised_asin']),
            models.Index(fields=['tenant', 'advertised_sku']),
        ]
        verbose_name = "Daily Product Ads Data"
        verbose_name_plural = "Daily Product Ads Data"

class SearchTermReportData(models.Model):
    """Model for storing search term report data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='search_term_data')
    report = models.ForeignKey(AdsReport, on_delete=models.CASCADE, related_name='search_term_data')
    
    # Report data fields
    date = models.DateField(db_index=True)
    campaign_name = models.CharField(max_length=255, null=True, blank=True)
    campaign_id = models.CharField(max_length=255, db_index=True)
    ad_group_name = models.CharField(max_length=255, null=True, blank=True)
    ad_group_id = models.CharField(max_length=255, null=True, blank=True)
    keyword_text = models.CharField(max_length=255, null=True, blank=True)
    match_type = models.CharField(max_length=50, null=True, blank=True)
    query = models.TextField(help_text="Customer search term")
    
    # Metrics
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    click_through_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cost_per_click = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Conversion metrics
    conversions = models.IntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Sales metrics
    sales_7d = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sales_14d = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sales_30d = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['tenant', 'query']),
            models.Index(fields=['tenant', 'campaign_id']),
        ]
        verbose_name = "Search Term Report Data"
        verbose_name_plural = "Search Term Report Data"

class ReportSchedule(models.Model):
    """Model for scheduling regular report refreshes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='report_schedules')
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='schedules')
    name = models.CharField(max_length=255)
    
    # Schedule configuration
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    ]
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='DAILY')
    hour = models.IntegerField(default=1, help_text="Hour of day to run (0-23)")
    minute = models.IntegerField(default=0, help_text="Minute of hour to run (0-59)")
    day_of_week = models.IntegerField(null=True, blank=True, help_text="Day of week for weekly schedules (0=Monday, 6=Sunday)")
    day_of_month = models.IntegerField(null=True, blank=True, help_text="Day of month for monthly schedules (1-31)")
    
    # Report configuration
    lookback_days = models.IntegerField(default=7, help_text="Number of days to look back for each report")
    selected_metrics = models.JSONField(help_text="List of metrics to include in the report")
    group_by = models.JSONField(default=list, blank=True, help_text="Grouping dimensions for the report")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField()
    
    # User relationship
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ads_report_schedules')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['next_run']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.name} ({self.get_frequency_display()})"
    
    def calculate_next_run(self):
        """Calculate the next scheduled run time"""
        now = timezone.now()
        if not self.last_run:
            base_time = now
        else:
            base_time = self.last_run
            
        next_run = None
        
        if self.frequency == 'DAILY':
            # Run every day at the specified time
            next_day = base_time + timezone.timedelta(days=1)
            next_run = timezone.datetime(
                year=next_day.year,
                month=next_day.month,
                day=next_day.day,
                hour=self.hour,
                minute=self.minute,
                tzinfo=timezone.get_current_timezone()
            )
        elif self.frequency == 'WEEKLY' and self.day_of_week is not None:
            # Run weekly on the specified day
            days_ahead = self.day_of_week - base_time.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
                
            next_day = base_time + timezone.timedelta(days=days_ahead)
            next_run = timezone.datetime(
                year=next_day.year,
                month=next_day.month,
                day=next_day.day,
                hour=self.hour,
                minute=self.minute,
                tzinfo=timezone.get_current_timezone()
            )
        elif self.frequency == 'MONTHLY' and self.day_of_month is not None:
            # Run monthly on the specified day
            # Find the next month
            if base_time.month == 12:
                next_month = 1
                next_year = base_time.year + 1
            else:
                next_month = base_time.month + 1
                next_year = base_time.year
                
            # Adjust for months with fewer days
            import calendar
            last_day = calendar.monthrange(next_year, next_month)[1]
            target_day = min(self.day_of_month, last_day)
            
            next_run = timezone.datetime(
                year=next_year,
                month=next_month,
                day=target_day,
                hour=self.hour,
                minute=self.minute,
                tzinfo=timezone.get_current_timezone()
            )
            
        # If we couldn't calculate next_run, default to tomorrow
        if not next_run:
            tomorrow = now + timezone.timedelta(days=1)
            next_run = timezone.datetime(
                year=tomorrow.year,
                month=tomorrow.month,
                day=tomorrow.day,
                hour=self.hour,
                minute=self.minute,
                tzinfo=timezone.get_current_timezone()
            )
            
        return next_run
