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
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import pandas as pd
import os
import fuzzywuzzy
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from sp1.header import final_sp_optimisation
from sb.header import final_sb_optimisation
from sd.header import load_and_process_reports



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

    
    actual_headers = df.columns.tolist()
    header_mapping = match_headers(actual_headers, expected_headers)
    return df.rename(columns=header_mapping)


@csrf_exempt
@api_view(['POST', 'OPTIONS']) #added api_view
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
            target_acos = float(request.POST.get('target_acos', 0))
            if target_acos <= 0:
                return create_response(request, {"error": "Invalid target ACOS"}, 400)
        except ValueError:
            return create_response(request, {"error": "Invalid target ACOS format"}, 400)

        # Define expected headers
        expected_headers_str = [
            "Start Date", "End Date", "Portfolio name", "Currency", "Campaign Name", 
            "Ad Group Name", "Targeting", "Match Type", "Customer Search Term", "Impressions", 
            "Clicks", "Click-Thru Rate (CTR)", "Cost Per Click (CPC)", "Spend", 
            "14 Day Total Sales ", "Total Advertising Cost of Sales (ACOS) ", 
            "Total Return on Advertising Spend (ROAS)", "14 Day Total Orders (#)", 
            "14 Day Total Units (#)", "14 Day Conversion Rate", 
            "14 Day Advertised ASIN Units (#)", "14 Day Brand Halo ASIN Units (#)", 
            "14 Day Advertised ASIN Sales (â‚¹)", "14 Day Brand Halo ASIN Sales (â‚¹)"
        ]

        expected_headers_bulk = [
            "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", 
            "Portfolio ID", "Ad ID", "Keyword ID", "Product Targeting ID", "Campaign Name", 
            "Ad Group Name", "Campaign Name (Informational only)", "Ad Group Name (Informational only)", 
            "Portfolio Name (Informational only)", "Start Date", "End Date", "Targeting Type", 
            "State", "Campaign State (Informational only)", "Ad Group State (Informational only)", 
            "Daily Budget", "SKU", "ASIN", "Eligibility Status (Informational only)", 
            "Reason for Ineligibility (Informational only)", "Ad Group Default Bid", 
            "Ad Group Default Bid (Informational only)", "Bid", "Keyword Text", 
            "Native Language Keyword", "Native Language Locale", "Match Type", "Bidding Strategy", 
            "Placement", "Percentage", "Product Targeting Expression", 
            "Resolved Product Targeting Expression (Informational only)", "Impressions", 
            "Clicks", "Click-through Rate", "Spend", "Sales", "Orders", "Units", 
            "Conversion Rate", "ACOS", "CPC", "ROAS"
        ]

        

        # Extract the relevant sheet data into a DataFrame
        try:
            str_df = pd.read_excel(file, sheet_name="SP Search Term Report")
            if str_df.empty:
                return create_response(request, {"error": "SP Search Term Report is empty"}, 400)
        except ValueError:
            return create_response(request, {"error": "SP Search Term Report not found in the uploaded file"}, 400)
        except Exception as e:
            return create_response(request, {"error": f"Error reading SP Search Term Report: {str(e)}"}, 500)
        
        try:
            bulk_df = pd.read_excel(file, sheet_name="Sponsored Products Campaigns")
            if bulk_df.empty:
                return create_response(request, {"error": "Sponsored Products Campaigns is empty"}, 400)
        except ValueError:
            return create_response(request, {"error": "Sponsored Products Campaigns not found in the uploaded file"}, 400)
        except Exception as e:
            return create_response(request, {"error": f"Error reading Sponsored Products Campaigns: {str(e)}"}, 500)

        # Standardize headers
        str_df = standardize_headers(str_df, expected_headers_str)
        bulk_df = standardize_headers(bulk_df, expected_headers_bulk)

        # Data filtering
        str_sk = str_df[str_df["Campaign Name (Informational only)"].str.lower().str.startswith("b0")]
        str_mk = str_df[~str_df["Campaign Name (Informational only)"].str.lower().str.startswith("b0")]
        bulk_sk = bulk_df[bulk_df["Campaign Name (Informational only)"].str.lower().str.startswith("b0")]
        bulk_mk = bulk_df[~bulk_df["Campaign Name (Informational only)"].str.lower().str.startswith("b0")]

        #Harvest data
        deduped_df, result_df = harvest_data_sk(
            str_df=str_sk,
            bulk_df=bulk_sk,
            target_acos=target_acos
        )

        #Campaign negation
        pt_df, kw_df = campaign_negation_sk(
            str_df=str_sk,
            bulk_df=bulk_sk,
            target_acos=target_acos,
            multiplier=1.5#Scale up mode set to 2.5 optimise set to 1.2
        )

        pt_df_mk, kw_df_mk = campaign_negation_mk(
            str_df=str_mk,
            bulk_df=bulk_mk,
            target_acos=target_acos,
            multiplier=1.5#Scale up mode set to 2.5 optimise set to 1.2
        )
        #Placement optimization
        filtered_bulk_df, valid_campaigns, RPC_df, asin_summary = placement_optimize_sk(
            bulk_df=bulk_sk,
            target_acos=target_acos
        )

        filtered_bulk_df_mk, valid_campaigns_mk, RPC_df_mk, bulk_summary_mk = placement_optimize_mk(
            bulk_df=bulk_mk,
            target_acos=target_acos
        )
        new_bid_df_mk = filtered_bulk_df_mk.drop(columns=["key", "RPC"], errors="ignore")

        # Combine filtered_bulk_df and new_bid_df_mk by appending new_bid_df_mk to filtered_bulk_df
        combined_df = pd.concat([filtered_bulk_df, new_bid_df_mk], ignore_index=True)
        pt_combined_df = pd.concat([pt_df, pt_df_mk], ignore_index=True)
        kw_combined_df = pd.concat([kw_df, kw_df_mk], ignore_index=True)
        placement_combined_df = pd.concat([valid_campaigns, valid_campaigns_mk], ignore_index=True)
        RPC_combined_df = pd.concat([RPC_df, RPC_df_mk], ignore_index=True)
        bulk_summary_combined_df = pd.concat([asin_summary, bulk_summary_mk], ignore_index=True)

        # Combine all the DataFrames into a single DataFrame
        final_combined_df = pd.concat([
            deduped_df,
            result_df,
            combined_df,
            pt_combined_df,
            kw_combined_df,
            placement_combined_df,
            RPC_combined_df,
            bulk_summary_combined_df
        ], axis=1)

        if final_combined_df.empty:
            return create_response(request, {"error": "No data to process"}, 400)

        final_combined_json = final_combined_df.to_json(orient="records")
        return create_response(request, json.loads(final_combined_json))

    except Exception as e:
        return create_response(request, {"error": f"Unexpected error: {str(e)}"}, 500)
            

def create_response(request, data, status=200):
    response = JsonResponse(data, safe=False, status=status)
    response["Access-Control-Allow-Origin"] = request.headers.get('Origin')
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
    return response


#New function for all optimisations
def all_optimisations(request):
    sp_target_acos = 0.30
    sb_target_acos = 0.30
    sd_target_acos = 0.30


    bulk_file_path = "/mnt/c/Users/arun/Downloads/Reports/bulk mygate wk12.xlsx"

    bulk_sheet_sp = "Sponsored Products Campaigns"
    bulk_sheet_sb="Sponsored Brands Campaigns"
    bulk_sheet_sd = "Sponsored Display Campaigns"
    bulk_sheet_sbr = "SB Search Term Report"
    bulk_sheet_str = "SP Search Term Report"
    campaign_file_path = "/mnt/c/Users/arun/Downloads/Reports/mygate sb placement wk12.xlsx"
    campaign_sheet="Sponsored_Brands_Campaign_place"

    sp_output_file_path = "/mnt/c/Users/arun/Downloads/Reports/Output_data_SP.xlsx"
    sb_output_file_path = "/mnt/c/Users/arun/Downloads/Reports/Output_data_SB.xlsx"
    sd_output_file_path = "/mnt/c/Users/arun/Downloads/Reports/Output_data_SD.xlsx"

    final_sp_optimisation(bulk_file_path, sp_output_file_path, sp_target_acos, bulk_sheet_sp, bulk_sheet_str)
    final_sb_optimisation(bulk_file_path, bulk_sheet_sb, bulk_sheet_sbr, sb_output_file_path, sb_target_acos, campaign_file_path, campaign_sheet)
    load_and_process_reports(bulk_file_path, bulk_sheet_sd, sd_output_file_path, sd_target_acos)
