import pandas as pd
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
import numpy as np
from fuzzywuzzy import process
from typing import List
from .expected_header import get_expected_header
from .campaign_negation_mk import campaign_negation_mk
from .placement_optimised_mk_rev import placement_optimised_mk_rev
from .placement_optimised_sk_rev import placement_optimised_sk_rev
from .new_campaign import harvest_sb

def load_excel(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name)

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

def filter_campaigns_sk(df, column_name):
    sk = df[df[column_name].str.lower().str.startswith("b0")]
    
    return sk

def filter_campaigns_mk(df, column_name):
    mk = df[~df[column_name].str.lower().str.startswith("b0")]
    return mk

def load_and_process_reports(file_path, sheet_name_bulk, sheet_name_str, campaign_file_path, campaign_sheet):
        
    file_paths = {
        "str": file_path,
        "bulk": file_path,
        "campaign": campaign_file_path
    }

    sheet_names = {
        "str": sheet_name_str,
        "bulk": sheet_name_bulk,
        "campaign": campaign_sheet
    }

    expected_headers = get_expected_header()

    # Load DataFrames with proper dtypes
    dfs = {key: pd.read_excel(file_paths[key], sheet_names[key], dtype={"Campaign ID": str, "Ad Group ID": str, "Keyword ID": str}) for key in file_paths}
    dfs = {key: standardize_headers(dfs[key], expected_headers[key]) for key in dfs}

    # Fix: Change "placement" to "campaign" in the filtered_data dictionary
    filtered_data = {
        "str_sk": filter_campaigns_sk(dfs["str"], "Campaign Name (Informational only)"),
        "bulk_sk": filter_campaigns_sk(dfs["bulk"], "Campaign Name (Informational only)"),
        "campaign_sk": filter_campaigns_sk(dfs["campaign"], "Campaign Name"),  # Changed from placement_sk
        "str_mk": filter_campaigns_mk(dfs["str"], "Campaign Name (Informational only)"),
        "bulk_mk": filter_campaigns_mk(dfs["bulk"], "Campaign Name (Informational only)"),
        "campaign_mk": filter_campaigns_mk(dfs["campaign"], "Campaign Name")  # Changed from placement_mk
    }

    return filtered_data

def final_sb_optimisation(file_path, sheet_name_bulk, sheet_name_str, output_file_path, target_acos, campaign_file_path, campaign_sheet):
    
    filtered_data = load_and_process_reports(file_path, sheet_name_bulk, sheet_name_str, campaign_file_path, campaign_sheet)
    
    target_df,harvested_df=harvest_sb(filtered_data["bulk_sk"],filtered_data["str_sk"], target_acos)

    filtered_bulk_df, placement_df,combined_df, top_of_search_df, rest_of_search_df = placement_optimised_mk_rev(filtered_data["campaign_mk"], filtered_data["bulk_mk"], target_acos)
    filtered_bulk_df_sk, placement_df_sk,combined_df_sk, top_of_search_df_sk, rest_of_search_df_sk = placement_optimised_sk_rev(filtered_data["campaign_sk"], filtered_data["bulk_sk"], target_acos)
    # filtered_bulk_df_sk=pd.DataFrame()
    # placement_df_sk=pd.DataFrame()
    # Remove rows from placement_df_sk where placement ratio is 0 or Campaign ID length is less than 1
    # placement_df_sk = placement_df_sk[(placement_df_sk["Placement ratio"] != 0) & (placement_df_sk["Campaign ID"].astype(str).str.len() >= 1)]
    # Drop the column named 'ASIN' in placement_df_sk if it exists
    if "ASIN" in placement_df_sk.columns:
        placement_df_sk = placement_df_sk.drop(columns=["ASIN"])

    pt_df_mk, kw_df_mk = campaign_negation_mk(
        bulk_df=filtered_data["bulk_mk"],
        str_df=filtered_data["str_mk"],
        target_acos=target_acos
    )
    
    bid_optimisation_df = pd.concat([filtered_bulk_df, filtered_bulk_df_sk], ignore_index=True)
    placement_optimisation_df = pd.concat([placement_df, placement_df_sk], ignore_index=True)

    # Save to Excel
    with pd.ExcelWriter(output_file_path, engine="xlsxwriter") as writer:
        target_df.to_excel(writer, sheet_name="Target Data", index=False)
        bid_optimisation_df.to_excel(writer, sheet_name="Bid Optimisation", index=False)
        placement_optimisation_df.to_excel(writer, sheet_name="Placement Optimisation", index=False)
        harvested_df.to_excel(writer, sheet_name="Harvested Data", index=False)
        
        # Commenting out less essential sheets to reduce file size
        # pt_df_mk.to_excel(writer, sheet_name="PT Data", index=False)
        # kw_df_mk.to_excel(writer, sheet_name="KW Data", index=False)
        # filtered_bulk_df.to_excel(writer, sheet_name="Filtered Bulk Data MK", index=False)
        # filtered_bulk_df_sk.to_excel(writer, sheet_name="Filtered Bulk Data SK", index=False)
        # placement_df.to_excel(writer, sheet_name="Placement Data MK", index=False)
        # placement_df_sk.to_excel(writer, sheet_name="Placement Data SK", index=False)
        # combined_df.to_excel(writer, sheet_name="Aggregated Data", index=False)
        # placement_summary.to_excel(writer, sheet_name="Placement Summary", index=False)
if __name__ == "__main__":
    bulk_file_path = '/mnt/c/Users/arun/Downloads/Reports/bulk skillofun wk10.xlsx'
    campaign_file_path = '/mnt/c/Users/arun/Downloads/Reports/shumee sb placement wk10.xlsx'
    target_acos = 0.30
    sheet_name_bulk = 'Sponsored Brands Campaigns'
    sheet_name_sbr = 'SB Search Term Report'
    campaign_sheet = 'Sponsored_Brands_Campaign_placement'
    output_file_path = '/mnt/c/Users/arun/Downloads/Reports/Output_data_SB.xlsx'
    final_sb_optimisation(bulk_file_path, sheet_name_bulk, sheet_name_sbr, output_file_path, target_acos, campaign_file_path, campaign_sheet)
