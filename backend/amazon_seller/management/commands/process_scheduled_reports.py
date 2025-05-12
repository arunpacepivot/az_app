from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from amazon_seller.services.reports import ReportingService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process scheduled Amazon Advertising reports'

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(f"Starting scheduled report processing at {start_time}")
        
        try:
            count = ReportingService.process_scheduled_reports()
            self.stdout.write(self.style.SUCCESS(f"Successfully processed {count} scheduled reports"))
        except Exception as e:
            logger.error(f"Error processing scheduled reports: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error processing scheduled reports: {str(e)}"))
            
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        self.stdout.write(f"Completed in {duration:.2f} seconds") 