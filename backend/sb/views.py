from django.shortcuts import render
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
from .header import final_sb_optimisation
import base64
from core.file_service import save_temp_file, get_excel_data, get_file_url


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
def process_sbads(request):
    if request.method == "OPTIONS":
        return create_response(request, {})
        
    try:
        # Validate files
        bulk_file = request.FILES.get('bulk_file')
        campaign_file = request.FILES.get('campaign_file')
        
        if not bulk_file:
            return create_response(request, {"error": "No bulk file uploaded"}, 400)
        if not campaign_file:
            return create_response(request, {"error": "No campaign file uploaded"}, 400)
            
        if not bulk_file.name.endswith(".xlsx"):
            return create_response(request, {"error": "Invalid bulk file type"}, 400)
        if not campaign_file.name.endswith(".xlsx"):
            return create_response(request, {"error": "Invalid campaign file type"}, 400)
        
        # ACOS validation
        try:
            target_acos = float(request.POST.get('target_acos', 0.30))
            if target_acos <= 0:
                return create_response(request, {"error": "Invalid target ACOS"}, 400)
        except ValueError:
            return create_response(request, {"error": "Invalid target ACOS format"}, 400)
        
        # Save files temporarily
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        bulk_file_path = os.path.join(temp_dir, bulk_file.name)
        campaign_file_path = os.path.join(temp_dir, campaign_file.name)
        output_file_path = os.path.join(temp_dir, f"SB_Output_{bulk_file.name}")
        
        with open(bulk_file_path, 'wb+') as destination:
            for chunk in bulk_file.chunks():
                destination.write(chunk)
                
        with open(campaign_file_path, 'wb+') as destination:
            for chunk in campaign_file.chunks():
                destination.write(chunk)
        
        # Define sheet names
        bulk_sheet = request.POST.get('bulk_sheet', "Sponsored Brands Campaigns")
        str_sheet = request.POST.get('str_sheet', "SB Search Term Report")
        campaign_sheet = request.POST.get('campaign_sheet', "Sponsored_Brands_Campaign_place")
        
        # Process the data
        final_sb_optimisation(bulk_file_path, bulk_sheet, str_sheet, output_file_path, 
                              target_acos, campaign_file_path, campaign_sheet)
        
        if not os.path.exists(output_file_path):
            return create_response(request, {"error": "Failed to process the file"}, 500)
        
        # Save file to file service and get its ID    
        file_result = save_temp_file(output_file_path, f"Optimized_SB_{bulk_file.name}")
            
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
        if os.path.exists(bulk_file_path):
            os.remove(bulk_file_path)
        if os.path.exists(campaign_file_path):
            os.remove(campaign_file_path)
            
        return create_response(request, response_data)

    except Exception as e:
        # Clean up any temporary files
        for file_path in [bulk_file_path, campaign_file_path]:
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
