from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand

def test_connection():
    db_conn = connections['default']
    try:
        c = db_conn.cursor()
        print("Successfully connected to the database!")
    except OperationalError:
        print("Could not connect to the database!")

if __name__ == "__main__":
    test_connection()

