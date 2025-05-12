"""
Final fix script to create the users table directly in the database.
This resolves the 'relation "users" does not exist' error.
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

def create_users_table():
    """
    Create the users table directly in the database if it doesn't exist.
    This matches the schema defined in the authentication.0001_initial migration.
    """
    with connection.cursor() as cursor:
        # Check if users table already exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("The 'users' table already exists.")
            return
            
        print("Creating 'users' table...")
        
        # Create users table with the same schema as defined in the migration
        cursor.execute("""
            CREATE TABLE "users" (
                "id" bigserial NOT NULL PRIMARY KEY,
                "password" varchar(128) NOT NULL,
                "last_login" timestamp with time zone NULL,
                "is_superuser" boolean NOT NULL,
                "username" varchar(150) NOT NULL UNIQUE,
                "is_staff" boolean NOT NULL,
                "is_active" boolean NOT NULL,
                "date_joined" timestamp with time zone NOT NULL,
                "firebase_uid" varchar(255) NULL UNIQUE,
                "email" varchar(254) NOT NULL UNIQUE,
                "first_name" varchar(150) NOT NULL,
                "last_name" varchar(150) NOT NULL,
                "created_at" timestamp with time zone NOT NULL,
                "updated_at" timestamp with time zone NOT NULL
            )
        """)
        
        # Create the many-to-many relationship tables
        cursor.execute("""
            CREATE TABLE "users_groups" (
                "id" bigserial NOT NULL PRIMARY KEY,
                "user_id" bigint NOT NULL,
                "group_id" integer NOT NULL,
                UNIQUE ("user_id", "group_id"),
                CONSTRAINT "users_groups_user_id_fkey" 
                    FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY DEFERRED,
                CONSTRAINT "users_groups_group_id_fkey" 
                    FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED
            )
        """)
        
        cursor.execute("""
            CREATE TABLE "users_user_permissions" (
                "id" bigserial NOT NULL PRIMARY KEY,
                "user_id" bigint NOT NULL,
                "permission_id" integer NOT NULL,
                UNIQUE ("user_id", "permission_id"),
                CONSTRAINT "users_user_permissions_user_id_fkey" 
                    FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY DEFERRED,
                CONSTRAINT "users_user_permissions_permission_id_fkey" 
                    FOREIGN KEY ("permission_id") REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED
            )
        """)
        
        print("Successfully created 'users' table and related tables!")
        print("You should now be able to run migrations normally.")

if __name__ == "__main__":
    create_users_table() 