from fuzzywuzzy import process
import pandas as pd
from sp_test.harvest import harvest_data_sk
from sp_test.harvest import build_campaign_rows
from sp_test.campaign_negation_sk import campaign_negation_sk
from sp_test.placement_optimise_sk_ab_net import placement_optimize_sk_ab_net
from sp_test.budget_optimise import budget_optimisation
from sp_test.campaign_negation_mk import campaign_negation_mk
from sp_test.placement_optimise_mk_ab_net import placement_optimize_mk_ab_net
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

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

def load_and_standardize_data(file_path, sheet_name, expected_headers):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    return standardize_headers(df, expected_headers)

def filter_campaign_data(df, prefix):
    return df[df["Campaign Name (Informational only)"].str.lower().str.startswith(prefix)]

def process_campaign_data(file_path, sheet_name_bulk, sheet_name_str):
    
    
    expected_headers_str = ["Product", "Campaign ID", "Ad Group ID", "Keyword ID", "Product Targeting ID", "Campaign Name (Informational only)", "Ad Group Name (Informational only)", "Portfolio Name (Informational only)", "State", "Campaign State (Informational only)", "Bid", "Keyword Text", "Match Type", "Product Targeting Expression", "Resolved Product Targeting Expression (Informational only)", "Customer Search Term", "Impressions", "Clicks", "Click-through Rate", "Spend", "Sales", "Orders", "Units", "Conversion Rate", "ACOS", "CPC", "ROAS"]
    
    expected_headers_bulk = ["Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Portfolio ID", "Ad ID", "Keyword ID", "Product Targeting ID", "Campaign Name", "Ad Group Name", "Campaign Name (Informational only)", "Ad Group Name (Informational only)", "Portfolio Name (Informational only)", "Start Date", "End Date", "Targeting Type", "State", "Campaign State (Informational only)", "Ad Group State (Informational only)", "Daily Budget", "SKU", "ASIN", "Eligibility Status (Informational only)", "Reason for Ineligibility (Informational only)", "Ad Group Default Bid", "Ad Group Default Bid (Informational only)", "Bid", "Keyword Text", "Native Language Keyword", "Native Language Locale", "Match Type", "Bidding Strategy", "Placement", "Percentage", "Product Targeting Expression", "Resolved Product Targeting Expression (Informational only)", "Impressions", "Clicks", "Click-through Rate", "Spend", "Sales", "Orders", "Units", "Conversion Rate", "ACOS", "CPC", "ROAS"]
    
    str_df = load_and_standardize_data(file_path, sheet_name_str, expected_headers_str)
    bulk_df = load_and_standardize_data(file_path, sheet_name_bulk, expected_headers_bulk)

    bulk_df = bulk_df[~bulk_df["Campaign Name (Informational only)"].str.lower().str.startswith("catchall")]
    
    str_sk = filter_campaign_data(str_df, "b0")
    str_mk = str_df[~str_df["Campaign Name (Informational only)"].str.lower().str.startswith("b0")]
    
    bulk_df["Campaign Name (Informational only)"] = bulk_df["Campaign Name (Informational only)"].fillna("").astype(str)
    bulk_sk = filter_campaign_data(bulk_df, "b0")
    bulk_mk = bulk_df[~bulk_df["Campaign Name (Informational only)"].str.lower().str.startswith("b0")]
    
    return str_sk, str_mk, bulk_sk, bulk_mk, bulk_df

def process_data(file_path, target_acos, sheet_name_bulk, sheet_name_str):
    str_sk, str_mk, bulk_sk, bulk_mk, bulk_df = process_campaign_data(file_path, sheet_name_bulk, sheet_name_str)
    
    deduped_df, result_df = harvest_data_sk(str_df=str_sk, bulk_df=bulk_sk, target_acos=target_acos)
    campaign_df = build_campaign_rows(deduped_df)
    pt_df, kw_df = campaign_negation_sk(str_df=str_sk, bulk_df=bulk_sk, target_acos=target_acos, multiplier=1.5)
    pt_df_mk, kw_df_mk = campaign_negation_mk(str_df=str_mk, bulk_df=bulk_mk, target_acos=target_acos, multiplier=1.5)
    
    filtered_bulk_df, valid_campaigns_sk, RPC_df, asin_summary = placement_optimize_sk_ab_net(bulk_df=bulk_sk, target_acos=target_acos)
    filtered_bulk_df_mk, RPC_df_mk, bulk_summary_mk, valid_campaigns_mk = placement_optimize_mk_ab_net(bulk_df=bulk_mk, target_acos=target_acos)
    budget_bulk_df_mk = budget_optimisation(bulk_df, target_acos)
    new_bid_df_mk = filtered_bulk_df_mk.drop(columns=["key", "RPC"], errors="ignore")
    
    return deduped_df, result_df, campaign_df, pt_df, kw_df, pt_df_mk, kw_df_mk, filtered_bulk_df, valid_campaigns_sk, RPC_df, asin_summary, filtered_bulk_df_mk, RPC_df_mk, bulk_summary_mk, budget_bulk_df_mk, new_bid_df_mk, valid_campaigns_mk

def save_to_excel(output_file_path, deduped_df, result_df, campaign_df, pt_df, kw_df, pt_df_mk, kw_df_mk, filtered_bulk_df, valid_campaigns_sk, RPC_df, asin_summary, filtered_bulk_df_mk,  RPC_df_mk, bulk_summary_mk, budget_bulk_df_mk, new_bid_df_mk, valid_campaigns_mk):
    
    # Combine filtered_bulk_df and new_bid_df_mk by appending new_bid_df_mk to filtered_bulk_df
    combined_df = pd.concat([filtered_bulk_df, new_bid_df_mk, budget_bulk_df_mk, valid_campaigns_mk, valid_campaigns_sk], ignore_index=True)
    pt_combined_df = pd.concat([pt_df, pt_df_mk], ignore_index=True)
    kw_combined_df = pd.concat([kw_df, kw_df_mk], ignore_index=True)
    # placement_combined_df = pd.concat([valid_campaigns, valid_campaigns_mk], ignore_index=True)
    RPC_combined_df = pd.concat([RPC_df, RPC_df_mk], ignore_index=True)
    bulk_summary_combined_df = pd.concat([asin_summary, bulk_summary_mk], ignore_index=True)
    # Sort combined_df by the "Entity" column
    # Define the custom sorting order for the "Entity" column
    entity_order = ["Keyword", "Product Targeting", "Bidding Adjustment", "Campaign"]
    
    # Create a categorical type with the specified order
    combined_df["Entity"] = pd.Categorical(combined_df["Entity"], categories=entity_order, ordered=True)
    
    # Sort the DataFrame by the "Entity" column using the custom order
    combined_df = combined_df.sort_values(by="Entity")

    # Drop the column named 'ASIN_Derived' in combined_df if it exists
    if "ASIN_Derived" in combined_df.columns:
        combined_df = combined_df.drop(columns=["ASIN_Derived"])

    with pd.ExcelWriter(output_file_path, engine="xlsxwriter") as writer:
        # Write each DataFrame to a specific sheet
        deduped_df.to_excel(writer, sheet_name="New campaigns", index=False)
        campaign_df.to_excel(writer, sheet_name="New campaigns-df", index=False)
        pt_combined_df.to_excel(writer, sheet_name="Product Negation", index=False)
        kw_combined_df.to_excel(writer, sheet_name="Keyword Negation", index=False)
        combined_df.to_excel(writer, sheet_name="Bids Optimized", index=False)
        # placement_combined_df.to_excel(writer, sheet_name="Placement Optimized", index=False)
        RPC_combined_df.to_excel(writer, sheet_name="RPC & Bids", index=False)
        bulk_summary_combined_df.to_excel(writer, sheet_name="ASIN Summary", index=False)
        result_df.to_excel(writer, sheet_name="Harvested Campaign", index=False)
        # filtered_df_str.to_excel(writer, sheet_name="Harvested Campaign SK", index=False)
        pt_df.to_excel(writer, sheet_name="Product Negation SK", index=False)
        pt_df_mk.to_excel(writer, sheet_name="Product Negation MK", index=False)
        kw_df.to_excel(writer, sheet_name="Keyword Negation SK", index=False)
        kw_df_mk.to_excel(writer, sheet_name="Keyword Negation MK", index=False)
        filtered_bulk_df.to_excel(writer, sheet_name="Bids Optimized SK", index=False)
        filtered_bulk_df_mk.to_excel(writer, sheet_name="Bids Optimized MK", index=False)
        new_bid_df_mk.to_excel(writer, sheet_name="Budget Optimized MK", index=False)
        valid_campaigns_sk.to_excel(writer, sheet_name="Placement Optimized SK", index=False)
        valid_campaigns_mk.to_excel(writer, sheet_name="Placement Optimized MK", index=False)
        RPC_df.to_excel(writer, sheet_name="RPC & Bids SK", index=False)
        RPC_df_mk.to_excel(writer, sheet_name="RPC & Bids MK", index=False)
        bulk_summary_mk.to_excel(writer, sheet_name="ASIN Summary MK", index=False)
        asin_summary.to_excel(writer, sheet_name="ASIN Summary SK", index=False)
    print(f"DataFrames have been successfully exported to {output_file_path}")

def final_sp_optimisation(file_path, output_file_path, target_acos, sheet_name_bulk, sheet_name_str):
    
    
    data = process_data(file_path, target_acos, sheet_name_bulk, sheet_name_str)
    save_to_excel(output_file_path, *data)


if __name__ == "__main__":
    file_path = '/mnt/c/Users/arun/Downloads/Reports/bulk skillofun wk11.xlsx'
    output_file_path = '/mnt/c/Users/arun/Downloads/Reports/Output_data.xlsx'
    target_acos = 0.30
    sheet_name_bulk = 'Sponsored Products Campaigns'
    sheet_name_str = 'SP Search Term Report'
    final_sp_optimisation(file_path, output_file_path, target_acos, sheet_name_bulk, sheet_name_str)

