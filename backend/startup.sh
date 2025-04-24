#!/bin/bash
# Try to navigate to the expected directory or fall back to script location
if [ -d "/home/site/wwwroot/backend" ]; then
    cd /home/site/wwwroot/backend
else
    cd "$(dirname "$0")" || echo "Warning: Could not change to script directory"
fi

# Wait for PostgreSQL to be ready (could add more robust check if needed)
echo "Waiting for PostgreSQL..."
sleep 3

echo "Creating migrations if needed..."
# Try to run makemigrations safely
python manage.py makemigrations --check || python manage.py makemigrations core

# Continue even if migrations creation has issues
if [ $? -ne 0 ]; then
    echo "Warning: Failed to create migrations, continuing anyway"
fi

echo "Running migrations..."
# Use fake-initial which helps when tables exist but migrations history doesn't
python manage.py migrate --fake-initial || python manage.py migrate

# Continue even if there are migration issues
if [ $? -ne 0 ]; then
    echo "Warning: Some migrations may not have applied correctly"
fi

echo "Starting Gunicorn..."
gunicorn --bind=0.0.0.0 --timeout 600 core.wsgi:application