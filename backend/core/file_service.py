import os
import uuid
import base64
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.http import HttpResponse, JsonResponse, FileResponse
import pandas as pd

# Dictionary to track file references
# Structure: {file_id: {path: str, created_at: datetime, access_count: int, expires_at: datetime}}
file_registry = {}

# Configuration
TEMP_FILE_EXPIRY_HOURS = 24  # Files expire after 24 hours
FILE_CLEANUP_THRESHOLD = 100  # Clean up when registry exceeds this size
AZURE_TEMP_PATH = os.environ.get('TEMP', os.path.join(settings.BASE_DIR, 'temp'))

def ensure_temp_dir():
    """Ensure the temp directory exists."""
    if not os.path.exists(AZURE_TEMP_PATH):
        os.makedirs(AZURE_TEMP_PATH, exist_ok=True)
    
def get_temp_path(filename):
    """Get the full path for a temporary file."""
    ensure_temp_dir()
    return os.path.join(AZURE_TEMP_PATH, filename)

def save_temp_file(file_obj, custom_filename=None):
    """Save a file object to the temp directory and register it."""
    ensure_temp_dir()
    
    # Generate a unique filename if none provided
    if custom_filename:
        filename = custom_filename
    else:
        file_extension = os.path.splitext(file_obj.name)[1] if hasattr(file_obj, 'name') else '.tmp'
        filename = f"{uuid.uuid4().hex}{file_extension}"
    
    file_path = get_temp_path(filename)
    
    # If file_obj is already a path, just register it
    if isinstance(file_obj, str) and os.path.exists(file_obj):
        file_id = uuid.uuid4().hex
        file_registry[file_id] = {
            'path': file_obj,
            'filename': os.path.basename(file_obj),
            'created_at': timezone.now(),
            'access_count': 0,
            'expires_at': timezone.now() + timedelta(hours=TEMP_FILE_EXPIRY_HOURS)
        }
        return file_id
    
    # Save file from request.FILES or similar
    if hasattr(file_obj, 'chunks'):
        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)
    # Save file from a BytesIO or similar
    elif hasattr(file_obj, 'read'):
        with open(file_path, 'wb+') as destination:
            destination.write(file_obj.read())
    # Save file from a string path
    elif isinstance(file_obj, str) and os.path.exists(file_obj):
        file_path = file_obj  # Just use the existing path
    else:
        raise ValueError("Unsupported file object type")
    
    # Register the file
    file_id = uuid.uuid4().hex
    file_registry[file_id] = {
        'path': file_path,
        'filename': filename,
        'created_at': timezone.now(),
        'access_count': 0,
        'expires_at': timezone.now() + timedelta(hours=TEMP_FILE_EXPIRY_HOURS)
    }
    
    # Clean up if registry is getting too large
    cleanup_old_files()
    
    return file_id

def cleanup_old_files():
    """Clean up expired or least accessed files if registry is too large."""
    now = timezone.now()
    
    # Remove expired files
    expired_ids = [fid for fid, info in file_registry.items() if info['expires_at'] < now]
    for file_id in expired_ids:
        delete_file(file_id)
    
    # If still too many files, remove least accessed
    if len(file_registry) > FILE_CLEANUP_THRESHOLD:
        # Sort by access count and creation time
        sorted_files = sorted(file_registry.items(), 
                            key=lambda x: (x[1]['access_count'], x[1]['created_at']))
        
        # Remove oldest, least accessed files until under threshold
        for file_id, _ in sorted_files[:len(file_registry) - FILE_CLEANUP_THRESHOLD + 10]:  # +10 for buffer
            delete_file(file_id)

def delete_file(file_id):
    """Delete a file from the registry and filesystem."""
    if file_id in file_registry:
        file_path = file_registry[file_id]['path']
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except (OSError, IOError) as e:
            print(f"Error deleting file {file_path}: {str(e)}")
        
        del file_registry[file_id]
        return True
    return False

def get_file_response(file_id, as_attachment=True):
    """Generate a FileResponse for a registered file."""
    if file_id not in file_registry:
        return None
    
    file_info = file_registry[file_id]
    file_path = file_info['path']
    
    if not os.path.exists(file_path):
        delete_file(file_id)  # Clean up registry entry
        return None
    
    # Update access stats
    file_info['access_count'] += 1
    file_info['expires_at'] = timezone.now() + timedelta(hours=TEMP_FILE_EXPIRY_HOURS)
    
    response = FileResponse(
        open(file_path, 'rb'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    if as_attachment:
        response['Content-Disposition'] = f'attachment; filename="{file_info["filename"]}"'
    
    return response

def get_file_url(file_id, request=None):
    """Generate a URL for downloading a file."""
    if file_id not in file_registry:
        return None
    
    if request:
        base_url = f"{request.scheme}://{request.get_host()}"
    else:
        # Default to relative URL if request not provided
        base_url = ""
    
    return f"{base_url}/api/v1/files/download/{file_id}/"

def get_file_metadata(file_id):
    """Get metadata for a file."""
    if file_id not in file_registry:
        return None
    
    info = file_registry[file_id]
    return {
        'filename': info['filename'],
        'created_at': info['created_at'].isoformat(),
        'expires_at': info['expires_at'].isoformat(),
        'access_count': info['access_count']
    }

def get_excel_data(file_id, sheet_name=None):
    """Get data from an Excel file as a dict."""
    if file_id not in file_registry:
        return None
    
    file_path = file_registry[file_id]['path']
    
    if not os.path.exists(file_path):
        delete_file(file_id)
        return None
    
    try:
        with pd.ExcelFile(file_path) as xls:
            # If sheet_name is None, read all sheets
            if sheet_name is None:
                result = {}
                for s in xls.sheet_names:
                    result[s] = pd.read_excel(xls, sheet_name=s).to_dict(orient="records")
                return result
            else:
                # Read specific sheet
                return pd.read_excel(xls, sheet_name=sheet_name).to_dict(orient="records")
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        return None

def get_file_content_base64(file_id):
    """Get file content as base64 encoded string."""
    if file_id not in file_registry:
        return None
    
    file_path = file_registry[file_id]['path']
    
    if not os.path.exists(file_path):
        delete_file(file_id)
        return None
    
    try:
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding file: {str(e)}")
        return None 