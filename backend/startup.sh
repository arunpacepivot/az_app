#!/bin/bash
cd /home/site/wwwroot/backend

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
sleep 3


echo "Running migrations..."
python manage.py migrate


echo "Starting Gunicorn..."
gunicorn --bind=0.0.0.0 --timeout 600 core.wsgi:application