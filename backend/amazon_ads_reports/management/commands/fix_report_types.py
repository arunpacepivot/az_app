from django.core.management.base import BaseCommand
from amazon_ads_reports.models import ReportType

class Command(BaseCommand):
    help = 'Fix report types configuration'

    def handle(self, *args, **options):
        # Fix daily product ads report
        try:
            daily_report = ReportType.objects.get(slug='daily-product-ads')
            daily_report.default_group_by = ["advertiser"]
            daily_report.save()
            self.stdout.write(self.style.SUCCESS(f"Updated Daily Product Ads report with default_group_by = ['advertiser']"))
        except ReportType.DoesNotExist:
            self.stdout.write(self.style.ERROR("Daily Product Ads report type not found"))
        
        # List all report types
        self.stdout.write("\nAll Report Types:")
        for rt in ReportType.objects.all():
            self.stdout.write(f"- {rt.name} (slug: {rt.slug}, report_type: {rt.api_report_type})")
            self.stdout.write(f"  ad_product: {rt.ad_product}")
            self.stdout.write(f"  default_group_by: {getattr(rt, 'default_group_by', None)}")
            self.stdout.write("") 