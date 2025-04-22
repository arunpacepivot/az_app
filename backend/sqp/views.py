import os
import base64
import pandas as pd
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .sqp_processor import process_sqp_file
from core.file_service import save_temp_file, get_excel_data, get_file_url

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
        
        # Setup file paths
        temp_file_path = os.path.join('temp', file.name)
        output_file_path = os.path.join('temp', f"SQP_Analysis_{os.path.splitext(file.name)[0]}.xlsx")
        
        # Create temp directory if it doesn't exist
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        
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
        except Exception as e:
            return create_response(request, {"error": f"Error processing file: {str(e)}"}, 500)
        
        if not os.path.exists(output_file_path):
            return create_response(request, {"error": "Failed to generate output file"}, 500)
        
        # Save file to file service and get its ID
        file_id = save_temp_file(output_file_path, f"SQP_Analysis_{os.path.splitext(file.name)[0]}.xlsx")
            
        # Extract data from the output Excel file for JSON response
        result_data = get_excel_data(file_id)
        
        # Remove the Keywords sheet since it's redundant with the keywords field
        if result_data and 'Keywords' in result_data:
            del result_data['Keywords']
            
        # Create response with JSON data and file reference
        response_data = {
            'data': result_data,
            'keywords': sqp_kw,
            'file': {
                'filename': f"SQP_Analysis_{os.path.splitext(file.name)[0]}.xlsx",
                'url': get_file_url(file_id, request),
                'file_id': file_id
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
                
        return create_response(request, {"error": f"Unexpected error: {str(e)}"}, 500) 