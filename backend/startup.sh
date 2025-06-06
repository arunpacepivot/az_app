#!/bin/bash
cd /home/site/wwwroot/backend

# Create temp_files directory if it doesn't exist
echo "Creating temp_files directory..."
mkdir -p /home/site/wwwroot/temp_files

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
sleep 3

echo "Creating migrations if needed..."
python manage.py makemigrations

if [ $? -ne 0 ]; then
    echo "Error: Failed to create migrations"
    exit 1
fi

echo "Running migrations..."
python manage.py migrate

if [ $? -ne 0 ]; then
    echo "Error: Failed to apply migrations"
    exit 1
fi

echo "Starting Gunicorn..."
gunicorn --bind=0.0.0.0 --timeout 600 core.wsgi:application