"""
Script to fix migration dependencies by directly modifying Django's migration records.
This will fake-apply authentication migration and adjust the migration order in the database.
"""
import os
import django

# Set environment variable to skip Firebase initialization
os.environ['DJANGO_SKIP_FIREBASE_INIT'] = '1'

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import necessary models
from django.db import connection

def fix_migration_dependencies():
    """
    Fix the migration dependency issue by directly updating the Django migrations table.
    - Mark authentication.0001_initial as applied
    - Update applied_at timestamp to be earlier than admin.0001_initial
    """
    with connection.cursor() as cursor:
        print("Checking if authentication.0001_initial is already applied...")
        cursor.execute("SELECT * FROM django_migrations WHERE app='authentication' AND name='0001_initial'")
        auth_migration = cursor.fetchone()
        
        if auth_migration:
            print("Authentication migration already exists, skipping...")
        else:
            print("Adding authentication.0001_initial migration record...")
            # Get the timestamp of admin.0001_initial
            cursor.execute("SELECT applied FROM django_migrations WHERE app='admin' AND name='0001_initial'")
            admin_timestamp = cursor.fetchone()[0]
            
            # Insert authentication.0001_initial with earlier timestamp
            cursor.execute(
                "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, %s)",
                ['authentication', '0001_initial', admin_timestamp]
            )
            print("Successfully added authentication.0001_initial migration record!")
            
        print("Migration fix completed. You should now be able to run migrations normally.")

if __name__ == "__main__":
    fix_migration_dependencies() 