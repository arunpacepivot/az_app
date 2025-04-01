﻿from django.shortcuts import render
from rest_framework import viewsets
from .models import ProcessedFile
from .serializers import ProcessedFileSerializer
import re
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods
import json
import pandas as pd
import os
import fuzzywuzzy
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from .header import load_and_process_reports
import base64


class ProcessedFileViewSet(viewsets.ModelViewSet):
    queryset = ProcessedFile.objects.all()
    serializer_class = ProcessedFileSerializer

@ensure_csrf_cookie
@require_http_methods(['GET', 'OPTIONS'])
def get_csrf(request):
    if request.method == "OPTIONS":
        response = JsonResponse({})
    else:
        response = JsonResponse({'csrfToken': get_token(request)})
    
    response["Access-Control-Allow-Origin"] = request.headers.get('Origin')
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
    return response


@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@parser_classes([MultiPartParser, FormParser])
@require_http_methods(['POST', 'OPTIONS'])
def process_sdads(request):
    if request.method == "OPTIONS":
        return create_response(request, {})
        
    try:
        # File validation
        file = request.FILES.get('file')
        if not file:
            return create_response(request, {"error": "No file uploaded"}, 400)
        if not file.name.endswith(".xlsx"):
            return create_response(request, {"error": "Invalid file type"}, 400)
        
        # ACOS validation
        try:
            target_acos = float(request.POST.get('target_acos', 0.30))
            if target_acos <= 0:
                return create_response(request, {"error": "Invalid target ACOS"}, 400)
        except ValueError:
            return create_response(request, {"error": "Invalid target ACOS format"}, 400)
        
        # Save the uploaded file temporarily
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file_path = os.path.join(temp_dir, file.name)
        output_file_path = os.path.join(temp_dir, f"SD_Output_{file.name}")
        
        with open(temp_file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Define sheet name
        sheet_name = request.POST.get('sheet_name', "Sponsored Display Campaigns")
        
        # Process the data
        load_and_process_reports(temp_file_path, sheet_name, output_file_path, target_acos)
        
        if not os.path.exists(output_file_path):
            return create_response(request, {"error": "Failed to process the file"}, 500)
            
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
            'excel_file': {
                'filename': f"Optimized_SD_{file.name}",
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


def create_response(request, data, status=200):
    response = JsonResponse(data, safe=False, status=status)
    response["Access-Control-Allow-Origin"] = request.headers.get('Origin')
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
    return response 
