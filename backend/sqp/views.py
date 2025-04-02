import os
import base64
import pandas as pd
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .sqp_processor import process_sqp_file

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
    """Process a Search Query Performance CSV file and return analysis results."""
    if request.method == "OPTIONS":
        return create_response(request, {})
        
    try:
        # File validation
        file = request.FILES.get('file')
        if not file:
            return create_response(request, {"error": "No file uploaded"}, 400)
        if not file.name.endswith(".csv"):
            return create_response(request, {"error": "Invalid file type. Only .csv files are supported."}, 400)
        
        # Setup file paths
        temp_file_path = os.path.join('temp', file.name)
        output_file_path = os.path.join('temp', f"SQP_Analysis_{file.name.replace('.csv', '.xlsx')}")
        
        # Create temp directory if it doesn't exist
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        
        # Save uploaded file temporarily
        with open(temp_file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Process the file
        try:
            result = process_sqp_file(temp_file_path, output_file_path)
            sqp_kw = result["sqp_kw"]
        except Exception as e:
            return create_response(request, {"error": f"Error processing file: {str(e)}"}, 500)
        
        if not os.path.exists(output_file_path):
            return create_response(request, {"error": "Failed to generate output file"}, 500)
            
        # Extract data from the output Excel file for JSON response
        result_data = {}
        with pd.ExcelFile(output_file_path) as xls:
            for sheet_name in xls.sheet_names:
                result_data[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name).to_dict(orient="records")
        
        # Get base64 encoded Excel file
        with open(output_file_path, 'rb') as excel_file:
            encoded_excel = base64.b64encode(excel_file.read()).decode('utf-8')
        
        # Create response with both JSON data and Excel file
        response_data = {
            'data': result_data,
            'keywords': sqp_kw.tolist(),
            'excel_file': {
                'filename': f"SQP_Analysis_{file.name.replace('.csv', '.xlsx')}",
                'content': encoded_excel,
                'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        }
        
        # Clean up temporary files
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(output_file_path):
            os.remove(output_file_path)
            
        return create_response(request, response_data)

    except Exception as e:
        # Clean up any temporary files
        for file_path in [temp_file_path, output_file_path]:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
                
        return create_response(request, {"error": f"Unexpected error: {str(e)}"}, 500) 