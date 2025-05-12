import os
import uuid
import logging
from datetime import datetime, timedelta
from django.conf import settings
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
import tempfile

# Set up logger
logger = logging.getLogger('file_service')

# Configuration with default values
# These should be set in settings.py and accessed here
AZURE_STORAGE_CONNECTION_STRING = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', None)
AZURE_CONTAINER_NAME = getattr(settings, 'AZURE_CONTAINER_NAME', 'tempfiles')
AZURE_BLOB_EXPIRY_HOURS = getattr(settings, 'AZURE_BLOB_EXPIRY_HOURS', 4)  # Files expire after 4 hours

def get_blob_service_client():
    """Get Azure Blob Service client from connection string."""
    if not AZURE_STORAGE_CONNECTION_STRING:
        logger.error("Azure Storage connection string not configured")
        raise ValueError("Azure Storage connection string not configured")
    
    return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

def ensure_container_exists():
    """Ensure the container exists in Azure Blob Storage."""
    try:
        client = get_blob_service_client()
        container_client = client.get_container_client(AZURE_CONTAINER_NAME)
        
        # Try to get container properties to check if it exists
        container_client.get_container_properties()
        logger.debug(f"Container '{AZURE_CONTAINER_NAME}' already exists")
        
        return container_client
    except ResourceNotFoundError:
        # Container doesn't exist, create it
        logger.info(f"Container '{AZURE_CONTAINER_NAME}' not found, creating")
        try:
            client = get_blob_service_client()
            container_client = client.create_container(AZURE_CONTAINER_NAME)
            logger.info(f"Created container '{AZURE_CONTAINER_NAME}'")
            return container_client
        except ResourceExistsError:
            # Handle race condition where container was created between check and create
            logger.info(f"Container '{AZURE_CONTAINER_NAME}' already exists (race condition)")
            return client.get_container_client(AZURE_CONTAINER_NAME)
        except Exception as e:
            logger.error(f"Failed to create container: {str(e)}")
            raise

def upload_blob(file_obj, custom_filename=None):
    """
    Upload a file to Azure Blob Storage.
    
    Args:
        file_obj: A file-like object, path string, or Django uploaded file
        custom_filename: Optional custom filename to use
    
    Returns:
        tuple: (blob_name, blob_url)
    """
    try:
        # Generate a unique blob name if none provided
        if custom_filename:
            blob_name = custom_filename
        else:
            # Get file extension
            if hasattr(file_obj, 'name'):
                file_extension = os.path.splitext(file_obj.name)[1]
            elif isinstance(file_obj, str) and os.path.exists(file_obj):
                file_extension = os.path.splitext(file_obj)[1]
            else:
                file_extension = '.tmp'
            
            # Create unique blob name with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            blob_name = f"{timestamp}_{uuid.uuid4().hex}{file_extension}"
        
        # Ensure container exists
        container_client = ensure_container_exists()
        
        # Get blob client
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload the file
        if hasattr(file_obj, 'chunks'):
            # Django uploaded file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            try:
                for chunk in file_obj.chunks():
                    temp_file.write(chunk)
                temp_file.close()
                
                with open(temp_file.name, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
            finally:
                # Clean up temp file
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                    
        elif hasattr(file_obj, 'read'):
            # File-like object
            blob_client.upload_blob(file_obj, overwrite=True)
            
        elif isinstance(file_obj, str) and os.path.exists(file_obj):
            # Path string
            with open(file_obj, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
                
        else:
            raise ValueError("Unsupported file object type")
        
        # Set blob metadata with expiry information
        expiry_time = datetime.utcnow() + timedelta(hours=AZURE_BLOB_EXPIRY_HOURS)
        metadata = {
            'expires_at': expiry_time.isoformat(),
            'original_filename': custom_filename or getattr(file_obj, 'name', blob_name)
        }
        blob_client.set_blob_metadata(metadata)
        
        # Generate SAS URL with expiry
        blob_url = get_blob_sas_url(blob_name, expiry_time)
        
        logger.info(f"Uploaded blob '{blob_name}' successfully")
        return blob_name, blob_url
        
    except Exception as e:
        logger.error(f"Error uploading to Azure Blob Storage: {str(e)}")
        raise

def get_blob_sas_url(blob_name, expiry_time=None):
    """
    Generate a SAS URL for a blob with expiry time.
    
    Args:
        blob_name: Name of the blob
        expiry_time: Optional expiry time, defaults to 4 hours from now
    
    Returns:
        str: SAS URL for the blob
    """
    if not expiry_time:
        expiry_time = datetime.utcnow() + timedelta(hours=AZURE_BLOB_EXPIRY_HOURS)
    
    try:
        # Parse connection string to extract account info
        conn_str = AZURE_STORAGE_CONNECTION_STRING
        # Split connection string and convert to dictionary
        parts = {
            part.split('=', 1)[0]: part.split('=', 1)[1]
            for part in conn_str.split(';')
            if '=' in part
        }
        
        account_name = parts.get('AccountName')
        account_key = parts.get('AccountKey')
        
        if not account_name or not account_key:
            raise ValueError("Connection string missing AccountName or AccountKey")
            
        # Generate SAS token with explicit account key
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=AZURE_CONTAINER_NAME,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time
        )
        
        # Build URL
        blob_url = f"https://{account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{blob_name}?{sas_token}"
        return blob_url
        
    except Exception as e:
        logger.error(f"Error generating SAS URL: {str(e)}")
        raise

def delete_blob(blob_name):
    """
    Delete a blob from Azure Blob Storage.
    
    Args:
        blob_name: Name of the blob to delete
    
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # Get container client
        container_client = ensure_container_exists()
        
        # Get blob client
        blob_client = container_client.get_blob_client(blob_name)
        
        # Delete the blob
        blob_client.delete_blob()
        logger.info(f"Deleted blob '{blob_name}' successfully")
        return True
        
    except ResourceNotFoundError:
        logger.warning(f"Blob '{blob_name}' not found for deletion")
        return False
    except Exception as e:
        logger.error(f"Error deleting blob '{blob_name}': {str(e)}")
        return False

def cleanup_expired_blobs():
    """Delete blobs that have expired based on their metadata."""
    try:
        # Get container client
        container_client = ensure_container_exists()
        
        # Current time
        now = datetime.utcnow()
        
        # List all blobs
        blob_list = container_client.list_blobs(include=['metadata'])
        
        # Check each blob for expiry
        for blob in blob_list:
            if blob.metadata and 'expires_at' in blob.metadata:
                try:
                    # Parse expiry time from metadata
                    expiry_time = datetime.fromisoformat(blob.metadata['expires_at'].replace('Z', '+00:00'))
                    
                    # If expired, delete it
                    if expiry_time < now:
                        blob_client = container_client.get_blob_client(blob.name)
                        blob_client.delete_blob()
                        logger.info(f"Deleted expired blob '{blob.name}'")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid expiry time in metadata for blob '{blob.name}': {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error cleaning up expired blobs: {str(e)}")
        return False 