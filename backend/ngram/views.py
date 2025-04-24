import os
import base64
import pandas as pd
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .ngram_processor import process_ngram_file
from core.file_service import save_temp_file, get_excel_data, get_file_url, get_temp_path

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
def process_ngram(request):
    """Process a bulk Excel file and return n-gram analysis results."""
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
        output_file_path_sk = get_temp_path(f"ngram_analysis_results_by_asin_sk_{file.name}")
        output_file_path_mk = get_temp_path(f"ngram_analysis_results_by_asin_mk_{file.name}")
        
        # Save uploaded file temporarily
        with open(temp_file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Get target ACOS from request parameters
        target_acos = float(request.data.get('target_acos', 0.2))
                
        # Process the file
        try:
            result = process_ngram_file(temp_file_path, output_file_path_sk, output_file_path_mk, target_acos)
        except Exception as e:
            return create_response(request, {"error": f"Error processing file: {str(e)}"}, 500)
        
        if not (os.path.exists(output_file_path_sk) and os.path.exists(output_file_path_mk)):
            return create_response(request, {"error": "Failed to generate output files"}, 500)
        
        # Save files to file service and get their IDs
        file_result_sk = save_temp_file(output_file_path_sk, f"ngram_analysis_results_by_asin_sk_{file.name}")
        file_result_mk = save_temp_file(output_file_path_mk, f"ngram_analysis_results_by_asin_mk_{file.name}")
        
        # Extract data from the output Excel files for JSON response
        result_data = {}
        
        # Read B0 ASINs data
        sk_data = get_excel_data(file_result_sk['file_id'])
        mk_data = get_excel_data(file_result_mk['file_id'])
        
        if sk_data:
            for sheet_name, sheet_data in sk_data.items():
                if sheet_name not in result_data:
                    result_data[sheet_name] = []
                for record in sheet_data:
                    record["file_source"] = "B0_ASINs"
                    result_data[sheet_name].append(record)
                    
        if mk_data:
            for sheet_name, sheet_data in mk_data.items():
                if sheet_name not in result_data:
                    result_data[sheet_name] = []
                for record in sheet_data:
                    record["file_source"] = "non_B0_ASINs"
                    result_data[sheet_name].append(record)
        
        # Create response with file URLs and JSON data
        response_data = {
            'status': result.get('status', 'success'),
            'message': result.get('message', 'N-gram analysis completed successfully'),
            'sk_asin_count': result.get('sk_asin_count', 0),
            'mk_asin_count': result.get('mk_asin_count', 0),
            'data': result_data,
            'files': [
                {
                    'filename': file_result_sk['filename'],
                    'url': file_result_sk.get('url') or get_file_url(file_result_sk['file_id'], request),
                    'file_id': file_result_sk['file_id'],
                    'type': 'B0 ASINs'
                },
                {
                    'filename': file_result_mk['filename'],
                    'url': file_result_mk.get('url') or get_file_url(file_result_mk['file_id'], request),
                    'file_id': file_result_mk['file_id'],
                    'type': 'Non-B0 ASINs'
                }
            ]
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
                
        return create_response(request, {"error": f"Unexpected error: {str(e)}"}, 500) 