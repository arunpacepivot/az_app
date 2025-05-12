# Amazon Ads Reports

This Django app provides a robust solution for retrieving, storing, and analyzing Amazon Advertising data using PostgreSQL.

## Features

- Multi-tenant architecture to support multiple Amazon Advertising accounts
- OAuth2 authentication with Amazon Advertising API
- Automated report generation and scheduling
- PostgreSQL storage for efficient data analysis
- REST API for report generation and data access
- Admin interface for report management

## Models

- `Tenant`: Multi-tenancy support
- `AmazonAdsCredential`: Amazon Advertising API credentials
- `ReportType`: Report type definitions
- `AdsReport`: Report metadata
- `DailyProductAdsData`: Storage for daily product advertising data
- `SearchTermReportData`: Storage for search term report data
- `ReportSchedule`: Report scheduling configuration

## API Endpoints

The API is accessible at `/api/v1/amazon-ads/`:

- `tenants/`: Manage tenants
- `credentials/`: Manage Amazon Ads API credentials
- `report-types/`: View available report types
- `reports/`: Manage reports
- `daily-data/`: Access daily product advertising data
- `search-terms/`: Access search term report data
- `schedules/`: Manage report schedules

## Management Commands

- `python manage.py process_pending_reports`: Process pending reports (check status, download and store data)
- `python manage.py run_scheduled_reports`: Run reports scheduled for execution

## Usage Example

### Setting up a tenant and credentials

```python
# Create a tenant
tenant = Tenant.objects.create(
    name="My Store",
    identifier="my-store"
)

# Set up Amazon Ads credentials
credential = AmazonAdsCredential.objects.create(
    tenant=tenant,
    client_id="your-client-id",
    client_secret="your-client-secret",
    refresh_token="your-refresh-token",
    profile_id="your-profile-id",
    region="EU"  # Or 'NA', 'FE' based on your Amazon marketplace
)
```

### Requesting a report

```python
from amazon_ads_reports.models import ReportType, Tenant
from amazon_ads_reports.services import AmazonAdsReportService
from datetime import date, timedelta

# Get required objects
tenant = Tenant.objects.get(identifier="my-store")
report_type = ReportType.objects.get(slug="daily-product-ads")
credential = tenant.amazon_ads_credentials.filter(is_active=True).first()

# Set date range
end_date = date.today() - timedelta(days=1)  # Yesterday
start_date = end_date - timedelta(days=30)  # Last 30 days

# Request report
report = AmazonAdsReportService.request_report(
    credential=credential,
    report_type=report_type,
    start_date=start_date,
    end_date=end_date,
    tenant=tenant
)

# Check report status
updated_report = AmazonAdsReportService.get_report_status(credential, report)

# Download and process report when completed
if updated_report.status == 'COMPLETED':
    AmazonAdsReportService.download_and_process_report(credential, updated_report)
```

### Setting up a scheduled report

```python
from amazon_ads_reports.models import ReportSchedule, ReportType, Tenant
from django.utils import timezone

# Create a daily schedule for product ads report
ReportSchedule.objects.create(
    tenant=tenant,
    report_type=ReportType.objects.get(slug="daily-product-ads"),
    name="Daily Products Report",
    frequency="DAILY",
    hour=1,  # Run at 1 AM
    minute=0,
    lookback_days=7,  # Get data for the last 7 days
    selected_metrics=ReportType.objects.get(slug="daily-product-ads").metrics,
    is_active=True,
    next_run=timezone.now() + timezone.timedelta(days=1)
)
```

## Setup

1. Install requirements: `pip install -r requirements.txt`
2. Apply migrations: `python manage.py migrate`
3. Set up cron jobs to run:
   - `python manage.py process_pending_reports`
   - `python manage.py run_scheduled_reports`

## Configuration

Set the following environment variables for PostgreSQL connection:
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST` 