"""
Amazon Advertising API reporting service
"""
import datetime
import logging
import json
import uuid
from django.utils import timezone
from django.db.models import Q
from django.conf import settings

from ..models import AmazonAdvertisingAccount, ReportSchedule, AdvertisingReport
from .advertising import AmazonAdvertisingService

logger = logging.getLogger(__name__)

class ReportingService:
    """Service for managing Amazon Advertising API reports"""
    
    @classmethod
    def calculate_date_range(cls, date_range, custom_start_date=None, custom_end_date=None):
        """
        Calculate start and end dates based on date range option
        
        Args:
            date_range: The selected date range option
            custom_start_date: Custom start date (if date_range is 'custom')
            custom_end_date: Custom end date (if date_range is 'custom')
            
        Returns:
            Tuple of (start_date, end_date) as strings in YYYYMMDD format
        """
        today = timezone.now().date()
        
        if date_range == 'custom' and custom_start_date and custom_end_date:
            start_date = custom_start_date
            end_date = custom_end_date
        elif date_range == 'last_7_days':
            start_date = today - datetime.timedelta(days=7)
            end_date = today - datetime.timedelta(days=1)  # Yesterday
        elif date_range == 'last_30_days':
            start_date = today - datetime.timedelta(days=30)
            end_date = today - datetime.timedelta(days=1)  # Yesterday
        elif date_range == 'month_to_date':
            start_date = today.replace(day=1)
            end_date = today - datetime.timedelta(days=1)  # Yesterday
        elif date_range == 'previous_month':
            # First day of current month
            first_day_current_month = today.replace(day=1)
            # Last day of previous month
            end_date = first_day_current_month - datetime.timedelta(days=1)
            # First day of previous month
            start_date = end_date.replace(day=1)
        else:
            # Default to last 7 days
            start_date = today - datetime.timedelta(days=7)
            end_date = today - datetime.timedelta(days=1)  # Yesterday
            
        # Format as YYYYMMDD strings for the API
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        return start_str, end_str
    
    @classmethod
    def request_report(cls, account, profile_id, report_type, metrics, start_date, end_date, segment=None, user=None):
        """
        Request a report from the Amazon Advertising API
        
        Args:
            account: AmazonAdvertisingAccount instance
            profile_id: The advertising profile ID
            report_type: The type of report (campaigns, adGroups, etc.)
            metrics: List or comma-separated string of metrics
            start_date: Start date (YYYYMMDD format)
            end_date: End date (YYYYMMDD format)
            segment: Optional segment for grouping data
            user: Optional user associated with this report
            
        Returns:
            AdvertisingReport instance
        """
        try:
            # Call the API to request a report
            result = AmazonAdvertisingService.get_reports(
                account, 
                profile_id, 
                report_type, 
                metrics, 
                start_date, 
                end_date,
                segment=segment
            )
            
            # If metrics is a list, convert to string for storage
            if isinstance(metrics, list):
                metrics_str = ','.join(metrics)
            else:
                metrics_str = metrics
                
            # Parse start and end dates from string format
            start_date_obj = datetime.datetime.strptime(start_date, '%Y%m%d').date() if start_date else None
            end_date_obj = datetime.datetime.strptime(end_date, '%Y%m%d').date()
            
            # Create and save report record
            report = AdvertisingReport.objects.create(
                report_id=result.get('reportId', str(uuid.uuid4())),
                report_type=report_type,
                status=result.get('status', 'PENDING'),
                metrics=metrics_str,
                start_date=start_date_obj,
                end_date=end_date_obj,
                segment=segment,
                advertising_account=account,
                user=user,
                download_url=result.get('location')
            )
            
            logger.info(f"Created report request: {report.report_id} for profile {profile_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error requesting report: {str(e)}")
            raise
    
    @classmethod
    def process_scheduled_reports(cls):
        """
        Process reports due to be generated based on schedule
        This method is designed to be called from a cron job
        
        Returns:
            Number of reports generated
        """
        now = timezone.now()
        count = 0
        
        # Get all active schedules that are due to run (next_run <= now)
        due_schedules = ReportSchedule.objects.filter(
            is_active=True,
            next_run__lte=now
        )
        
        logger.info(f"Processing {due_schedules.count()} scheduled reports")
        
        for schedule in due_schedules:
            try:
                # Verify account is still active
                if not schedule.advertising_account.is_active:
                    logger.warning(f"Skipping scheduled report {schedule.id} - account {schedule.advertising_account.profile_id} is inactive")
                    continue
                
                # Calculate date range
                start_date, end_date = cls.calculate_date_range(
                    schedule.date_range,
                    schedule.custom_start_date,
                    schedule.custom_end_date
                )
                
                # Request the report
                report = cls.request_report(
                    account=schedule.advertising_account,
                    profile_id=schedule.advertising_account.profile_id,
                    report_type=schedule.report_type,
                    metrics=schedule.metrics,
                    start_date=start_date,
                    end_date=end_date,
                    segment=schedule.segment,
                    user=schedule.user
                )
                
                # Update schedule
                schedule.last_run = now
                schedule.calculate_next_run()
                schedule.save()
                
                count += 1
                logger.info(f"Generated scheduled report {report.report_id} for schedule {schedule.name}")
                
            except Exception as e:
                logger.error(f"Error processing scheduled report {schedule.id}: {str(e)}")
                
                # Update next_run even if there was an error to prevent retrying too frequently
                try:
                    schedule.last_run = now
                    schedule.calculate_next_run()
                    schedule.save()
                except Exception as save_error:
                    logger.error(f"Error updating schedule after failure: {str(save_error)}")
        
        return count
    
    @classmethod
    def check_pending_reports(cls):
        """
        Check status of pending reports and update database
        This method is designed to be called from a cron job
        
        Returns:
            Number of reports updated
        """
        count = 0
        # Get all reports in PENDING status
        pending_reports = AdvertisingReport.objects.filter(
            status__in=['PENDING', 'IN_PROGRESS', 'PROCESSING']
        )
        
        logger.info(f"Checking status of {pending_reports.count()} pending reports")
        
        for report in pending_reports:
            try:
                # In a real implementation, we would call the API to check status
                # For now, simulate with a placeholder
                
                # Get the account associated with the report
                account = report.advertising_account
                
                # For demonstration, mark as complete after 5 minutes
                if (timezone.now() - report.created_at).total_seconds() > 300:
                    report.status = 'COMPLETED'
                    report.completed_at = timezone.now()
                    report.save()
                    count += 1
                    logger.info(f"Report {report.report_id} marked as completed")
                
            except Exception as e:
                logger.error(f"Error checking report status for {report.report_id}: {str(e)}")
        
        return count
    
    @classmethod
    def download_completed_reports(cls):
        """
        Download content for completed reports that have a download URL
        This method is designed to be called from a cron job
        
        Returns:
            Number of reports downloaded
        """
        count = 0
        # Get completed reports with download URLs that haven't been processed
        completed_reports = AdvertisingReport.objects.filter(
            status='COMPLETED',
            download_url__isnull=False,
            report_data__isnull=True
        )
        
        logger.info(f"Downloading {completed_reports.count()} completed reports")
        
        for report in completed_reports:
            try:
                # In a real implementation, we would download the file from the URL
                # For now, simulate with a placeholder
                
                # Simulate downloaded data
                sample_data = {
                    "reportId": report.report_id,
                    "status": "COMPLETED",
                    "data": [
                        {"campaign": "Campaign 1", "impressions": 1000, "clicks": 50},
                        {"campaign": "Campaign 2", "impressions": 2000, "clicks": 100}
                    ]
                }
                
                report.report_data = sample_data
                report.save()
                count += 1
                logger.info(f"Downloaded data for report {report.report_id}")
                
            except Exception as e:
                logger.error(f"Error downloading report {report.report_id}: {str(e)}")
        
        return count 