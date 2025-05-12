import os
import base64
import pandas as pd
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .cerebro_processor import process_cerebro_file
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
def process_cerebro(request):
    """Process a Cerebro Excel file and return analysis results."""
    if request.method == "OPTIONS":
        return create_response(request, {})
        
    try:
        # File validation
        file = request.FILES.get('file')
        if not file:
            return create_response(request, {"error": "No file uploaded"}, 400)
        if not file.name.endswith(".xlsx"):
            return create_response(request, {"error": "Invalid file type. Only .xlsx files are supported."}, 400)
        
        # Get parameters
        min_search_volume = float(request.POST.get('min_search_volume', 100))
        
        # Setup file paths using get_temp_path to ensure proper directory structure
        temp_file_path = get_temp_path(file.name)
        output_file_path = get_temp_path(f"Cerebro_Analysis_{file.name}")
        
        logger.info(f"Processing Cerebro file: {file.name}")
        logger.info(f"Temp file path: {temp_file_path}")
        logger.info(f"Output file path: {output_file_path}")
        
        # Save uploaded file temporarily
        with open(temp_file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Process the file
        try:
            combined_df, cerebro_kw = process_cerebro_file(temp_file_path, output_file_path, min_search_volume)
            logger.info(f"Cerebro processing successful")
        except Exception as e:
            logger.error(f"Error processing Cerebro file: {str(e)}")
            return create_response(request, {"error": f"Error processing file: {str(e)}"}, 500)
        
        if not os.path.exists(output_file_path):
            logger.error(f"Output file not created: {output_file_path}")
            return create_response(request, {"error": "Failed to generate output file"}, 500)
        
        # Save file to file service and get its ID
        file_result = save_temp_file(output_file_path, f"Cerebro_Analysis_{file.name}")
        logger.info(f"Saved output file with ID: {file_result['file_id']}")
            
        # Extract data from the output Excel file for JSON response
        result_data = get_excel_data(file_result['file_id'])
        
        # Create response with JSON data and file reference
        response_data = {
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
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        logger.error(f"Unexpected error in Cerebro processing: {str(e)}")
        return create_response(request, {"error": f"Unexpected error: {str(e)}"}, 500) 