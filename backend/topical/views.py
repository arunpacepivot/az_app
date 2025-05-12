import os
import base64
import pandas as pd
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .topical_processor import process_topical_file
from core.file_service import save_temp_file, get_excel_data, get_file_url, get_temp_path
import logging

# Set up logger
logger = logging.getLogger(__name__)

def create_response(request, data, status=200):
    """Create a consistent response format."""
    response = {
        "data": data,
        "status": status
    }
    from django.http import JsonResponse
    return JsonResponse(response, status=status, safe=False)

@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@parser_classes([MultiPartParser, FormParser])
@require_http_methods(['POST', 'OPTIONS'])
def process_topical(request):
    """Process a bulk Excel file and return topical analysis results."""
    if request.method == "OPTIONS":
        return create_response(request, {})
        
    try:
        # File validation
        file = request.FILES.get('file')
        if not file:
            return create_response(request, {"error": "No file uploaded"}, 400)
        if not file.name.endswith((".xlsx", ".xls")):
            return create_response(request, {"error": "Invalid file type. Only Excel files are supported."}, 400)
        
        # Setup file paths using get_temp_path to ensure proper directory structure
        temp_file_path = get_temp_path(file.name)
        output_file_path = get_temp_path(f"ASIN_Top_80_Percent_Data_{file.name}")
        
        logger.info(f"Processing Topical file: {file.name}")
        logger.info(f"Temp file path: {temp_file_path}")
        logger.info(f"Output file path: {output_file_path}")
        
        # Save uploaded file temporarily
        with open(temp_file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Get target ACOS from request parameters
        target_acos = float(request.data.get('target_acos', 0.25))
                
        # Process the file
        try:
            result = process_topical_file(temp_file_path, output_file_path, target_acos)
            logger.info(f"Topical processing successful")
        except Exception as e:
            logger.error(f"Error processing Topical file: {str(e)}")
            return create_response(request, {"error": f"Error processing file: {str(e)}"}, 500)
        
        if not os.path.exists(output_file_path):
            logger.error(f"Output file not created: {output_file_path}")
            return create_response(request, {"error": "Failed to generate output file"}, 500)
        
        # Save file to file service and get its ID
        file_result = save_temp_file(output_file_path, f"ASIN_Top_80_Percent_Data_{file.name}")
        logger.info(f"Saved output file with ID: {file_result['file_id']}")
            
        # Extract data from the output Excel file for JSON response
        result_data = get_excel_data(file_result['file_id'])
        
        # Create response with file URL and JSON data
        response_data = {
            'status': result.get('status', 'success'),
            'message': result.get('message', 'Topical analysis completed successfully'),
            'b0_asin_count': result.get('b0_asin_count', 0),
            'non_b0_asin_count': result.get('non_b0_asin_count', 0),
            'data': result_data,
            'file': {
                'filename': file_result['filename'],
                'url': file_result.get('url') or get_file_url(file_result['file_id'], request),
                'file_id': file_result['file_id']
            }
        }
        
        # Clean up temporary files
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        return create_response(request, response_data)

    except Exception as e:
        # Clean up any temporary files
        temp_files = [temp_file_path]
        for file_path in temp_files:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        
        logger.error(f"Unexpected error in Topical processing: {str(e)}")
        return create_response(request, {"error": f"Unexpected error: {str(e)}"}, 500) 