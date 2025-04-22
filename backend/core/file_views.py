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
    load_registry
)

# Set up logger
logger = logging.getLogger(__name__)

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
        return create_response({"error": "File not found in registry"}, 404)
    
    # Get file path and check if file exists on disk
    file_info = file_registry[file_id]
    file_path = file_info['path']
    
    if not os.path.exists(file_path):
        logger.error(f"File exists in registry but not on disk: {file_path}")
        return create_response({"error": "File exists in registry but not on disk"}, 404)
    
    logger.info(f"Serving file: {file_info['filename']} (path: {file_path})")
    
    # Get file response
    response = get_file_response(file_id)
    if response:
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