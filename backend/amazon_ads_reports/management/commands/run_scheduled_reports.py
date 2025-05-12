from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
import time

from amazon_ads_reports.services import AmazonAdsReportService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run scheduled Amazon Ads reports that are due for execution'
    
    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.SUCCESS(f'Started running scheduled reports at {timezone.now()}'))
        
        try:
            count = AmazonAdsReportService.process_scheduled_reports()
            
            elapsed_time = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(
                f'Successfully scheduled {count} reports in {elapsed_time:.2f} seconds'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running scheduled reports: {str(e)}'))
            logger.exception("Error in run_scheduled_reports command")
            raise 