from django.core.management.base import BaseCommand
from amazon_ads_reports.models import Tenant, AmazonAdsCredential
import os
import sys
import uuid

class Command(BaseCommand):
    help = 'Update Amazon Ads credentials with values from drive folder'

    def handle(self, *args, **options):
        # Add drive folder to path so we can import from it
        drive_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'drive')
        sys.path.append(drive_path)
        
        try:
            # Import values from ads_key.py in drive folder
            from ads_key import client_id, client_secret, refresh_token, profile_id, client
            
            self.stdout.write(self.style.SUCCESS(f"Successfully imported values from ads_key.py"))
            self.stdout.write(f"Client ID: {client_id}")
            self.stdout.write(f"Profile ID: {profile_id}")
            self.stdout.write(f"Client name: {client}")
            
            # Find tenant with matching name or identifier
            tenant = None
            try:
                tenant = Tenant.objects.get(name__icontains=client)
                self.stdout.write(self.style.SUCCESS(f"Found tenant by name: {tenant.name} (ID: {tenant.id})"))
            except Tenant.DoesNotExist:
                try:
                    tenant = Tenant.objects.get(identifier__icontains=client)
                    self.stdout.write(self.style.SUCCESS(f"Found tenant by identifier: {tenant.identifier} (ID: {tenant.id})"))
                except Tenant.DoesNotExist:
                    # Use first tenant if no match found
                    tenant = Tenant.objects.first()
                    self.stdout.write(self.style.WARNING(f"No tenant found matching '{client}', using first tenant: {tenant.name} (ID: {tenant.id})"))
            
            # Get or create credential for tenant
            credential, created = AmazonAdsCredential.objects.update_or_create(
                tenant=tenant,
                is_active=True,
                defaults={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'refresh_token': refresh_token,
                    'profile_id': profile_id,
                    'region': 'EU'  # Hardcoded since all API URLs use EU
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created new credential (ID: {credential.id})"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated existing credential (ID: {credential.id})"))
                
            self.stdout.write(self.style.SUCCESS("Credentials updated successfully!"))
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"Error importing from ads_key.py: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating credentials: {e}")) 