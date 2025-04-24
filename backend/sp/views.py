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
from .header import final_sp_optimisation, match_headers, standardize_headers
import base64
from io import BytesIO
from core.file_service import save_temp_file, get_excel_data, get_file_url

# Import SB and SD modules (wrapped in try-except to handle potential import errors)
try:
    from sb.header import final_sb_optimisation
except ImportError:
    # Create a placeholder function to avoid errors
    def final_sb_optimisation(*args, **kwargs):
        raise ImportError("SB module is not available")

try:
    from sd.header import load_and_process_reports
except ImportError:
    # Create a placeholder function to avoid errors
    def load_and_process_reports(*args, **kwargs):
        raise ImportError("SD module is not available")

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
def process_spads(request):
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

        # Python code for Azure compatibility
        temp_dir = os.environ.get('TEMP', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp'))
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file_path = os.path.join(temp_dir, file.name)
        output_file_path = os.path.join(temp_dir, f"SP_Output_{file.name}")
        
        with open(temp_file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Verify that required sheets exist
        try:
            with pd.ExcelFile(temp_file_path) as xls:
                sheet_names = xls.sheet_names
                if "SP Search Term Report" not in sheet_names:
                    return create_response(request, {"error": "SP Search Term Report not found in the uploaded file"}, 400)
                if "Sponsored Products Campaigns" not in sheet_names:
                    return create_response(request, {"error": "Sponsored Products Campaigns not found in the uploaded file"}, 400)
                
                # Check if sheets are empty
                str_df = pd.read_excel(temp_file_path, sheet_name="SP Search Term Report")
                if str_df.empty:
                    return create_response(request, {"error": "SP Search Term Report is empty"}, 400)
                
                bulk_df = pd.read_excel(temp_file_path, sheet_name="Sponsored Products Campaigns")
                if bulk_df.empty:
                    return create_response(request, {"error": "Sponsored Products Campaigns is empty"}, 400)
        except Exception as e:
            return create_response(request, {"error": f"Error reading Excel file: {str(e)}"}, 500)

        # Process the data using the final_sp_optimisation function
        final_sp_optimisation(temp_file_path, output_file_path, target_acos, 
                             "Sponsored Products Campaigns", "SP Search Term Report")
        
        if not os.path.exists(output_file_path):
            return create_response(request, {"error": "Failed to process the file"}, 500)
            
        # Save file to file service and get its ID
        file_result = save_temp_file(output_file_path, f"Optimized_SP_{file.name}")
            
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
                
        return create_response(request, {"error": f"Unexpected error: {str(e)}"}, 500)


# Function for all optimisations - integrated with other services
@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@require_http_methods(['POST', 'OPTIONS'])
def all_optimisations(request):
    if request.method == "OPTIONS":
        return create_response(request, {})
        
    try:
        # File validation
        file = request.FILES.get('file')
        if not file:
            return create_response(request, {"error": "No file uploaded"}, 400)
        if not file.name.endswith(".xlsx"):
            return create_response(request, {"error": "Invalid file type"}, 400)
        
        # Save the file temporarily for processing
        bulk_file_path = os.path.join('temp', file.name)
        os.makedirs(os.path.dirname(bulk_file_path), exist_ok=True)
        with open(bulk_file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
                
        # Optional campaign file for SB
        campaign_file_path = None
        if 'campaign_file' in request.FILES:
            campaign_file = request.FILES.get('campaign_file')
            campaign_file_path = os.path.join('temp', campaign_file.name)
            with open(campaign_file_path, 'wb+') as destination:
                for chunk in campaign_file.chunks():
                    destination.write(chunk)
        
        # ACOS parameters
        sp_target_acos = float(request.POST.get('sp_target_acos', 0.30))
        sb_target_acos = float(request.POST.get('sb_target_acos', 0.30))
        sd_target_acos = float(request.POST.get('sd_target_acos', 0.30))

        # Sheet names
        bulk_sheet_sp = request.POST.get('bulk_sheet_sp', "Sponsored Products Campaigns")
        bulk_sheet_sb = request.POST.get('bulk_sheet_sb', "Sponsored Brands Campaigns")
        bulk_sheet_sd = request.POST.get('bulk_sheet_sd', "Sponsored Display Campaigns")
        bulk_sheet_sbr = request.POST.get('bulk_sheet_sbr', "SB Search Term Report")
        bulk_sheet_str = request.POST.get('bulk_sheet_str', "SP Search Term Report")
        campaign_sheet = request.POST.get('campaign_sheet', "Sponsored_Brands_Campaign_place")

        # Output file paths
        sp_output_file_path = os.path.join('temp', f"Output_data_SP_{file.name}")
        sb_output_file_path = os.path.join('temp', f"Output_data_SB_{file.name}")
        sd_output_file_path = os.path.join('temp', f"Output_data_SD_{file.name}")
        
        # Combined output path for the final Excel file
        combined_output_path = os.path.join('temp', f"Combined_Output_{file.name}")

        # Process each optimization type
        results = {}
        
        # Process SP optimization
        try:
            final_sp_optimisation(bulk_file_path, sp_output_file_path, sp_target_acos, bulk_sheet_sp, bulk_sheet_str)
            if os.path.exists(sp_output_file_path):
                results["sp"] = {"status": "success", "path": sp_output_file_path}
            else:
                results["sp"] = {"status": "error", "message": "Failed to generate SP output file"}
        except Exception as e:
            results["sp"] = {"status": "error", "message": str(e)}
        
        # Process SB optimization if the sb module is available
        try:
            if campaign_file_path:
                try:
                    final_sb_optimisation(bulk_file_path, bulk_sheet_sb, bulk_sheet_sbr, sb_output_file_path, sb_target_acos, campaign_file_path, campaign_sheet)
                    if os.path.exists(sb_output_file_path):
                        results["sb"] = {"status": "success", "path": sb_output_file_path}
                    else:
                        results["sb"] = {"status": "error", "message": "Failed to generate SB output file"}
                except ImportError:
                    results["sb"] = {"status": "error", "message": "SB module not available"}
            else:
                results["sb"] = {"status": "error", "message": "No campaign file provided for SB optimization"}
        except Exception as e:
            results["sb"] = {"status": "error", "message": str(e)}
        
        # Process SD optimization if the sd module is available
        try:
            try:
                load_and_process_reports(bulk_file_path, bulk_sheet_sd, sd_output_file_path, sd_target_acos)
                if os.path.exists(sd_output_file_path):
                    results["sd"] = {"status": "success", "path": sd_output_file_path}
                else:
                    results["sd"] = {"status": "error", "message": "Failed to generate SD output file"}
            except ImportError:
                results["sd"] = {"status": "error", "message": "SD module not available"}
        except Exception as e:
            results["sd"] = {"status": "error", "message": str(e)}
        
        # Combine successful outputs into a single Excel file
        with pd.ExcelWriter(combined_output_path, engine="xlsxwriter") as writer:
            # Add sheets from successful outputs
            for opt_type, result in results.items():
                if result["status"] == "success":
                    path = result["path"]
                    with pd.ExcelFile(path) as xls:
                        for sheet_name in xls.sheet_names:
                            # Add prefix to sheet name to identify source
                            prefixed_sheet_name = f"{opt_type.upper()}_{sheet_name}"
                            df = pd.read_excel(path, sheet_name=sheet_name)
                            if not df.empty:
                                df.to_excel(writer, sheet_name=prefixed_sheet_name, index=False)
        
        # Return the combined Excel file as JSON with base64 encoding
        if os.path.exists(combined_output_path):
            # Extract data from the output Excel file for JSON response
            combined_data = {}
            with pd.ExcelFile(combined_output_path) as xls:
                for sheet_name in xls.sheet_names:
                    combined_data[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name).to_dict(orient="records")
            
            # Get base64 encoded Excel file
            with open(combined_output_path, 'rb') as excel_file:
                encoded_excel = base64.b64encode(excel_file.read()).decode('utf-8')
            
            # Create response with both JSON data and Excel file
            response_data = {
                'data': combined_data,
                'results': results,  # Include individual optimization results
                'excel_file': {
                    'filename': f"Combined_Output_{file.name}",
                    'content': encoded_excel,
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }
            }
            
            # Clean up temporary files
            for path in [bulk_file_path, campaign_file_path, sp_output_file_path, sb_output_file_path, sd_output_file_path, combined_output_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass
            
            return create_response(request, response_data)
        
        if not os.path.exists(combined_output_path):
            return create_response(request, {"error": "Failed to generate combined output file"}, 500)
    
    except Exception as e:
        # Clean up any temporary files
        paths = [
            bulk_file_path if 'bulk_file_path' in locals() else None,
            campaign_file_path if 'campaign_file_path' in locals() else None,
            sp_output_file_path if 'sp_output_file_path' in locals() else None,
            sb_output_file_path if 'sb_output_file_path' in locals() else None,
            sd_output_file_path if 'sd_output_file_path' in locals() else None,
            combined_output_path if 'combined_output_path' in locals() else None
        ]
        
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
                
        return create_response(request, {"error": f"Unexpected error: {str(e)}"}, 500)


@csrf_exempt
@api_view(['POST', 'OPTIONS'])
@parser_classes([MultiPartParser, FormParser])
@require_http_methods(['POST', 'OPTIONS'])
def optimize_all(request):
    if request.method == "OPTIONS":
        return create_response(request, {})
    
    temp_file_path = None
    sp_output_path = None
    sb_output_path = None
    sd_output_path = None
    combined_output_path = None
        
    try:
        # File validation
        file = request.FILES.get('file')
        if not file:
            return create_response(request, {"error": "No file uploaded"}, 400)
        if not file.name.endswith(".xlsx"):
            return create_response(request, {"error": "Invalid file type"}, 400)
        
        # ACOS validation
        try:
            sp_target_acos = float(request.POST.get('sp_target_acos', request.POST.get('target_acos', 0.30)))
            sb_target_acos = float(request.POST.get('sb_target_acos', request.POST.get('target_acos', 0.30)))
            sd_target_acos = float(request.POST.get('sd_target_acos', request.POST.get('target_acos', 0.30)))
            
            if sp_target_acos <= 0 or sb_target_acos <= 0 or sd_target_acos <= 0:
                return create_response(request, {"error": "Invalid target ACOS value(s)"}, 400)
        except ValueError:
            return create_response(request, {"error": "Invalid target ACOS format"}, 400)

        #  Python code for Azure compatibility
        temp_dir = os.environ.get('TEMP', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp'))
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file_path = os.path.join(temp_dir, file.name)
        try:
            with open(temp_file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
        except Exception as e:
            return create_response(request, {"error": f"Failed to save uploaded file: {str(e)}"}, 500)
        
        # Check which sheets are available in the Excel file
        try:
            available_sheets = pd.ExcelFile(temp_file_path).sheet_names
        except Exception as e:
            return create_response(request, {"error": f"Failed to read Excel file: {str(e)}"}, 500)
        
        # Define sheet names
        sp_bulk_sheet = request.POST.get('sp_bulk_sheet', "Sponsored Products Campaigns")
        sp_str_sheet = request.POST.get('sp_str_sheet', "SP Search Term Report")
        sb_bulk_sheet = request.POST.get('sb_bulk_sheet', "Sponsored Brands Campaigns")
        sb_str_sheet = request.POST.get('sb_str_sheet', "SB Search Term Report")
        sb_campaign_sheet = request.POST.get('sb_campaign_sheet', "Sponsored_Brands_Campaign_place")
        sd_bulk_sheet = request.POST.get('sd_bulk_sheet', "Sponsored Display Campaigns")
        
        # Output paths
        sp_output_path = os.path.join(temp_dir, f"Output_SP_{file.name}")
        sb_output_path = os.path.join(temp_dir, f"Output_SB_{file.name}")
        sd_output_path = os.path.join(temp_dir, f"Output_SD_{file.name}")
        combined_output_path = os.path.join(temp_dir, f"Output_Combined_{file.name}")
        
        # Process results
        results = {}
        sp_success = False
        sb_success = False
        sd_success = False
        
        # Process SP if sheets are available
        if sp_bulk_sheet in available_sheets and sp_str_sheet in available_sheets:
            try:
                # Process the data
                final_sp_optimisation(temp_file_path, sp_output_path, sp_target_acos, sp_bulk_sheet, sp_str_sheet)
                if os.path.exists(sp_output_path):
                    sp_success = True
                    
                    # Extract processed data for JSON
                    sp_processed_dfs = {}
                    with pd.ExcelFile(sp_output_path) as xls:
                        for sheet_name in xls.sheet_names:
                            sp_processed_dfs[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name).to_dict(orient="records")
                    
                    results['sp'] = {
                        'success': True,
                        'data': sp_processed_dfs
                    }
                else:
                    results['sp'] = {
                        'success': False,
                        'error': "Failed to process SP data"
                    }
            except Exception as e:
                results['sp'] = {
                    'success': False,
                    'error': str(e)
                }
        else:
            results['sp'] = {
                'success': False,
                'error': "Required SP sheets not found in the uploaded file"
            }
        
        # Process SB if sheets are available
        if sb_bulk_sheet in available_sheets and sb_str_sheet in available_sheets and sb_campaign_sheet in available_sheets:
            try:
                # Process the data
                try:
                    final_sb_optimisation(temp_file_path, sb_bulk_sheet, sb_str_sheet, sb_output_path, sb_target_acos, temp_file_path, sb_campaign_sheet)
                    if os.path.exists(sb_output_path):
                        sb_success = True
                        
                        # Extract processed data for JSON
                        sb_processed_dfs = {}
                        with pd.ExcelFile(sb_output_path) as xls:
                            for sheet_name in xls.sheet_names:
                                sb_processed_dfs[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name).to_dict(orient="records")
                        
                        results['sb'] = {
                            'success': True,
                            'data': sb_processed_dfs
                        }
                    else:
                        results['sb'] = {
                            'success': False,
                            'error': "Failed to process SB data"
                        }
                except ImportError:
                    results['sb'] = {
                        'success': False,
                        'error': "SB module is not available"
                    }
            except Exception as e:
                results['sb'] = {
                    'success': False,
                    'error': str(e)
                }
        else:
            results['sb'] = {
                'success': False,
                'error': "Required SB sheets not found in the uploaded file"
            }
        
        # Process SD if sheets are available
        if sd_bulk_sheet in available_sheets:
            try:
                # Process the data
                try:
                    load_and_process_reports(temp_file_path, sd_bulk_sheet, sd_output_path, sd_target_acos)
                    if os.path.exists(sd_output_path):
                        sd_success = True
                        
                        # Extract processed data for JSON
                        sd_processed_dfs = {}
                        with pd.ExcelFile(sd_output_path) as xls:
                            for sheet_name in xls.sheet_names:
                                sd_processed_dfs[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name).to_dict(orient="records")
                        
                        results['sd'] = {
                            'success': True,
                            'data': sd_processed_dfs
                        }
                    else:
                        results['sd'] = {
                            'success': False,
                            'error': "Failed to process SD data"
                        }
                except ImportError:
                    results['sd'] = {
                        'success': False,
                        'error': "SD module is not available" 
                    }
            except Exception as e:
                results['sd'] = {
                    'success': False,
                    'error': str(e)
                }
        else:
            results['sd'] = {
                'success': False,
                'error': "Required SD sheets not found in the uploaded file"
            }
        
        # If at least one process was successful, create combined Excel file
        if sp_success or sb_success or sd_success:
            try:
                # Create a combined Excel file
                with pd.ExcelWriter(combined_output_path) as writer:
                    # Add SP sheets
                    if sp_success:
                        with pd.ExcelFile(sp_output_path) as xls:
                            for sheet_name in xls.sheet_names:
                                df = pd.read_excel(xls, sheet_name=sheet_name)
                                df.to_excel(writer, sheet_name=f"SP_{sheet_name}", index=False)
                    
                    # Add SB sheets
                    if sb_success:
                        with pd.ExcelFile(sb_output_path) as xls:
                            for sheet_name in xls.sheet_names:
                                df = pd.read_excel(xls, sheet_name=sheet_name)
                                df.to_excel(writer, sheet_name=f"SB_{sheet_name}", index=False)
                    
                    # Add SD sheets
                    if sd_success:
                        with pd.ExcelFile(sd_output_path) as xls:
                            for sheet_name in xls.sheet_names:
                                df = pd.read_excel(xls, sheet_name=sheet_name)
                                df.to_excel(writer, sheet_name=f"SD_{sheet_name}", index=False)
                
                # Save combined file to file service and get the file ID
                file_id = save_temp_file(combined_output_path)
                
                # Extract ALL data from the output Excel file for JSON response
                combined_data = get_excel_data(file_id)
                
                # Create response with file reference instead of base64
                response_data = {
                    'data': combined_data,
                    'file': {
                        'filename': f"Optimized_{file.name}",
                        'url': get_file_url(file_id),
                        'file_id': file_id
                    }
                }
                
                # Clean up temporary files
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    if os.path.exists(sp_output_path):
                        os.remove(sp_output_path)
                    if os.path.exists(sb_output_path):
                        os.remove(sb_output_path)
                    if os.path.exists(sd_output_path):
                        os.remove(sd_output_path)
                    # Do NOT delete combined_output_path as it's needed for download
                    # if os.path.exists(combined_output_path):
                    #     os.remove(combined_output_path)
                except PermissionError:
                    # Log that we couldn't clean up, but don't fail the request
                    print(f"Warning: Unable to remove some temporary files due to permission error")
                except Exception as e:
                    print(f"Warning: Error during file cleanup: {str(e)}")
                
                return create_response(request, response_data)
                
            except Exception as e:
                return create_response(request, {
                    "error": f"Error creating combined file: {str(e)}",
                    "partial_results": results
                }, 500)
        else:
            # Clean up temporary files
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception:
                pass
            
            return create_response(request, {
                "error": "No successful optimizations",
                "details": results
            }, 400)

    except Exception as e:
        # Print detailed error information for debugging
        import traceback
        traceback.print_exc()
        
        # Clean up any temporary files
        for file_path in [temp_file_path, sp_output_path, sb_output_path, sd_output_path, combined_output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except PermissionError:
                    # Log error but continue
                    print(f"Warning: Unable to remove {file_path} due to permission error")
                except Exception:
                    pass
                
        return create_response(request, {"error": f"Unexpected error: {str(e)}"}, 500)

def create_response(request, data, status=200):
    response = JsonResponse(data, safe=False, status=status)
    response["Access-Control-Allow-Origin"] = request.headers.get('Origin')
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
    return response
