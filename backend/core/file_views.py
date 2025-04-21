from django.http import JsonResponse, Http404, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from .file_service import (
    get_file_response, 
    delete_file,
    get_file_metadata
)

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
        
    response = get_file_response(file_id)
    if response:
        return response
    else:
        return create_response({"error": "File not found"}, 404)

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