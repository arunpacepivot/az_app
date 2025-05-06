from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from amazon_seller.services.reports import ReportingService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check and update pending Amazon Advertising reports'

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(f"Starting pending report check at {start_time}")
        
        try:
            count = ReportingService.check_pending_reports()
            self.stdout.write(self.style.SUCCESS(f"Successfully updated {count} pending reports"))
            
            # Also download completed reports
            download_count = ReportingService.download_completed_reports()
            self.stdout.write(self.style.SUCCESS(f"Successfully downloaded {download_count} completed reports"))
        except Exception as e:
            logger.error(f"Error checking pending reports: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error checking pending reports: {str(e)}"))
            
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        self.stdout.write(f"Completed in {duration:.2f} seconds") 