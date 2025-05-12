import os
import base64
import pandas as pd
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .sqp_processor import process_sqp_file
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
def process_sqp(request):
    """Process a Search Query Performance CSV or Excel file and return analysis results."""
    if request.method == "OPTIONS":
        return create_response(request, {})
        
    try:
        # File validation
        file = request.FILES.get('file')
        if not file:
            return create_response(request, {"error": "No file uploaded"}, 400)
        
        # Accept CSV and Excel files
        valid_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = os.path.splitext(file.name.lower())[1]
        if file_extension not in valid_extensions:
            return create_response(
                request, 
                {"error": f"Invalid file type. Only CSV and Excel files are supported (.csv, .xlsx, .xls)."}, 
                400
            )
        
        # Setup file paths using get_temp_path to ensure proper directory structure
        temp_file_path = get_temp_path(file.name)
        output_file_path = get_temp_path(f"SQP_Analysis_{os.path.splitext(file.name)[0]}.xlsx")
        
        logger.info(f"Processing SQP file: {file.name}")
        logger.info(f"Temp file path: {temp_file_path}")
        logger.info(f"Output file path: {output_file_path}")
        
        # Save uploaded file temporarily
        with open(temp_file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Process the file
        try:
            result = process_sqp_file(temp_file_path, output_file_path)
            sqp_kw = result.get("sqp_kw", [])
            
            # Convert numpy array to list if needed and ensure it's not empty
            if hasattr(sqp_kw, 'tolist'):
                sqp_kw = sqp_kw.tolist()
            
            # Ensure we have keywords
            if len(sqp_kw) == 0 and "target_df" in result and not result["target_df"].empty:
                # Fallback to extract keywords from target_df if sqp_kw is empty
                sqp_kw = result["target_df"]["Search Query"].unique().tolist()
                
            logger.info(f"SQP processing successful, found {len(sqp_kw)} keywords")
        except Exception as e:
            logger.error(f"Error processing SQP file: {str(e)}")
            return create_response(request, {"error": f"Error processing file: {str(e)}"}, 500)
        
        if not os.path.exists(output_file_path):
            logger.error(f"Output file not created: {output_file_path}")
            return create_response(request, {"error": "Failed to generate output file"}, 500)
        
        # Save file to file service and get its ID
        file_result = save_temp_file(output_file_path, f"SQP_Analysis_{os.path.splitext(file.name)[0]}.xlsx")
        logger.info(f"Saved output file with ID: {file_result['file_id']}")
            
        # Extract data from the output Excel file for JSON response
        result_data = get_excel_data(file_result['file_id'])
        
        # Remove the Keywords sheet since it's redundant with the keywords field
        if result_data and 'Keywords' in result_data:
            del result_data['Keywords']
            
        # Create response with JSON data and file reference
        response_data = {
            'data': result_data,
            'keywords': sqp_kw,
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
        
        logger.error(f"Unexpected error in SQP processing: {str(e)}")
        return create_response(request, {"error": f"Unexpected error: {str(e)}"}, 500) 