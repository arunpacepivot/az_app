from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
import time

from amazon_ads_reports.services import AmazonAdsReportService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process pending Amazon Ads reports - check status and download completed reports'
    
    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.SUCCESS(f'Started processing pending reports at {timezone.now()}'))
        
        try:
            count = AmazonAdsReportService.process_pending_reports()
            
            elapsed_time = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(
                f'Successfully processed {count} reports in {elapsed_time:.2f} seconds'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing reports: {str(e)}'))
            logger.exception("Error in process_pending_reports command")
            raise 