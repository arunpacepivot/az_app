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

def harvest_data_sk(str_df: pd.DataFrame, bulk_df: pd.DataFrame, target_acos: float ) -> pd.DataFrame:
    df_str = str_df.copy()
    # Add "ASIN" column by extracting the first word from "Campaign Name"
    df_str.loc[:, "ASIN"] = df_str["Campaign Name (Informational only)"].apply(lambda x: x.split()[0])
    # Set "Targeting" equal to "Keyword Text" where it is not empty, otherwise use "Product Targeting Expression"
    df_str.loc[:, "Targeting"] = df_str.apply(
        lambda row: row["Keyword Text"] if pd.notna(row["Keyword Text"]) and row["Keyword Text"].strip() != "" else row["Product Targeting Expression"],
        axis=1
    )
    df_str.loc[:, "Targeting"] = df_str["Targeting"].fillna("").astype(str)

    # Grouped summary of ASIN and Placement
    str_summary = df_str.groupby(["ASIN"]).agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum",
        "Units": "sum"
    }).reset_index()

    str_summary["CPC"] = str_summary["Spend"] / str_summary["Clicks"]
    str_summary["RPC"] = str_summary["Sales"] / str_summary["Clicks"]
    str_summary["AOV"] = str_summary["Sales"] / str_summary["Units"]
    str_summary["Conversion"] = str_summary["Sales"] / str_summary["Orders"]
    # Filter df_str for where match type is not equal to "exact", targeting does not begin with "asin" and 14 day total orders >= 3
    filtered_df_str = df_str[
        (df_str["Match Type"] != "Exact") &
        (~df_str["Targeting"].str.startswith("asin")) &
        (df_str["Orders"] >= 2)
    ]
    # Create a new DataFrame to store the results
    result_data = []

    # Iterate over each row in the filtered DataFrame
    for _, row in filtered_df_str.iterrows():
        asin = row["ASIN"]
        customer_search_term = row["Customer Search Term"]
        acos = row["ACOS"]
        cpc = row["CPC"]
    
        # Calculate the bid based on the given conditions
        if acos > target_acos * 1.2:
            bid = cpc * (target_acos / acos)
        elif 0.8 * target_acos < acos <= 1.2 * target_acos:
            bid = cpc
        elif acos < 0.8 * target_acos:
            asin_cpc = str_summary[str_summary["ASIN"] == asin]["CPC"].values[0]
            bid = min(cpc * 1.1, asin_cpc)
        else:
            bid = np.nan   # In case none of the conditions are met, which should not happen

        # Append the result to the list
        result_data.append({
            "ASIN": asin,
            "Customer Search Term": customer_search_term,
            "Bid": round(bid, 2),
            "Type": "PT" if customer_search_term.lower().startswith("b0") else "KW"
        })

    # Convert the result list to a DataFrame
    result_df = pd.DataFrame(result_data)

    # Load the bulk file into a DataFrame
    bulk_df = bulk_df
    # Filter the DataFrame for rows where Match Type is in ["Broad", "Phrase", "Exact"]
    filtered_kw_df = bulk_df[bulk_df["Match Type"].isin(["Broad", "Phrase", "Exact"])]

    # Initialize a list to store the rows for the new DataFrame
    asin_kw_match_data = []

    # Iterate over each row in the filtered DataFrame
    for _, row in filtered_kw_df.iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        # Skip if campaign_name is NaN or not a string
        if pd.isna(campaign_name) or not isinstance(campaign_name, str):
            continue

        asin = campaign_name.split()[0]
        kw_pt = row["Keyword Text"]
        match_type = row["Match Type"]

        # Append the row to asin_kw_match_data
        asin_kw_match_data.append({
            "ASIN": asin,
            "KW/PT": kw_pt,
            "Match Type": match_type
        })

    # Filter the DataFrame for rows where Product Targeting Expression starts with "asin"
    filtered_pt_df = bulk_df[bulk_df["Product Targeting Expression"].str.startswith("asin", na=False)]

    # Iterate over each row in the filtered Product Targeting DataFrame
    for _, row in filtered_pt_df.iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        # Skip if campaign_name is NaN or not a string
        if pd.isna(campaign_name) or not isinstance(campaign_name, str):
            continue

        asin = campaign_name.split()[0]
        kw_pt = row["Product Targeting Expression"].split('"')[1]  # Extract the value inside quotes
        match_type = "PT"

        # Append the row to asin_kw_match_data
        asin_kw_match_data.append({
            "ASIN": asin,
            "KW/PT": kw_pt,
            "Match Type": match_type
        })

    # Create the asin_kw_match DataFrame from the asin_kw_match_data
    asin_kw_match = pd.DataFrame(asin_kw_match_data)

    # Create a new DataFrame with the specified columns
    deduped_columns = ["ASIN", "KW/PT", "Broad", "Phrase", "Exact", "PT", "CPC"]
    deduped_df = pd.DataFrame(columns=deduped_columns).astype({
        "ASIN": str,
        "KW/PT": str,
        "Broad": str,
        "Phrase": str,
        "Exact": str,
        "PT": str,
        "CPC": float
    })

    # Iterate over each row in result_df
    for _, row in result_df.iterrows():
        asin = row["ASIN"]
        kw_pt = row["Customer Search Term"]
        cpc = row["Bid"]

        # Check if the row already exists in deduped_df
        existing_row = deduped_df[(deduped_df["ASIN"] == asin) & (deduped_df["KW/PT"] == kw_pt) ]
        if existing_row.empty:
            # If the row does not exist, create a new row with default values
            new_row = pd.DataFrame([{
                "ASIN": str(asin),
                "KW/PT": str(kw_pt),
                "Broad": "doesn't exist",
                "Phrase": "doesn't exist",
                "Exact": "doesn't exist",
                "PT": "doesn't exist",
                "CPC": float(cpc)
            }])
            deduped_df = pd.concat([deduped_df, new_row], ignore_index=True)

        # Check for keyword match type combinations in asin_kw_match
        for match_type in ["Broad", "Phrase", "Exact", "PT"]:
            if not asin_kw_match[(asin_kw_match["ASIN"] == asin) & (asin_kw_match["KW/PT"] == kw_pt) & (asin_kw_match["Match Type"] == match_type)].empty:
                deduped_df.loc[(deduped_df["ASIN"] == asin) & (deduped_df["KW/PT"] == kw_pt), match_type] = "exists"
            else:
                deduped_df.loc[(deduped_df["ASIN"] == asin) & (deduped_df["KW/PT"] == kw_pt), match_type] = "doesn't exist"
    # Add a new column "Type" to deduped_df
    deduped_df["Type"] = deduped_df["KW/PT"].apply(lambda x: "PT" if x.lower().startswith("b0") else "KW")
    return deduped_df, result_df

def campaign_negation_sk(str_df: pd.DataFrame, bulk_df: pd.DataFrame, target_acos: float, multiplier: float ) -> pd.DataFrame:
    df_str = str_df.copy()
    # Add "ASIN" column by extracting the first word from "Campaign Name"
    df_str.loc[:, "ASIN"] = df_str["Campaign Name (Informational only)"].apply(lambda x: x.split()[0])
    df_str["Targeting"] = df_str.apply(
        lambda row: row["Keyword Text"] if pd.notna(row["Keyword Text"]) and row["Keyword Text"].strip() != "" else row["Product Targeting Expression"],
        axis=1
    )
    df_str["Targeting"] = df_str["Targeting"].fillna("").astype(str)
    # Grouped summary of ASIN and Placement
    str_summary = df_str.groupby(["ASIN"]).agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum",
        "Units": "sum"
    }).reset_index()

    str_summary["CPC"] = str_summary["Spend"] / str_summary["Clicks"]
    str_summary["RPC"] = str_summary["Sales"] / str_summary["Clicks"]
    str_summary["AOV"] = str_summary["Sales"] / str_summary["Units"]
    str_summary["Conversion"] = str_summary["Sales"] / str_summary["Orders"]

    # Define the maximum spend based on AOV and target ACOS
    df_str.loc[:, "ASIN"] = df_str["Campaign Name (Informational only)"].apply(lambda x: x.split()[0])
    df_str = df_str[df_str["Sales"] == 0]

    # Initialize an empty list to store the filtered rows
    filtered_rows = []

    for _, row in df_str.iterrows():
        asin = row["ASIN"]
        spend = row["Spend"]
        
        # Check if the ASIN exists in str_summary
        if asin in str_summary["ASIN"].values:
            aov = str_summary[str_summary["ASIN"] == asin]["AOV"].values[0]
            max_spend = aov * target_acos * multiplier
            
            # Filter rows where spend is greater than max_spend
            if spend > max_spend:
                filtered_rows.append(row)

    # Convert the filtered rows to a DataFrame
    if not filtered_rows:
        filtered_df = pd.DataFrame()
    else:
        filtered_df = pd.DataFrame(filtered_rows)
        filtered_df["Max Spend"] = filtered_df.apply(
        lambda row: str_summary[str_summary["ASIN"] == row["ASIN"]]["AOV"].values[0] * target_acos 
        if row["ASIN"] in str_summary["ASIN"].values else 0, 
        axis=1
    )
        filtered_df = filtered_df[
        (filtered_df["Match Type"] != "EXACT") & 
        (~filtered_df["Targeting"].str.startswith("asin"))
    ]
    
    # Initialize empty lists to store rows for PT_df and KW_df
    pt_rows = []
    kw_rows = []

    # Iterate over each row in filtered_df
    for _, row in filtered_df.iterrows():
        customer_search_term = row["Customer Search Term"]
        campaign_name = row["Campaign Name (Informational only)"]
        ad_group_name = row["Ad Group Name (Informational only)"]
        campaign_id = row["Campaign ID"]
        ad_group_id = row["Ad Group ID"]

        # Check if the customer search term starts with 'b0' (case insensitive)
        if customer_search_term.lower().startswith("b0"):
            pt_rows.append({
                "Campaign ID": str(campaign_id),  # Placeholder, will be filled later
                "Ad Group ID": str(ad_group_id),  # Placeholder, will be filled later
                "Campaign Name (Informational only)": campaign_name,
                "Ad Group Name (Informational only)": ad_group_name,
                "Customer Search Term": customer_search_term
            })
        else:
            kw_rows.append({
                "Campaign ID": str(campaign_id),  # Placeholder, will be filled later
                "Ad Group ID": str(ad_group_id),  # Placeholder, will be filled later
                "Campaign Name (Informational only)": campaign_name,
                "Ad Group Name (Informational only)": ad_group_name,
                "Customer Search Term": customer_search_term
            })

    
    # Convert the lists to DataFrames
    pt_df = pd.DataFrame(pt_rows)
    kw_df = pd.DataFrame(kw_rows)
    

    df_bulk_report = bulk_df
    negative_keywords = df_bulk_report[
        df_bulk_report["Match Type"].isin(["Negative Exact", "Negative Phrase"])
    ][["Campaign Name (Informational only)", "Ad Group Name (Informational only)", "Keyword Text"]]

    # Remove rows in pt_df where the Customer Search Term exists in the negative keywords
    pt_df = pt_df[~pt_df.apply(
        lambda row: (row["Campaign Name (Informational only)"], row["Ad Group Name (Informational only)"], row["Customer Search Term"]) in 
                    negative_keywords.itertuples(index=False, name=None), axis=1)]  #CHANGE

    # Remove rows in kw_df where the Customer Search Term exists in the negative keywords
    kw_df = kw_df[~kw_df.apply(
        lambda row: (row["Campaign Name (Informational only)"], row["Ad Group Name (Informational only)"], row["Customer Search Term"]) in 
                    negative_keywords.itertuples(index=False, name=None), axis=1)]  #CHANGE
    
    return pt_df, kw_df

def campaign_negation_mk(str_df: pd.DataFrame, bulk_df: pd.DataFrame, target_acos: float, multiplier: float ) -> pd.DataFrame:
    df_str = str_df
    df_str["Targeting"] = df_str.apply(
        lambda row: row["Keyword Text"] if pd.notna(row["Keyword Text"]) and row["Keyword Text"].strip() != "" else row["Product Targeting Expression"],
        axis=1
    )
    df_str["Targeting"] = df_str["Targeting"].fillna("").astype(str)
    # Grouped summary of ASIN and Placement
    str_summary = df_str.groupby(["Campaign Name (Informational only)"]).agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum",
        "Units": "sum"
    }).reset_index()

    str_summary["CPC"] = str_summary["Spend"] / str_summary["Clicks"]
    str_summary["RPC"] = str_summary["Sales"] / str_summary["Clicks"]
    str_summary["AOV"] = str_summary["Sales"] / str_summary["Units"]
    str_summary["Conversion"] = str_summary["Sales"] / str_summary["Orders"]

    # Define the maximum spend based on AOV and target ACOS
    df_str = df_str[df_str["Sales"] == 0]

    # Initialize an empty list to store the filtered rows
    filtered_rows = []

    for _, row in df_str.iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        spend = row["Spend"]
        
        # Check if the ASIN exists in str_summary
        if campaign_name in str_summary["Campaign Name (Informational only)"].values:
            aov = str_summary[str_summary["Campaign Name (Informational only)"] == campaign_name]["AOV"].values[0]
            max_spend = aov * target_acos * multiplier
            
            # Filter rows where spend is greater than max_spend
            if spend > max_spend:
                filtered_rows.append(row)

    # Convert the filtered rows to a DataFrame
    
    if filtered_rows:
        filtered_df = pd.DataFrame(filtered_rows)
    else:
        filtered_df = pd.DataFrame()  # Create an empty DataFrame if filtered_rows is empty
    # Add a column "Max Spend" to the filtered DataFrame and populate it with the calculated max_spend values
    if not filtered_df.empty:
        filtered_df["Max Spend"] = filtered_df.apply(
            lambda row: str_summary[str_summary["Campaign Name (Informational only)"] == row["Campaign Name (Informational only)"]]["AOV"].values[0] * target_acos 
        if row["Campaign Name (Informational only)"] in str_summary["Campaign Name (Informational only)"].values else 0, 
        axis=1
        )
        filtered_df = filtered_df[
        (filtered_df["Match Type"] != "EXACT") & 
        (~filtered_df["Targeting"].str.startswith("asin"))
        ]

    
    # Initialize empty lists to store rows for PT_df and KW_df
    pt_rows = []
    kw_rows = []

    # Iterate over each row in filtered_df
    for _, row in filtered_df.iterrows():
        customer_search_term = row["Customer Search Term"]
        campaign_name = row["Campaign Name (Informational only)"]
        ad_group_name = row["Ad Group Name (Informational only)"]
        campaign_id = row["Campaign ID"]
        ad_group_id = row["Ad Group ID"]

        # Check if the customer search term starts with 'b0' (case insensitive)
        if customer_search_term.lower().startswith("b0"):
            pt_rows.append({
                "Campaign ID": str(campaign_id),  # Placeholder, will be filled later
                "Ad Group ID": str(ad_group_id),  # Placeholder, will be filled later
                "Campaign Name (Informational only)": campaign_name,
                "Ad Group Name (Informational only)": ad_group_name,
                "Customer Search Term": customer_search_term
            })
        else:
            kw_rows.append({
                "Campaign ID": str(campaign_id),  # Placeholder, will be filled later
                "Ad Group ID": str(ad_group_id),  # Placeholder, will be filled later
                "Campaign Name (Informational only)": campaign_name,
                "Ad Group Name (Informational only)": ad_group_name,
                "Customer Search Term": customer_search_term
            })

    # Convert the lists to DataFrames
    if not pt_rows:
        pt_df = pd.DataFrame()
    else:
        pt_df = pd.DataFrame(pt_rows)
    if not kw_rows:
        kw_df = pd.DataFrame()
    else:
        kw_df = pd.DataFrame(kw_rows)
    
    pt_df_mk=pd.DataFrame()
    kw_df_mk=pd.DataFrame()
    # Load df_bulk_report to get Campaign ID and Ad Group ID
    df_bulk_report = bulk_df
    
    if not pt_df.empty:
        pt_df = pt_df[["Campaign ID", "Ad Group ID", "Campaign Name (Informational only)", "Ad Group Name (Informational only)", "Customer Search Term"]]
    if not kw_df.empty:     
        kw_df = kw_df[["Campaign ID", "Ad Group ID", "Campaign Name (Informational only)", "Ad Group Name (Informational only)", "Customer Search Term"]]
     #CHANGE: Filter pt_df and kw_df based on conditions from df_bulk_report
    negative_keywords = df_bulk_report[
        df_bulk_report["Match Type"].isin(["Negative Exact", "Negative Phrase"])
    ][["Campaign Name (Informational only)", "Ad Group Name (Informational only)", "Keyword Text"]]

    # Remove rows in pt_df where the Customer Search Term exists in the negative keywords
    pt_df = pt_df[~pt_df.apply(
        lambda row: (row["Campaign Name (Informational only)"], row["Ad Group Name (Informational only)"], row["Customer Search Term"]) in 
                    negative_keywords.itertuples(index=False, name=None), axis=1)]  #CHANGE
    # Remove rows in kw_df where the Customer Search Term exists in the negative keywords
    kw_df = kw_df[~kw_df.apply(
        lambda row: (row["Campaign Name (Informational only)"], row["Ad Group Name (Informational only)"], row["Customer Search Term"]) in 
                    negative_keywords.itertuples(index=False, name=None), axis=1)]  #CHANGE
    pt_df_mk = pt_df
    kw_df_mk = kw_df
    return pt_df_mk, kw_df_mk

def placement_optimize_sk( bulk_df: pd.DataFrame, target_acos: float ) -> pd.DataFrame:
    # Filter bulk_df for the required conditions to create df_placement
    df_placement = bulk_df[
        (bulk_df["Entity"] == "Bidding Adjustment") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Placement"].isin(["Placement Product Page", "Placement Top", "Placement Rest Of Search"]))
    ].copy() 

    df_placement["ASIN_Derived"] = df_placement["Campaign Name (Informational only)"].str.split().str[0]
    if df_placement.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Grouped summary of ASIN and Placement
    asin_summary = df_placement.groupby(["ASIN_Derived", "Placement"], observed=True).agg({
            "Impressions": "sum",
            "Clicks": "sum",
            "Spend": "sum",
            "Sales": "sum",
            "Orders": "sum",
            "Units": "sum"
        }).reset_index()

    asin_summary["CPC"] = asin_summary["Spend"] / asin_summary["Clicks"]
    asin_summary["RPC"] = asin_summary["Sales"] / asin_summary["Clicks"]
    asin_summary["AOV"] = asin_summary["Sales"] / asin_summary["Units"]
    asin_summary["Conversion"] = asin_summary["Sales"] / asin_summary["Orders"]

    # Calculate `RPC` and create new DataFrame
    RPC_df = df_placement[[
        "Campaign Name (Informational only)", "Placement", "Sales", "Clicks", "ACOS", "Spend", "Units", "CPC", "ASIN_Derived"
    ]].copy()

    # Extract ASIN (first word of Campaign Name) for new DataFrame
    RPC_df["RPC"] = RPC_df.apply(
        lambda x: x["Sales"] / x["Clicks"] if x["Clicks"] > 0 else 0,
        axis=1
    )

    # Initialize ideal bid and multiplier columns
    RPC_df["Ideal Bid"] = 0.0
    RPC_df["Multiplier"] = 0.0

    # Iterate over each unique Campaign Name to apply the logic for Ideal Bid calculation
    for campaign_name, group in RPC_df.groupby("Campaign Name (Informational only)"):
        group_indices = group.index
        rpc_greater_than_zero = group[group["RPC"] > 0]
        
        # Case: All three rows have RPC == 0
        if len(rpc_greater_than_zero) == 0:
            RPC_df.loc[group_indices, "Ideal Bid"] = np.nan

        # Case 1: All three placements have RPC > 0
        elif len(rpc_greater_than_zero) == 3:
            for idx in group_indices:
                row = RPC_df.loc[idx]
                if row["ACOS"] > target_acos:
                    RPC_df.at[idx, "Ideal Bid"] = row["RPC"] * target_acos
                else:
                    # Add error checking for asin_cpc lookup
                    asin_placement_data = asin_summary[
                        (asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & 
                        (asin_summary["Placement"] == row["Placement"])
                    ]
                    

                    if len(asin_placement_data) > 0:
                        asin_cpc = asin_placement_data["CPC"].values[0] if not asin_placement_data.empty else placement_aggregate_cpc.get(row["Placement"], 0)
                        if row["ACOS"] < 0.5 * target_acos:
                            multiplier = 1.5
                        elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                            multiplier = 1.25
                        else:
                            multiplier = 1.1
                        RPC_df.at[idx, "Ideal Bid"] = min(asin_cpc * multiplier, row["CPC"] * 1.1)
                    else:
                        # Fallback when no matching data found
                        RPC_df.at[idx, "Ideal Bid"] = row["CPC"] * 1.1
            # Calculate aggregate CPC for each placement as a fallback
            placement_aggregate_cpc = asin_summary.groupby("Placement", observed=True)["CPC"].mean().to_dict()

        # Case 2: Only one placement has RPC > 0
        elif len(rpc_greater_than_zero) == 1:
            idx = rpc_greater_than_zero.index[0]
            row = RPC_df.loc[idx]
            
            if row["ACOS"] > target_acos:
                RPC_df.at[idx, "Ideal Bid"] = row["RPC"] * target_acos
            else:
                # Attempt to get CPC for the specific ASIN-placement, fall back to placement aggregate CPC if missing
                asin_cpc = asin_summary[(asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & (asin_summary["Placement"] == row["Placement"])]["CPC"].values
                asin_cpc = asin_cpc[0] if len(asin_cpc) > 0 and not pd.isna(asin_cpc[0]) else placement_aggregate_cpc.get(row["Placement"], 0)

                if row["ACOS"] < 0.5 * target_acos:
                    multiplier = 1.5
                elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                    multiplier = 1.25
                else:
                    multiplier = 1.1
                RPC_df.at[idx, "Ideal Bid"] = min(asin_cpc * multiplier, row["CPC"] * 1.1)

            # Calculate bids for other placements based on ASIN CPC ratio
            reference_placement = RPC_df.at[idx, "Placement"]
            reference_cpc = asin_summary[(asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & (asin_summary["Placement"] == reference_placement)]["CPC"].values
            reference_cpc = reference_cpc[0] if len(reference_cpc) > 0 and not pd.isna(reference_cpc[0]) else placement_aggregate_cpc.get(reference_placement, 0)
            reference_ideal_bid = RPC_df.at[idx, "Ideal Bid"]

            for other_idx in group_indices:
                placement = RPC_df.at[other_idx, "Placement"]
                asin_cpc = asin_summary[(asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & (asin_summary["Placement"] == placement)]["CPC"].values
                asin_cpc = asin_cpc[0] if len(asin_cpc) > 0 and not pd.isna(asin_cpc[0]) else placement_aggregate_cpc.get(placement, 0)
                if other_idx != idx:
                    RPC_df.at[other_idx, "Ideal Bid"] = reference_ideal_bid * (asin_cpc / reference_cpc)

        # Case 3: Two placements have RPC > 0
        elif len(rpc_greater_than_zero) == 2:
            for idx in rpc_greater_than_zero.index:
                row = RPC_df.loc[idx]
                
                if row["ACOS"] > target_acos:
                    RPC_df.at[idx, "Ideal Bid"] = row["RPC"] * target_acos
                else:
                    asin_cpc = asin_summary[(asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & (asin_summary["Placement"] == row["Placement"])]["CPC"].values
                    asin_cpc = asin_cpc[0] if len(asin_cpc) > 0 and not pd.isna(asin_cpc[0]) else placement_aggregate_cpc.get(row["Placement"], 0)

                    if row["ACOS"] < 0.5 * target_acos:
                        multiplier = 1.5
                    elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                        multiplier = 1.25
                    else:
                        multiplier = 1.1    
                    RPC_df.at[idx, "Ideal Bid"] = min(asin_cpc * multiplier, row["CPC"] * 1.1)

            ideal_bids = RPC_df.loc[group_indices, "Ideal Bid"]
            max_bid = ideal_bids.max()
            for other_idx in group_indices:
                if other_idx not in rpc_greater_than_zero.index:
                    
                    placement_zero_rpc = RPC_df.at[other_idx, "Placement"]
                    asin_cpc_zero_rpc = asin_summary[(asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & (asin_summary["Placement"] == placement_zero_rpc)]["CPC"].values
                    asin_cpc_zero_rpc = asin_cpc_zero_rpc[0] if len(asin_cpc_zero_rpc) > 0 and not pd.isna(asin_cpc_zero_rpc[0]) else placement_aggregate_cpc.get(placement_zero_rpc, 0)

                    placement_max_bid = RPC_df.loc[RPC_df["Ideal Bid"] == max_bid, "Placement"].values[0]
                    asin_cpc_max_bid = asin_summary[(asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & (asin_summary["Placement"] == placement_max_bid)]["CPC"].values
                    asin_cpc_max_bid = asin_cpc_max_bid[0] if len(asin_cpc_max_bid) > 0 and not pd.isna(asin_cpc_max_bid[0]) else placement_aggregate_cpc.get(placement_max_bid, 0)

                    RPC_df.at[other_idx, "Ideal Bid"] = max_bid * (asin_cpc_zero_rpc / asin_cpc_max_bid)

        

        # Calculate Multiplier for each row
        valid_bids = RPC_df.loc[group_indices]
        valid_bids = valid_bids[valid_bids["Ideal Bid"] != np.nan]  # Apply the filter on the subset directly
        if not valid_bids.empty:
            min_bid = valid_bids["Ideal Bid"].min()
            RPC_df.loc[group_indices, "Multiplier"] = valid_bids["Ideal Bid"].apply(
                lambda x: (x / min_bid) - 1 if x != np.nan else np.nan
            )
    # Load the bulk file into a DataFrame
    bulk_df = bulk_df

    valid_campaigns_data = []
    # Iterate over each unique campaign in bid_df
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        # Filter the rows for the current campaign
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign]
        campaign_rows.loc[:, "ASIN_Derived_bulk"] = campaign_rows["Campaign Name (Informational only)"].str.split().str[0]
        # Extract the ideal bids for each placement
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Multiplier"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Multiplier"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Multiplier"].values[0]

        # Check if all three ideal bids are not 0
        if top_of_search_bid != 0 or product_pages_bid != 0 or rest_of_search_bid != 0:
            campaign_id_values = bulk_df[bulk_df["Campaign Name (Informational only)"] == campaign]["Campaign ID"].values
            # Append the rows to valid_campaigns_data
            if len(campaign_id_values) > 0:
                campaign_id = str(campaign_id_values[0])
                valid_campaigns_data.append({
                    "Campaign Name": campaign,
                    "Campaign ID": campaign_id,
                    "Placement Rest Of Search": min(round(rest_of_search_bid * 100, 2), 900),
                    "Placement Top": min(round(top_of_search_bid * 100, 2), 900),
                    "Placement Product Page": min(round(product_pages_bid * 100, 2), 900)
                    
                })

    # Create the valid_campaigns DataFrame from the valid_campaigns_data
    valid_campaigns = pd.DataFrame(valid_campaigns_data)
    valid_campaigns=valid_campaigns.dropna(subset=["Placement Rest Of Search","Placement Top","Placement Product Page"],how="all")    
        # Initialize a list to store the rows for the new DataFrame
    campaign_bid_data = []

    # Iterate over each unique campaign in valid_campaigns
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        # Filter the rows for the current campaign
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign]

        # Extract the ideal bids for each placement
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Ideal Bid"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Ideal Bid"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Ideal Bid"].values[0]

        # Check if all three ideal bids are not 0
        if top_of_search_bid != np.nan and product_pages_bid != np.nan and rest_of_search_bid != np.nan:
            # Find the minimum ideal bid
            min_ideal_bid = min(top_of_search_bid, product_pages_bid, rest_of_search_bid)

            # Append the row to campaign_bid_data
            campaign_bid_data.append({
                "Campaign Name": campaign,
                "Bid": min_ideal_bid
            })
            
    # Convert campaign_bid_data to DataFrame before returning
    campaign_bid_df = pd.DataFrame(campaign_bid_data)
    
    # Filter the DataFrame for rows where Entity is "Keyword" or "Product Targeting"
    filtered_bulk_df = bulk_df[
        (bulk_df["Entity"].isin(["Keyword", "Product Targeting"])) &
        (bulk_df["State"] == "enabled") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Ad Group State (Informational only)"] == "enabled")
    ].copy()  # Create explicit copy

    # Now modify the copy
    filtered_bulk_df["ASIN"] = filtered_bulk_df["Campaign Name (Informational only)"].fillna("").astype(str).apply(
        lambda x: x.split()[0] if x.strip() else None
    )

    # Grouped summary of ASIN
    bulk_asin_summary = filtered_bulk_df.groupby("ASIN").agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum"
    }).reset_index()

    # Calculate additional metrics
    bulk_asin_summary["AOV"] = bulk_asin_summary["Sales"] / bulk_asin_summary["Orders"]
    bulk_asin_summary["Click to Conversion"] = bulk_asin_summary["Clicks"] / bulk_asin_summary["Orders"]
    bulk_asin_summary["CPC"] = bulk_asin_summary["Spend"] / bulk_asin_summary["Clicks"]
    # Create a new column "New bid" in filtered_bulk_df and initialize with None
    filtered_bulk_df["New bid"] = pd.NA  # Using pd.NA instead of None for better pandas compatibility
    
    # Iterate over each row in campaign_bid_df
    for _, row in campaign_bid_df.iterrows():
        campaign_name = row["Campaign Name"]
        bid_value = row["Bid"]

        # Update the "New bid" column in filtered_bulk_df where the campaign name matches
        filtered_bulk_df.loc[filtered_bulk_df["Campaign Name (Informational only)"] == campaign_name, "New bid"] = bid_value
    # Iterate over each row in filtered_bulk_df where "New bid" is blank
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna()].iterrows():
        # Check if clicks are 0
        if row["Clicks"] == 0:
            # Extract the ASIN from the first word of the campaign name
            campaign_name = row["Campaign Name (Informational only)"]
            # Skip if campaign_name is NaN or not a string
            if pd.isna(campaign_name) or not isinstance(campaign_name, str):
                continue
                
            asin = campaign_name.split()[0]
            # Find the CPC for the ASIN from bulk_asin_summary
            asin_cpc = bulk_asin_summary[bulk_asin_summary["ASIN"] == asin]["CPC"].values[0]
            # Calculate the new bid as the minimum of row CPC * 1.1 and the CPC derived from bulk_asin_summary
            new_bid = min(row["Bid"] * 1.1, asin_cpc)
            # Update the "New bid" column in filtered_bulk_df
            filtered_bulk_df.at[row.name, "New bid"] = new_bid
    # Iterate over each row in filtered_bulk_df where "New bid" is still NaN and "Clicks" > 0
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna() & (filtered_bulk_df["Clicks"] > 0)].iterrows():
        # Check if 14 Day Total Orders is 0
        if row["Orders"] == 0:
            # Extract the ASIN from the first word of the campaign name
            campaign_name = row["Campaign Name (Informational only)"]
            
            # Skip if campaign_name is NaN or not a string
            if pd.isna(campaign_name) or not isinstance(campaign_name, str):
                continue
                
            asin = campaign_name.split()[0]
            # Get the Click to Conversion and AOV metrics from bulk_asin_summary
            asin_matches = bulk_asin_summary[bulk_asin_summary["ASIN"] == asin]
            if asin_matches.empty:
                continue
                
            click_to_conversion = asin_matches["Click to Conversion"].values[0]
            aov = asin_matches["AOV"].values[0]
            # Calculate the new bid as AOV * target_acos / (row clicks + click to conversion)
            new_bid = (aov * target_acos) / (row["Clicks"] + click_to_conversion)
            if new_bid > row["Bid"]:
                new_bid = row["Bid"]
            else:
                new_bid = new_bid
            # Update the "New bid" column in filtered_bulk_df
            filtered_bulk_df.at[row.name, "New bid"] = new_bid
    # Iterate over each row in filtered_bulk_df where "New bid" is still NaN
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna()].iterrows():
        # Check if ACOS is greater than target ACOS
        if row["ACOS"] > target_acos:
            # Calculate the new bid as row CPC * (target ACOS / row ACOS)
            new_bid = row["CPC"] * (target_acos / row["ACOS"])
        else:
            # Extract the ASIN from the first word of the campaign name
            campaign_name = row["Campaign Name (Informational only)"]
            # Skip if campaign_name is NaN or not a string
            if pd.isna(campaign_name) or not isinstance(campaign_name, str):
                continue
                
            asin = campaign_name.split()[0]
            # Find the CPC for the ASIN from bulk_asin_summary
            asin_cpc = bulk_asin_summary[bulk_asin_summary["ASIN"] == asin]["CPC"].values[0]
            # Calculate the new bid as the minimum of row CPC * 1.1 and the CPC derived from bulk_asin_summary
            new_bid = round(min(row["CPC"] * 1.1, asin_cpc), 2)
            if new_bid < 1:
                new_bid = 1
        
        # Update the "New bid" column in filtered_bulk_df
        filtered_bulk_df.at[row.name, "New bid"] = new_bid
    if filtered_bulk_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame() 
    # Create the placement_df DataFrame from placement_data

    def adjust_bid(bid):
            new_bid = max(bid, 1.00)
            return round(new_bid, 2)
    filtered_bulk_df["New bid"] = filtered_bulk_df["New bid"].apply(adjust_bid)
    return filtered_bulk_df, valid_campaigns, RPC_df, asin_summary

def placement_optimize_mk( bulk_df: pd.DataFrame, target_acos: float ) -> pd.DataFrame:
    # Load and create `df` and `processed_df` from previous steps
    df_placement = bulk_df[
        (bulk_df["Entity"] == "Bidding Adjustment") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Placement"].isin(["Placement Product Page", "Placement Top", "Placement Rest Of Search"]))
    ].copy() 
    
    if df_placement.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    # Grouped summary of ASIN and Placement
    summary = df_placement.groupby(["Campaign Name (Informational only)", "Placement"], observed=True).agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum",
        "Units": "sum"
    }).reset_index()

    summary["CPC"] = summary["Spend"] / summary["Clicks"]
    summary["RPC"] = summary["Sales"] / summary["Clicks"]
    summary["AOV"] = summary["Sales"] / summary["Units"]
    summary["Conversion"] = summary["Sales"] / summary["Orders"]

    # Calculate `RPC` and create new DataFrame
    RPC_df = df_placement[[
        "Campaign Name (Informational only)", "Placement", "Sales", "Clicks", "ACOS", "Spend", "Units", "CPC"
    ]].copy()

    # Extract ASIN (first word of Campaign Name) for new DataFrame
    
    RPC_df["RPC"] = RPC_df.apply(
        lambda x: x["Sales"] / x["Clicks"] if x["Clicks"] > 0 else 0,
        axis=1
    )

    # Initialize ideal bid and multiplier columns
    RPC_df["Ideal Bid"] = 0.0
    RPC_df["Multiplier"] = 0.0

    # Iterate over each unique Campaign Name to apply the logic for Ideal Bid calculation
    for campaign_name, group in RPC_df.groupby("Campaign Name (Informational only)"):
        group_indices = group.index
        rpc_greater_than_zero = group[group["RPC"] > 0]
        
        # Case: All three rows have RPC == 0
        if len(rpc_greater_than_zero) == 0:
            RPC_df.loc[group_indices, "Ideal Bid"] = np.nan

        # Case 1: All three placements have RPC > 0
        elif len(rpc_greater_than_zero) == 3:
            for idx in group_indices:
                row = RPC_df.loc[idx]
                if row["ACOS"] > target_acos:
                    RPC_df.at[idx, "Ideal Bid"] = row["RPC"] * target_acos
                else:
                    # Add error checking for asin_cpc lookup
                    placement_data = summary[
                        (summary["Placement"] == row["Placement"])
                    ]
                    

                    if len(placement_data) > 0:
                        placement_cpc = placement_data["CPC"].values[0]
                        if row["ACOS"] < 0.5 * target_acos:
                            multiplier = 1.5
                        elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                            multiplier = 1.25
                        else:
                            multiplier = 1.1
                        RPC_df.at[idx, "Ideal Bid"] = min(placement_cpc * multiplier, row["CPC"] * 1.1)
                    else:
                        # Fallback when no matching data found
                        RPC_df.at[idx, "Ideal Bid"] = row["CPC"] * 1.1
            # Calculate aggregate CPC for each placement as a fallback
            placement_aggregate_cpc = summary.groupby("Placement", observed=True)["CPC"].mean().to_dict()

        # Case 2: Only one placement has RPC > 0
        elif len(rpc_greater_than_zero) == 1:
            idx = rpc_greater_than_zero.index[0]
            row = RPC_df.loc[idx]
            if row["ACOS"] > target_acos:
                RPC_df.at[idx, "Ideal Bid"] = row["RPC"] * target_acos
            else:
                # Attempt to get CPC for the specific placement, fall back to placement aggregate CPC if missing
                placement_cpc = summary[(summary["Placement"] == row["Placement"])]["CPC"].values
                placement_cpc = placement_cpc[0] if len(placement_cpc) > 0 and not pd.isna(placement_cpc[0]) else placement_aggregate_cpc.get(row["Placement"], 0)

                if row["ACOS"] < 0.5 * target_acos:
                    multiplier = 1.5
                elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                    multiplier = 1.25
                else:
                    multiplier = 1.1
                RPC_df.at[idx, "Ideal Bid"] = min(placement_cpc * multiplier, row["CPC"] * 1.1)

            # Calculate bids for other placements based on ASIN CPC ratio
            reference_placement = RPC_df.at[idx, "Placement"]
            reference_cpc = summary[(summary["Placement"] == reference_placement)]["CPC"].values
            reference_cpc = reference_cpc[0] if len(reference_cpc) > 0 and not pd.isna(reference_cpc[0]) else placement_aggregate_cpc.get(reference_placement, 0)
            reference_ideal_bid = RPC_df.at[idx, "Ideal Bid"]

            for other_idx in group_indices:
                placement = RPC_df.at[other_idx, "Placement"]
                placement_cpc = summary[(summary["Placement"] == placement)]["CPC"].values
                placement_cpc = placement_cpc[0] if len(placement_cpc) > 0 and not pd.isna(placement_cpc[0]) else placement_aggregate_cpc.get(placement, 0)
                if other_idx != idx:
                    RPC_df.at[other_idx, "Ideal Bid"] = reference_ideal_bid * (placement_cpc / reference_cpc)

        # Case 3: Two placements have RPC > 0
        elif len(rpc_greater_than_zero) == 2:
            for idx in rpc_greater_than_zero.index:
                row = RPC_df.loc[idx]
                if row["ACOS"] > target_acos:
                    RPC_df.at[idx, "Ideal Bid"] = row["RPC"] * target_acos
                else:
                    placement_cpc = summary[(summary["Placement"] == row["Placement"])]["CPC"].values
                    placement_cpc = placement_cpc[0] if len(placement_cpc) > 0 and not pd.isna(placement_cpc[0]) else placement_aggregate_cpc.get(row["Placement"], 0)

                    if row["ACOS"] < 0.5 * target_acos:
                        multiplier = 1.5
                    elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                        multiplier = 1.25
                    else:
                        multiplier = 1.1    
                    RPC_df.at[idx, "Ideal Bid"] = min(placement_cpc * multiplier, row["CPC"] * 1.1)

            ideal_bids = RPC_df.loc[group_indices, "Ideal Bid"]
            max_bid = ideal_bids.max()
            for other_idx in group_indices:
                if other_idx not in rpc_greater_than_zero.index:
                    placement_zero_rpc = RPC_df.at[other_idx, "Placement"]
                    placement_cpc_zero_rpc = summary[(summary["Placement"] == placement_zero_rpc)]["CPC"].values
                    placement_cpc_zero_rpc = placement_cpc_zero_rpc[0] if len(placement_cpc_zero_rpc) > 0 and not pd.isna(placement_cpc_zero_rpc[0]) else placement_aggregate_cpc.get(placement_zero_rpc, 0)

                    placement_max_bid = RPC_df.loc[RPC_df["Ideal Bid"] == max_bid, "Placement"].values[0]
                    placement_cpc_max_bid = summary[(summary["Placement"] == placement_max_bid)]["CPC"].values
                    placement_cpc_max_bid = placement_cpc_max_bid[0] if len(placement_cpc_max_bid) > 0 and not pd.isna(placement_cpc_max_bid[0]) else placement_aggregate_cpc.get(placement_max_bid, 0)

                    RPC_df.at[other_idx, "Ideal Bid"] = max_bid * (placement_cpc_zero_rpc / placement_cpc_max_bid)

        

        # Calculate Multiplier for each row
        valid_bids = RPC_df.loc[group_indices]
        valid_bids = valid_bids[valid_bids["Ideal Bid"] != np.nan]  # Apply the filter on the subset directly
        if not valid_bids.empty:
            min_bid = valid_bids["Ideal Bid"].min()
            RPC_df.loc[group_indices, "Multiplier"] = valid_bids["Ideal Bid"].apply(
                lambda x: (x / min_bid) - 1 if x != np.nan else np.nan
            )
     # Load the bulk file into a DataFrame
    bulk_df = bulk_df

    valid_campaigns_data = []
    # Iterate over each unique campaign in bid_df
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        # Filter the rows for the current campaign
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign]

        # Extract the ideal bids for each placement
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Multiplier"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Multiplier"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Multiplier"].values[0]

        # Check if all three ideal bids are not 0
        if top_of_search_bid != 0 or product_pages_bid != 0 or rest_of_search_bid != 0:
            campaign_id_values = bulk_df[bulk_df["Campaign Name (Informational only)"] == campaign]["Campaign ID"].values
            # Append the rows to valid_campaigns_data
            if len(campaign_id_values) > 0:
                campaign_id = str(campaign_id_values[0])
                valid_campaigns_data.append({
                    "Campaign Name": campaign,
                    "Campaign ID": campaign_id,
                    "Placement Rest Of Search": min(round(rest_of_search_bid * 100, 2), 900),
                    "Placement Top": min(round(top_of_search_bid * 100, 2), 900),
                    "Placement Product Page": min(round(product_pages_bid * 100, 2), 900)
                    
                })

    # Create the valid_campaigns DataFrame from the valid_campaigns_data
    valid_campaigns = pd.DataFrame(valid_campaigns_data)
    valid_campaigns=valid_campaigns.dropna(subset=["Placement Rest Of Search","Placement Top","Placement Product Page"],how="all")    
        # Initialize a list to store the rows for the new DataFrame
    campaign_bid_data = []

    # Iterate over each unique campaign in valid_campaigns
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        # Filter the rows for the current campaign
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign]

        # Extract the ideal bids for each placement
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Ideal Bid"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Ideal Bid"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Ideal Bid"].values[0]

        #Extract the multiplier for each placement
        top_of_search_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Multiplier"].values[0]
        product_pages_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Multiplier"].values[0]
        rest_of_search_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Multiplier"].values[0]

        # Check if all three ideal bids are not 0
        if top_of_search_bid != np.nan and product_pages_bid != np.nan and rest_of_search_bid != np.nan:
            # Find the minimum ideal bid
            min_ideal_bid = min(top_of_search_bid, product_pages_bid, rest_of_search_bid)

            # Append the row to campaign_bid_data
            campaign_bid_data.append({
                "Campaign Name (Informational only)": campaign,
                "Bid": min_ideal_bid,
                "Multiplier": max(top_of_search_multiplier, product_pages_multiplier, rest_of_search_multiplier)
            })
            
    # Convert campaign_bid_data to DataFrame before returning
    campaign_bid_df = pd.DataFrame(campaign_bid_data)
    
    # Filter the DataFrame for rows where Entity is "Keyword" or "Product Targeting"
    filtered_bulk_df = bulk_df[
        (bulk_df["Entity"].isin(["Keyword", "Product Targeting"])) &
        (bulk_df["State"] == "enabled") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Ad Group State (Informational only)"] == "enabled")
    ].copy()  # Create explicit copy

    # Now modify the copy
    # Convert all values in the "Bid" column of filtered_bulk_df to float
    filtered_bulk_df["Bid"] = filtered_bulk_df["Bid"].astype(float)
    
    filtered_bulk_df["key"] = filtered_bulk_df.apply(
        lambda row: row["Keyword Text"] if pd.notna(row["Keyword Text"]) and row["Keyword Text"].strip() != "" else row["Product Targeting Expression"],
        axis=1
    )

    filtered_bulk_df["RPC"] = filtered_bulk_df.apply(
        lambda row: row["Sales"] / row["Clicks"] if row["Clicks"] > 0 else 0,
        axis=1
    )

    # Grouped summary of ASIN
    bulk_summary = filtered_bulk_df.groupby("Campaign Name (Informational only)").agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum"
    }).reset_index()

    # Calculate additional metrics
    bulk_summary["AOV"] = bulk_summary["Sales"] / bulk_summary["Orders"]
    bulk_summary["Click to Conversion"] = bulk_summary["Clicks"] / bulk_summary["Orders"]
    bulk_summary["CPC"] = bulk_summary["Spend"] / bulk_summary["Clicks"]
    bulk_summary["RPC"] = bulk_summary["Sales"] / bulk_summary["Clicks"]
    # Create a new column "key" in bulk_summary
    
    # Create a new column "New bid" in filtered_bulk_df and initialize with None
    filtered_bulk_df["New bid"] = pd.NA  # Using pd.NA instead of None for better pandas compatibility

    # Iterate over each row in campaign_bid_df
    for _, row in campaign_bid_df.iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        multiple = row["Multiplier"]
       
        # Update the "New bid" column in filtered_bulk_df where the campaign name matches
        filtered_bulk_df.loc[filtered_bulk_df["Campaign Name (Informational only)"] == campaign_name, "New bid"] = ((filtered_bulk_df.apply(
            lambda row: row["RPC"] if row["Campaign Name (Informational only)"] == campaign_name else row["New bid"],
            axis=1
        ))*target_acos)/(1+multiple)
    # Iterate over each row in filtered_bulk_df where "New bid" is not NaN
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].notna()].iterrows():
        # Check if the new bid is greater than 1.2 times the original bid
        if row["New bid"] > 1.2 * row["Bid"]:
            # Set the new bid to 1.2 times the original bid
            filtered_bulk_df.at[row.name, "New bid"] = 1.2 * row["Bid"]
#==================================================Plcement done==================================================
    # Iterate over each row in filtered_bulk_df where "New bid" is blank and "Clicks" is 0
    for index, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna() | (filtered_bulk_df["New bid"] == 0)].iterrows():
        
        campaign_name = row["Campaign Name (Informational only)"]
        
        # Skip if campaign_name is NaN or not a string
        if pd.isna(campaign_name) or not isinstance(campaign_name, str):
            continue

        # Find the CPC for the campaign from bulk_summary
        campaign_cpc_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["CPC"].values
        # Use default CPC of 5 if no CPC values are found or if CPC is NaN or 0
        campaign_cpc = campaign_cpc_values[0] if len(campaign_cpc_values) > 0 and not pd.isna(campaign_cpc_values[0]) and campaign_cpc_values[0] > 0 else 5

        # Handle invalid or missing bid values
        bid = row["Bid"] if not pd.isna(row["Bid"]) and row["Bid"] > 0 else row["Ad Group Default Bid (Informational only)"]

        # Calculate New Bid
        if row["Clicks"] == 0:
            # If clicks are 0, use the default logic
            new_bid = max(1, min(bid * 1.1, campaign_cpc))  # At least 1
        else:
            # If clicks are greater than 0, adjust the bid based on ACOS
            if row["ACOS"] > target_acos:
                new_bid = row["CPC"] * (target_acos / row["ACOS"])
            else:
                new_bid = round(min(row["CPC"] * 1.1, campaign_cpc), 2)
                if new_bid < 1:
                    new_bid = 1

        # Debug log for problematic cases
        if new_bid == 0:
            print(f"ERROR: Campaign '{campaign_name}' Row ID {index} resulted in New bid 0. Bid: {bid}, CPC: {campaign_cpc}")

        # Assign new bid
        filtered_bulk_df.at[index, "New bid"] = new_bid 
    # Iterate over each row in filtered_bulk_df where "New bid" is still NaN and "Clicks" > 0
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna() | (filtered_bulk_df["New bid"] == 0) & (filtered_bulk_df["Orders"] == 0) & (filtered_bulk_df["Clicks"] > 0)].iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        
        # Skip if campaign_name is NaN or not a string
        if pd.isna(campaign_name) or not isinstance(campaign_name, str):
            continue
        
        # Find the CPC for the campaign from bulk_summary
        campaign_cpc_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["CPC"].values
        campaign_aov_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["AOV"].values
        campaign_clicks_to_conversion_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["Clicks to conversion"].values
        # Use default CPC of 5 if no CPC values are found or if CPC is NaN or 0
        campaign_cpc = campaign_cpc_values[0] if len(campaign_cpc_values) > 0 and not pd.isna(campaign_cpc_values[0]) and campaign_cpc_values[0] > 0 else 5
        campaign_aov = campaign_aov_values[0] if len(campaign_aov_values) > 0 and not pd.isna(campaign_aov_values[0]) and campaign_aov_values[0] > 0 else 0
        campaign_clicks_to_conversion = campaign_clicks_to_conversion_values[0] if len(campaign_clicks_to_conversion_values) > 0 and not pd.isna(campaign_clicks_to_conversion_values[0]) and campaign_clicks_to_conversion_values[0] > 0 else 0
        # Handle invalid or missing bid values
        bid = row["Bid"] if not pd.isna(row["Bid"]) and row["Bid"] > 0 else row["Ad Group Default Bid (Informational only)"]

        # Calculate New Bid
        new_bid = (campaign_aov * target_acos) / (campaign_clicks_to_conversion + row["Clicks"])
        if new_bid < 1:
            new_bid = 1
        
        if new_bid > bid:
            new_bid = bid
        # Assign new bid
        filtered_bulk_df.at[row.name, "New bid"] = new_bid
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna() | (filtered_bulk_df["New bid"] == 0) & (filtered_bulk_df["Orders"] > 0) & (filtered_bulk_df["Clicks"] > 0)].iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        
        # Skip if campaign_name is NaN or not a string
        if pd.isna(campaign_name) or not isinstance(campaign_name, str):
            continue
        
        # Find the CPC for the campaign from bulk_summary
        campaign_cpc_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["CPC"].values
        # Use default CPC of 5 if no CPC values are found or if CPC is NaN or 0
        campaign_cpc = campaign_cpc_values[0] if len(campaign_cpc_values) > 0 and not pd.isna(campaign_cpc_values[0]) and campaign_cpc_values[0] > 0 else 5

        # Handle invalid or missing bid values
        bid = row["Bid"] if not pd.isna(row["Bid"]) and row["Bid"] > 0 else row["Ad Group Default Bid (Informational only)"]

        # Check if ACOS is greater than target ACOS
        if row["ACOS"] > target_acos:
            # Calculate the new bid as row CPC * (target ACOS / row ACOS)
            new_bid = row["CPC"] * (target_acos / row["ACOS"])
        else:
            # Calculate the new bid as the minimum of row CPC * 1.1 and the CPC derived from bulk_summary
            new_bid = round(min(row["CPC"] * 1.1, campaign_cpc), 2)
            if new_bid < 1:
                new_bid = 1
        
        # Update the "New bid" column in filtered_bulk_df
        filtered_bulk_df.at[row.name, "New bid"] = new_bid
    
    def adjust_bid(bid):
        new_bid = max(bid, 1.00)
        return round(new_bid, 2)
    filtered_bulk_df["New bid"] = filtered_bulk_df["New bid"].apply(adjust_bid)

    # Create the placement_df DataFrame from placement_data
    filtered_bulk_df_mk = filtered_bulk_df
    valid_campaigns_mk = valid_campaigns
    RPC_df_mk = RPC_df
    bulk_summary_mk = bulk_summary
    return filtered_bulk_df_mk, valid_campaigns_mk, RPC_df_mk, bulk_summary_mk

def match_headers(actual_headers, expected_headers):
    
    header_mapping = {}
    for header in actual_headers:
        match, score = process.extractOne(header, expected_headers)
        if score > 80:  # Set a threshold for similarity
            header_mapping[header] = match
    return header_mapping

def standardize_headers(df, expected_headers):
    
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
            "14 Day Advertised ASIN Sales (₹)", "14 Day Brand Halo ASIN Sales (₹)"
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