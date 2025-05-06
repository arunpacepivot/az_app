# Amazon Seller and Advertising API Integration

This module provides backend integration with Amazon Seller API and Amazon Advertising API, including OAuth authentication, campaign management, and scheduled report generation.

## Setup

1. Add the following settings to your Django settings file:

```python
# Amazon API credentials
AMAZON_CLIENT_ID = 'your-client-id'
AMAZON_CLIENT_SECRET = 'your-client-secret'
AMAZON_REDIRECT_URI = 'https://your-domain.com/amazon/auth/callback'
AMAZON_ADVERTISING_REDIRECT_URI = 'https://your-domain.com/amazon/advertising/auth/callback'

# Frontend URL for redirects
FRONTEND_URL = 'https://your-frontend-domain.com'
```

2. Add the app to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'amazon_seller',
    # ...
]
```

3. Include the URLs in your project's `urls.py`:

```python
urlpatterns = [
    # ...
    path('amazon/', include('amazon_seller.urls')),
    # ...
]
```

4. Run migrations:

```bash
python manage.py makemigrations amazon_seller
python manage.py migrate
```

## Setting Up Cron Jobs for Report Processing

The module includes management commands to process scheduled reports and check the status of pending reports. These commands should be set up as cron jobs to run at regular intervals.

### Report Scheduling Commands

1. `process_scheduled_reports` - Processes reports due to be generated based on schedules
2. `check_pending_reports` - Checks status of pending reports and downloads completed reports

### Setting up Cron Jobs

#### Using crontab (Linux/Unix)

Edit your crontab:

```bash
crontab -e
```

Add the following entries:

```
# Process scheduled reports every 15 minutes
*/15 * * * * cd /path/to/your/project && python manage.py process_scheduled_reports

# Check pending reports every 5 minutes
*/5 * * * * cd /path/to/your/project && python manage.py check_pending_reports
```

#### Using Windows Task Scheduler

1. Open Task Scheduler
2. Create a new Task:
   - Action: Start a program
   - Program/script: python.exe
   - Arguments: manage.py process_scheduled_reports
   - Set the trigger to repeat every 15 minutes

3. Create another Task for checking pending reports with similar settings but a 5-minute interval.

## Authentication Flow

### Seller API

1. Redirect user to authentication URL:
   - `GET /amazon/auth/init`
   - Optional query parameters: `region`, `user_id`

2. Amazon redirects back to your callback URL with an authorization code:
   - `GET /amazon/auth/callback`

### Advertising API

1. Redirect user to authentication URL:
   - `GET /amazon/advertising/auth/init`
   - Optional query parameters: `region`, `scopes`, `user_id`

2. Amazon redirects back to your callback URL with an authorization code:
   - `GET /amazon/advertising/auth/callback`

## API Endpoints

### Advertising Profiles

- List advertising profiles: `GET /amazon/api/advertising/profiles`

### Campaigns

- List campaigns: `GET /amazon/api/advertising/campaigns/{profile_id}`
- Create campaign: `POST /amazon/api/advertising/campaigns/{profile_id}`

### Ad Groups

- List ad groups: `GET /amazon/api/advertising/ad-groups/{profile_id}`
- Create ad group: `POST /amazon/api/advertising/ad-groups/{profile_id}`

### Reports

- Generate report: `POST /amazon/api/advertising/reports/{profile_id}`

### Report Schedules

- List schedules: `GET /amazon/api/report-schedules`
- Create schedule: `POST /amazon/api/report-schedules`
- View schedule: `GET /amazon/api/report-schedules/{schedule_id}`
- Update schedule: `PUT /amazon/api/report-schedules/{schedule_id}`
- Delete schedule: `DELETE /amazon/api/report-schedules/{schedule_id}`

### Report Management

- List reports: `GET /amazon/api/reports`
- Create report: `POST /amazon/api/reports`
- View report: `GET /amazon/api/reports/{report_id}`
- Delete report: `DELETE /amazon/api/reports/{report_id}` 