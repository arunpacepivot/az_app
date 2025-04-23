from django.http import JsonResponse, Http404, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
import os
import logging
from .file_service import (
    get_file_response, 
    delete_file,
    get_file_metadata,
    file_registry,
    load_registry,
    get_temp_path,
    normalize_azure_path,
    AZURE_TEMP_PATH
)

# Set up logger
logger = logging.getLogger('file_service')

def create_response(data, status=200):
    """Create a consistent response format."""
    response = {
        "data": data,
        "status": status
    }
    return JsonResponse(response, status=status, safe=False)

@csrf_exempt
@api_view(['GET', 'OPTIONS'])
@require_http_methods(['GET', 'OPTIONS'])
def download_file(request, file_id):
    """Stream a file for download."""
    if request.method == "OPTIONS":
        return create_response({})
    
    logger.info(f"File download requested: {file_id}")
    
    # Force reload of registry to ensure we have latest data
    load_registry()
    
    # Check if file exists in registry
    if file_id not in file_registry:
        logger.warning(f"File ID not found in registry: {file_id}")
        # Add debugging for available files
        logger.info(f"Available files in registry: {list(file_registry.keys())}")
        return create_response({"error": "File not found in registry", "file_id": file_id}, 404)
    
    # Get file path and check if file exists on disk
    file_info = file_registry[file_id]
    file_path = normalize_azure_path(file_info['path'])  # Normalize path
    file_info['path'] = file_path  # Update the normalized path in registry
    filename = file_info['filename']
    
    logger.info(f"Looking for file: {filename} at path: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File exists in registry but not on disk: {file_path}")
        
        # Try alternative paths
        alt_path = get_temp_path(filename)
        logger.info(f"Checking alternative path: {alt_path}")
        
        if os.path.exists(alt_path):
            logger.info(f"Found file at alternative path: {alt_path}")
            file_info['path'] = alt_path
            file_path = alt_path
        else:
            # Try standard temp paths in Azure
            standard_paths = [
                os.path.join(AZURE_TEMP_PATH, filename),
                os.path.join('/home/site/wwwroot/temp_files', filename),
                os.path.join('/tmp', filename)
            ]
            
            found = False
            for std_path in standard_paths:
                if os.path.exists(std_path):
                    logger.info(f"Found file at standard path: {std_path}")
                    file_info['path'] = std_path
                    file_path = std_path
                    found = True
                    break
            
            if not found:
                # Last attempt - scan ALL files in temp directory
                logger.info("Scanning entire temp directory for the file...")
                temp_dir = os.path.dirname(file_path)
                
                try:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file == filename:
                                found_path = os.path.join(root, file)
                                logger.info(f"Found file in directory scan: {found_path}")
                                file_info['path'] = found_path
                                file_path = found_path
                                found = True
                                break
                        if found:
                            break
                except Exception as e:
                    logger.error(f"Error scanning for file: {e}")
                
                if not found:
                    # File truly does not exist
                    return create_response({
                        "error": "File exists in registry but not on disk",
                        "file_id": file_id,
                        "filename": filename,
                        "path": file_path
                    }, 404)
    
    logger.info(f"Serving file: {file_info['filename']} (path: {file_path})")
    
    # Get file response
    response = get_file_response(file_id)
    if response:
        logger.info(f"Successfully generated response for file: {file_id}")
        return response
    else:
        logger.error(f"Failed to generate response for file: {file_id}")
        return create_response({"error": "File found but could not be served"}, 500)

@csrf_exempt
@api_view(['GET', 'OPTIONS'])
@require_http_methods(['GET', 'OPTIONS'])
def file_info(request, file_id):
    """Get metadata for a file."""
    if request.method == "OPTIONS":
        return create_response({})
        
    metadata = get_file_metadata(file_id)
    if metadata:
        return create_response(metadata)
    else:
        return create_response({"error": "File not found"}, 404)

@csrf_exempt
@api_view(['DELETE', 'OPTIONS'])
@require_http_methods(['DELETE', 'OPTIONS'])
def remove_file(request, file_id):
    """Delete a file."""
    if request.method == "OPTIONS":
        return create_response({})
        
    success = delete_file(file_id)
    if success:
        return create_response({"message": "File deleted successfully"})
    else:
        return create_response({"error": "File not found"}, 404) 