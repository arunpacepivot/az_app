import os
import uuid
import base64
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.http import HttpResponse, JsonResponse, FileResponse
import pandas as pd
from urllib.parse import urljoin

# Import Azure Blob Storage service
try:
    from .azure_blob_service import upload_blob, get_blob_sas_url, delete_blob, cleanup_expired_blobs
    AZURE_BLOB_AVAILABLE = True
except ImportError:
    AZURE_BLOB_AVAILABLE = False

# Set up logger
logger = logging.getLogger('file_service')

# Dictionary to track file references
# Structure: {file_id: {path: str, created_at: datetime, access_count: int, expires_at: datetime}}
file_registry = {}

# Additional dictionary to track Azure blobs
# Structure: {file_id: {blob_name: str, blob_url: str, created_at: datetime, expires_at: datetime}}
azure_blob_registry = {}

# Configuration
TEMP_FILE_EXPIRY_HOURS = 4  # Files expire after 4 hours
FILE_CLEANUP_THRESHOLD = 100  # Clean up when registry exceeds this size
AZURE_TEMP_PATH = '/home/site/wwwroot/temp_files'  # Use absolute path for consistency
REGISTRY_FILE = os.path.join(AZURE_TEMP_PATH, 'file_registry.json')
AZURE_REGISTRY_FILE = os.path.join(AZURE_TEMP_PATH, 'azure_blob_registry.json')

# Check if Azure Blob Storage should be used
USE_AZURE_STORAGE = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', None) and AZURE_BLOB_AVAILABLE
logger.info(f"Using Azure Blob Storage: {USE_AZURE_STORAGE}")

def normalize_azure_path(path):
    """Convert between /root/ and /home/ paths in Azure."""
    if not path:  # Handle None or empty paths
        return path
    if isinstance(path, str) and path.startswith('/root/'):
        return path.replace('/root/', '/home/', 1)
    return path

def ensure_temp_dir():
    """Ensure the temp directory exists and is writable."""
    global AZURE_TEMP_PATH, REGISTRY_FILE, AZURE_REGISTRY_FILE
    
    if not os.path.exists(AZURE_TEMP_PATH):
        try:
            os.makedirs(AZURE_TEMP_PATH, exist_ok=True)
            logger.info(f"Created temp directory at {AZURE_TEMP_PATH}")
            
            # Set liberal permissions for the temp directory in Azure
            try:
                import stat
                os.chmod(AZURE_TEMP_PATH, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777 permissions
                logger.info(f"Set permissions on temp directory: {AZURE_TEMP_PATH}")
            except Exception as e:
                logger.warning(f"Unable to set permissions on temp directory: {str(e)}")
                
            # Verify the directory is writable by creating a test file
            test_file = os.path.join(AZURE_TEMP_PATH, ".test_write")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                logger.info("Verified temp directory is writable")
            except Exception as e:
                logger.error(f"Temp directory is not writable: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create temp directory: {str(e)}")
            # Fallback to a directory we know should be writable in Azure
            fallback_path = '/home/site/wwwroot/azure_temp'
            logger.warning(f"Falling back to alternative temp path: {fallback_path}")
            
            try:
                os.makedirs(fallback_path, exist_ok=True)
                AZURE_TEMP_PATH = fallback_path
                REGISTRY_FILE = os.path.join(AZURE_TEMP_PATH, 'file_registry.json')
                AZURE_REGISTRY_FILE = os.path.join(AZURE_TEMP_PATH, 'azure_blob_registry.json')
            except Exception as e2:
                logger.critical(f"Failed to create fallback temp directory: {str(e2)}")

def get_temp_path(filename):
    """Get the full path for a temporary file."""
    ensure_temp_dir()
    # Ensure consistent path separators
    return os.path.join(AZURE_TEMP_PATH, filename).replace('\\', '/')

def load_registry():
    """Load file registry from JSON file."""
    global file_registry, azure_blob_registry
    ensure_temp_dir()
    
    # Load local file registry
    try:
        if os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE, 'r') as f:
                data = json.load(f)
                
                # Convert string dates back to datetime objects
                for file_id, info in data.items():
                    if 'created_at' in info and isinstance(info['created_at'], str):
                        info['created_at'] = timezone.datetime.fromisoformat(info['created_at'].replace('Z', '+00:00'))
                    if 'expires_at' in info and isinstance(info['expires_at'], str):
                        info['expires_at'] = timezone.datetime.fromisoformat(info['expires_at'].replace('Z', '+00:00'))
                    
                    # Normalize paths for Azure
                    if 'path' in info and isinstance(info['path'], str):
                        info['path'] = normalize_azure_path(info['path'])
                
                file_registry = data
                logger.info(f"Loaded {len(file_registry)} files from registry file")
    except Exception as e:
        logger.error(f"Error loading file registry: {e}")
        file_registry = {}
    
    # Load Azure blob registry
    if USE_AZURE_STORAGE:
        try:
            if os.path.exists(AZURE_REGISTRY_FILE):
                with open(AZURE_REGISTRY_FILE, 'r') as f:
                    data = json.load(f)
                    
                    # Convert string dates back to datetime objects
                    for file_id, info in data.items():
                        if 'created_at' in info and isinstance(info['created_at'], str):
                            info['created_at'] = timezone.datetime.fromisoformat(info['created_at'].replace('Z', '+00:00'))
                        if 'expires_at' in info and isinstance(info['expires_at'], str):
                            info['expires_at'] = timezone.datetime.fromisoformat(info['expires_at'].replace('Z', '+00:00'))
                    
                    azure_blob_registry = data
                    logger.info(f"Loaded {len(azure_blob_registry)} Azure blobs from registry file")
        except Exception as e:
            logger.error(f"Error loading Azure blob registry: {e}")
            azure_blob_registry = {}
        
    # Scan temp directory for files not in registry
    try:
        scan_temp_directory()
    except Exception as e:
        logger.error(f"Error scanning temp directory: {e}")

def save_registry():
    """Save file registry to JSON file."""
    ensure_temp_dir()
    
    # Save local file registry
    try:
        # Normalize paths before serializing
        for file_id, info in file_registry.items():
            if 'path' in info and isinstance(info['path'], str):
                info['path'] = normalize_azure_path(info['path'])
        
        # Convert datetime objects to ISO format strings for JSON serialization
        serializable_registry = {}
        for file_id, info in file_registry.items():
            serializable_info = info.copy()
            if 'created_at' in info and hasattr(info['created_at'], 'isoformat'):
                serializable_info['created_at'] = info['created_at'].isoformat()
            if 'expires_at' in info and hasattr(info['expires_at'], 'isoformat'):
                serializable_info['expires_at'] = info['expires_at'].isoformat()
            serializable_registry[file_id] = serializable_info
            
        with open(REGISTRY_FILE, 'w') as f:
            json.dump(serializable_registry, f)
        logger.debug(f"Registry saved with {len(file_registry)} entries")
    except Exception as e:
        logger.error(f"Error saving file registry: {e}")
    
    # Save Azure blob registry
    if USE_AZURE_STORAGE:
        try:
            # Convert datetime objects to ISO format strings for JSON serialization
            serializable_registry = {}
            for file_id, info in azure_blob_registry.items():
                serializable_info = info.copy()
                if 'created_at' in info and hasattr(info['created_at'], 'isoformat'):
                    serializable_info['created_at'] = info['created_at'].isoformat()
                if 'expires_at' in info and hasattr(info['expires_at'], 'isoformat'):
                    serializable_info['expires_at'] = info['expires_at'].isoformat()
                serializable_registry[file_id] = serializable_info
                
            with open(AZURE_REGISTRY_FILE, 'w') as f:
                json.dump(serializable_registry, f)
            logger.debug(f"Azure blob registry saved with {len(azure_blob_registry)} entries")
        except Exception as e:
            logger.error(f"Error saving Azure blob registry: {e}")

def scan_temp_directory():
    """Scan temp directory for files not in registry."""
    ensure_temp_dir()
    
    # Get all files currently registered in the file system
    registered_paths = set()
    for info in file_registry.values():
        if 'path' in info:
            # Add both home and root versions of the path for comparison
            path = info['path']
            if path is not None:  # Check for None
                registered_paths.add(path)
                if isinstance(path, str):  # Ensure path is a string before using startswith
                    if path.startswith('/home/'):
                        registered_paths.add(path.replace('/home/', '/root/', 1))
                    elif path.startswith('/root/'):
                        registered_paths.add(path.replace('/root/', '/home/', 1))
    
    logger.debug(f"Registered paths: {len(registered_paths)}")
    
    # Scan the temp directory for files
    try:
        all_files = os.listdir(AZURE_TEMP_PATH)
        logger.debug(f"Found {len(all_files)} files in temp directory")
        
        for filename in all_files:
            file_path = os.path.join(AZURE_TEMP_PATH, filename)
            
            # Skip directories and registry file
            if os.path.isdir(file_path) or filename == 'file_registry.json':
                continue
                
            # If file isn't in registry, add it
            if file_path not in registered_paths:
                # Create a new file ID
                file_id = uuid.uuid4().hex
                
                # Register the file
                file_registry[file_id] = {
                    'path': file_path,
                    'filename': filename,
                    'created_at': timezone.now(),
                    'access_count': 0,
                    'expires_at': timezone.now() + timedelta(hours=TEMP_FILE_EXPIRY_HOURS)
                }
                
                logger.info(f"Found unregistered file: {filename}, registered as {file_id}")
                
        # If we found new files, save the registry
        save_registry()
    except Exception as e:
        logger.error(f"Error scanning temp directory: {e}")

# Load registry at module import time
load_registry()

def save_temp_file(file_obj, custom_filename=None):
    """Save a file either to local temp dir or Azure Blob Storage."""
    # Store in database if possible
    try:
        from .models import StoredFile
        db_available = True
    except (ImportError, ModuleNotFoundError):
        db_available = False
        logger.warning("StoredFile model not available, using file-based registry only")

    # If Azure Blob Storage is available and configured, use it
    if USE_AZURE_STORAGE:
        try:
            # Create unique filename with timestamp for better traceability
            if custom_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                base, ext = os.path.splitext(custom_filename)
                unique_filename = f"{base}_{timestamp}_{uuid.uuid4().hex[:6]}{ext}"
            else:
                unique_filename = None
                
            # Upload to Azure Blob Storage
            blob_name, blob_url = upload_blob(file_obj, unique_filename)
            
            # Generate consistent file ID
            file_id = uuid.uuid4().hex
            
            # Display filename for UI
            if custom_filename:
                display_filename = custom_filename
            elif hasattr(file_obj, 'name'):
                display_filename = os.path.basename(file_obj.name)
            elif isinstance(file_obj, str) and os.path.exists(file_obj):
                display_filename = os.path.basename(file_obj)
            else:
                display_filename = blob_name
                
            # Expiry time
            expires_at = timezone.now() + timedelta(hours=settings.AZURE_BLOB_EXPIRY_HOURS)
                
            # Store in database if available
            if db_available:
                try:
                    StoredFile.objects.create(
                        file_id=file_id,
                        filename=display_filename,
                        blob_name=blob_name,
                        blob_url=blob_url,
                        local_path=None,
                        expires_at=expires_at,
                        is_blob=True
                    )
                    logger.info(f"File saved to database with ID: {file_id}")
                except Exception as e:
                    logger.error(f"Error saving to database: {str(e)}")
                
            # Register in memory caches for backward compatibility
            blob_info = {
                'blob_name': blob_name,
                'blob_url': blob_url,
                'filename': display_filename,
                'created_at': timezone.now(),
                'expires_at': expires_at
            }
            
            # Update both registries
            azure_blob_registry[file_id] = blob_info
            file_registry[file_id] = {
                'path': None,
                'filename': display_filename,
                'created_at': timezone.now(),
                'access_count': 0,
                'expires_at': expires_at,
                'is_azure_blob': True,
                'blob_name': blob_name,
                'blob_url': blob_url
            }
            
            # Save both registries
            save_registry()
            
            # Log the success
            logger.info(f"File saved to Azure: ID={file_id}, blob={blob_name}")
            
            # Return both file_id and URL
            return {"file_id": file_id, "url": blob_url, "filename": display_filename}
            
        except Exception as e:
            logger.error(f"Azure upload failed: {str(e)}")
    
    # Original local file storage logic
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
        save_registry()
        
        # Store in database if available
        if db_available:
            try:
                StoredFile.objects.create(
                    file_id=file_id,
                    filename=os.path.basename(file_obj),
                    local_path=file_obj,
                    expires_at=timezone.now() + timedelta(hours=TEMP_FILE_EXPIRY_HOURS),
                    is_blob=False
                )
                logger.info(f"Existing file path saved to database with ID: {file_id}")
            except Exception as e:
                logger.error(f"Error saving existing path to database: {str(e)}")
        
        # Return file_id only for local files
        return {"file_id": file_id, "filename": os.path.basename(file_obj)}
    
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
    expires_at = timezone.now() + timedelta(hours=TEMP_FILE_EXPIRY_HOURS)
    
    file_registry[file_id] = {
        'path': file_path,
        'filename': filename,
        'created_at': timezone.now(),
        'access_count': 0,
        'expires_at': expires_at
    }
    
    # Store in database if available
    if db_available:
        try:
            StoredFile.objects.create(
                file_id=file_id,
                filename=filename,
                local_path=file_path,
                expires_at=expires_at,
                is_blob=False
            )
            logger.info(f"Local file saved to database with ID: {file_id}")
        except Exception as e:
            logger.error(f"Error saving local file to database: {str(e)}")
    
    # Clean up if registry is getting too large
    cleanup_old_files()
    
    # Save the updated registry
    save_registry()
    
    # Return only file_id for local files
    return {"file_id": file_id, "filename": filename}

def cleanup_old_files():
    """Clean up expired or least accessed files if registry is too large."""
    now = timezone.now()
    
    # Handle local file cleanups
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
    
    # Handle Azure blob cleanups if enabled
    if USE_AZURE_STORAGE:
        # Clean up expired blobs in our registry
        expired_blob_ids = [fid for fid, info in azure_blob_registry.items() if info['expires_at'] < now]
        for file_id in expired_blob_ids:
            if file_id in azure_blob_registry:
                try:
                    # Try to delete from Azure
                    blob_name = azure_blob_registry[file_id]['blob_name']
                    delete_blob(blob_name)
                except Exception as e:
                    logger.error(f"Error deleting expired Azure blob: {str(e)}")
                # Remove from registry regardless
                del azure_blob_registry[file_id]
        
        # Run Azure blob cleanup function to delete any orphaned blobs
        try:
            cleanup_expired_blobs()
        except Exception as e:
            logger.error(f"Error cleaning up expired Azure blobs: {str(e)}")
    
    # Save the updated registry
    if expired_ids or len(file_registry) > FILE_CLEANUP_THRESHOLD or (USE_AZURE_STORAGE and expired_blob_ids):
        save_registry()

def delete_file(file_id):
    """Delete a file from the registry and filesystem."""
    # Check if it's an Azure blob
    if USE_AZURE_STORAGE and file_id in azure_blob_registry:
        try:
            # Delete from Azure
            blob_name = azure_blob_registry[file_id]['blob_name']
            delete_blob(blob_name)
            # Remove from registry
            del azure_blob_registry[file_id]
            save_registry()
            return True
        except Exception as e:
            logger.error(f"Error deleting Azure blob: {str(e)}")
            # Continue to check local files in case of fallback
    
    # Check local file
    if file_id in file_registry:
        file_path = file_registry[file_id]['path']
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file {file_path}")
            else:
                logger.warning(f"File to delete does not exist: {file_path}")
        except (OSError, IOError) as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
        
        del file_registry[file_id]
        save_registry()
        return True
    
    return False

def get_file_response(file_id, as_attachment=True):
    """Generate a FileResponse for a registered file."""
    logger.debug(f"Fetching file with ID: {file_id}")
    
    # Check if it's an Azure blob
    if USE_AZURE_STORAGE and file_id in azure_blob_registry:
        # For Azure blobs, we'll redirect to the blob URL
        try:
            blob_info = azure_blob_registry[file_id]
            # Check if URL is still valid or needs refresh
            if 'expires_at' in blob_info and blob_info['expires_at'] < timezone.now():
                # URL is expired, refresh it
                try:
                    blob_url = get_blob_sas_url(blob_info['blob_name'])
                    blob_info['blob_url'] = blob_url
                    blob_info['expires_at'] = timezone.now() + timedelta(hours=settings.AZURE_BLOB_EXPIRY_HOURS)
                    save_registry()
                except Exception as e:
                    logger.error(f"Error refreshing Azure blob URL: {str(e)}")
                    # Try to fall back to local file if it exists
                    if file_id in file_registry:
                        return get_file_response_local(file_id, as_attachment)
                    return None
            
            # Return redirect response to the blob URL
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(blob_info['blob_url'])
        
        except Exception as e:
            logger.error(f"Error creating response for Azure blob: {str(e)}")
            # Try to fall back to local file if it exists
            if file_id in file_registry:
                return get_file_response_local(file_id, as_attachment)
            return None
    
    # If not Azure or fallback, use local file response
    return get_file_response_local(file_id, as_attachment)

def get_file_response_local(file_id, as_attachment=True):
    """Generate a FileResponse for a local file (original implementation)."""
    logger.debug(f"Fetching local file with ID: {file_id}")
    
    if file_id not in file_registry:
        # Try to reload registry
        logger.warning(f"File ID {file_id} not found in registry, reloading")
        load_registry()
        
        if file_id not in file_registry:
            logger.warning(f"File ID {file_id} still not found after reload")
            return None
    
    file_info = file_registry[file_id]
    
    # Normalize path for Azure
    file_path = normalize_azure_path(file_info['path'])
    file_info['path'] = file_path  # Update registry entry with normalized path
    
    logger.debug(f"File path from registry (normalized): {file_path}")
    
    if not os.path.exists(file_path):
        logger.warning(f"File doesn't exist at normalized path: {file_path}")
        
        # Check if the filename exists in the temp dir (registry might have wrong path)
        filename = file_info['filename']
        potential_path = get_temp_path(filename)
        if os.path.exists(potential_path):
            logger.info(f"Found file at alternative path: {potential_path}")
            # Update registry with correct path
            file_info['path'] = potential_path
            file_path = potential_path
            save_registry()
        else:
            logger.error(f"File not found at alternative path either: {potential_path}")
            delete_file(file_id)  # Clean up registry entry
            return None
    
    # Update access stats
    file_info['access_count'] += 1
    file_info['expires_at'] = timezone.now() + timedelta(hours=TEMP_FILE_EXPIRY_HOURS)
    save_registry()
    
    try:
        # Open the file with explicit encoding to handle potential issues
        file_obj = open(file_path, 'rb')
        response = FileResponse(
            file_obj,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        if as_attachment:
            response['Content-Disposition'] = f'attachment; filename="{file_info["filename"]}"'
        
        logger.info(f"Successfully created response for file: {file_id}")
        return response
    except Exception as e:
        logger.error(f"Error creating file response: {str(e)}")
        return None

def get_file_url(file_id, request=None):
    """Generate a URL for downloading a file."""
    # Check if it's an Azure blob
    if USE_AZURE_STORAGE and file_id in azure_blob_registry:
        # For Azure blobs, we can return the direct blob URL
        blob_info = azure_blob_registry[file_id]
        
        # Check if URL is still valid or needs refresh
        if 'expires_at' in blob_info and blob_info['expires_at'] < timezone.now():
            # URL is expired, refresh it
            try:
                blob_url = get_blob_sas_url(blob_info['blob_name'])
                blob_info['blob_url'] = blob_url
                blob_info['expires_at'] = timezone.now() + timedelta(hours=settings.AZURE_BLOB_EXPIRY_HOURS)
                save_registry()
                return blob_url
            except Exception as e:
                logger.error(f"Error refreshing Azure blob URL: {str(e)}")
                # Fall back to API URL
        
        return blob_info['blob_url']
    
    # Fix for local files - use the download endpoint instead of direct for better compatibility
    if request:
        # Ensure no double slashes by using urljoin
        base_url = f"{request.scheme}://{request.get_host()}"
        return urljoin(base_url, f"api/v1/files/download/{file_id}/")
    else:
        return f"/api/v1/files/download/{file_id}/"

def get_file_metadata(file_id):
    """Get metadata for a file."""
    # Check if it's an Azure blob
    if USE_AZURE_STORAGE and file_id in azure_blob_registry:
        info = azure_blob_registry[file_id]
        return {
            'filename': info['filename'],
            'created_at': info['created_at'].isoformat(),
            'expires_at': info['expires_at'].isoformat(),
            'storage_type': 'azure_blob'
        }
    
    # Fall back to original implementation for local files
    if file_id not in file_registry:
        return None
    
    info = file_registry[file_id]
    return {
        'filename': info['filename'],
        'created_at': info['created_at'].isoformat(),
        'expires_at': info['expires_at'].isoformat(),
        'access_count': info['access_count'],
        'storage_type': 'local'
    }

def get_excel_data(file_id, sheet_name=None):
    """Get data from an Excel file as a dict."""
    # For Azure blobs
    if USE_AZURE_STORAGE and file_id in azure_blob_registry:
        try:
            info = azure_blob_registry[file_id]
            blob_url = info['blob_url']
            
            # Use a unique temp file for each request
            import tempfile
            import random
            import time
            
            # Create a temporary file with more unique name to avoid conflicts
            temp_name = f"excel_{time.time()}_{random.randint(1000,9999)}.xlsx"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{temp_name}")
            
            try:
                # Download the file
                import requests
                response = requests.get(blob_url)
                response.raise_for_status()
                
                # Write to temp file
                with open(temp_file.name, 'wb') as f:
                    f.write(response.content)
                
                # Close the file before reading
                f.close()
                
                # Read with pandas
                result = pd.read_excel(temp_file.name, sheet_name=sheet_name)
                if sheet_name is None:
                    # Handle multiple sheets
                    result_dict = {}
                    with pd.ExcelFile(temp_file.name) as xls:
                        for s in xls.sheet_names:
                            result_dict[s] = pd.read_excel(xls, sheet_name=s).to_dict(orient="records")
                    return result_dict
                else:
                    return result.to_dict(orient="records")
                    
            finally:
                # Make sure to properly close and delete the temp file
                try:
                    if os.path.exists(temp_file.name):
                        # Don't use temp_file.handle, just close and remove
                        temp_file.close()
                        os.unlink(temp_file.name)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to clean up temp file: {str(cleanup_err)}")
                    
        except Exception as e:
            logger.error(f"Error reading Excel file from Azure blob: {str(e)}")
            # Try to fall back to local file if it exists
            if file_id in file_registry:
                pass  # Continue to local file logic
            else:
                return None
    
    # Original implementation for local files
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
        logger.error(f"Error reading Excel file: {str(e)}")
        return None

def get_file_content_base64(file_id):
    """Get file content as base64 encoded string."""
    # For Azure blobs, we need to download the file first
    if USE_AZURE_STORAGE and file_id in azure_blob_registry:
        try:
            info = azure_blob_registry[file_id]
            blob_url = info['blob_url']
            
            # Download the file
            import requests
            response = requests.get(blob_url)
            response.raise_for_status()
            
            # Return base64 encoded content
            return base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting base64 content from Azure blob: {str(e)}")
            # Try to fall back to local file if it exists
            if file_id in file_registry:
                pass  # Continue to local file logic
            else:
                return None
    
    # Original implementation for local files
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
        logger.error(f"Error encoding file: {str(e)}")
        return None

def get_blob_url_by_filename(filename):
    """Find a blob URL by filename as fallback."""
    for file_id, info in azure_blob_registry.items():
        if info.get('filename') == filename:
            logger.info(f"Found blob by filename: {filename}, ID: {file_id}")
            return info.get('blob_url')
    return None

def download_file(request, file_id):
    """Generate a FileResponse for a registered file."""
    logger.info(f"File download requested: {file_id}")
    
    # Check if file exists in Azure registry
    if USE_AZURE_STORAGE and file_id in azure_blob_registry:
        # Get the blob URL and redirect directly to it
        blob_info = azure_blob_registry[file_id]
        blob_url = blob_info['blob_url']
        
        # Check if URL is expired and refresh if needed
        if blob_info['expires_at'] < timezone.now():
            try:
                blob_url = get_blob_sas_url(blob_info['blob_name'])
                blob_info['blob_url'] = blob_url
                blob_info['expires_at'] = timezone.now() + timedelta(hours=settings.AZURE_BLOB_EXPIRY_HOURS)
                save_registry()
            except Exception as e:
                logger.error(f"Error refreshing blob URL: {str(e)}")
        
        # Redirect to the blob URL
        from django.http import HttpResponseRedirect
        logger.info(f"Redirecting to Azure blob URL for file ID: {file_id}")
        return HttpResponseRedirect(blob_url)
    
