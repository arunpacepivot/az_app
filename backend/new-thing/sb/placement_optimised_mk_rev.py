import pandas as pd
from typing import List, Tuple
import warnings
warnings.filterwarnings("ignore")

def process_campaign_placement(placement_df: pd.DataFrame, target_acos: float) -> pd.DataFrame:
    # Create explicit copy of input DataFrame
    placement_df = placement_df.copy()
    
    
    # Remove all columns to the right of "14 Day Conversion Rate"
    if "14 Day Conversion Rate" in placement_df.columns:
        placement_df = placement_df.loc[:, : "14 Day Conversion Rate"]

    # Drop percentage columns from placement_df
    columns_to_drop: List[str] = [
        "Click-Thru Rate (CTR)", 
        "Total Advertising Cost of Sales (ACOS)", 
        "Total Return on Advertising Spend (ROAS)", 
        "14 Day Conversion Rate",
        "Viewable Impressions",
        "Cost per 1,000 viewable impressions (VCPM)",

    ]
    
    # Ensure columns exist before attempting to drop them
    columns_to_drop = [col for col in columns_to_drop if col in placement_df.columns]
    placement_df = placement_df.drop(columns=columns_to_drop)

    # Filter for campaigns where Placement is not "Top of Search on Amazon"
    rest_of_search_df = placement_df[placement_df["Placement"] != "Top of Search on Amazon"]

    # Define the metrics to aggregate
    metrics_to_aggregate: List[str] = [
        "Impressions", "Clicks", "Spend", "14 Day Total Sales (â‚¹)", 
        "14 Day Total Orders (#)", "14 Day Total Units (#)"
    ]

    # Aggregate metrics by Campaign Name
    aggregated_rest_of_search_df = rest_of_search_df.groupby("Campaign Name")[metrics_to_aggregate].sum().reset_index()

    # Add a column for Placement and set it to "Rest of Search on Amazon"
    aggregated_rest_of_search_df["Placement"] = "Rest of Search on Amazon"

    # Create explicit copy when filtering
    top_of_search_df = placement_df[placement_df["Placement"] == "Top of Search on Amazon"].copy()

    # Concatenate the aggregated rows into placement_df
    placement_df = pd.concat([placement_df, aggregated_rest_of_search_df], ignore_index=True)

    placement_df["CPC"]=placement_df["Spend"]/placement_df["Clicks"]
    placement_df["ACOS"]=placement_df["Spend"]/placement_df["14 Day Total Sales (â‚¹)"]
    placement_df["CVR"]=placement_df["14 Day Total Orders (#)"]/placement_df["Clicks"]

    # Combine top_of_search_df and aggregated_rest_of_search_df into a new DataFrame
    combined_df = pd.concat([top_of_search_df, aggregated_rest_of_search_df], ignore_index=True).sort_values(by="Campaign Name")

    # Calculate metrics for combined_df
    combined_df.loc[:, "CPC"] = combined_df["Spend"] / combined_df["Clicks"].replace(0, float("nan"))
    combined_df.loc[:, "ACOS"] = combined_df["Spend"] / combined_df["14 Day Total Sales (â‚¹)"].replace(0, float("nan"))
    combined_df.loc[:, "CVR"] = combined_df["14 Day Total Orders (#)"] / combined_df["Clicks"].replace(0, float("nan"))

    # Replace infinities and NaN with 0
    combined_df = combined_df.replace([float("inf"), float("-inf")], 0).fillna(0)

    #Calculate overall RPC
    overall_rpc = combined_df["14 Day Total Sales (â‚¹)"].sum() / combined_df["Clicks"].sum() if combined_df["Clicks"].sum() > 0 else 0.0

    # Calculate Top of Search RPC
    top_of_search_sales_sum = placement_df[placement_df["Placement"] == "Top of Search on Amazon"]["14 Day Total Sales (â‚¹)"].sum()
    top_of_search_clicks_sum = placement_df[placement_df["Placement"] == "Top of Search on Amazon"]["Clicks"].sum()

    top_of_search_rpc = top_of_search_sales_sum / top_of_search_clicks_sum if top_of_search_clicks_sum > 0 else overall_rpc

     # Calculate Rest of Search RPC
    rest_of_search_sales_sum = placement_df[placement_df["Placement"] == "Rest of Search on Amazon"]["14 Day Total Sales (â‚¹)"].sum()
    rest_of_search_clicks_sum = placement_df[placement_df["Placement"] == "Rest of Search on Amazon"]["Clicks"].sum()

    rest_of_search_rpc = rest_of_search_sales_sum / rest_of_search_clicks_sum if rest_of_search_clicks_sum > 0 else overall_rpc
    

    # Use .loc for setting values
    combined_df.loc[:, "RPC"] = 0.0

    # Calculate RPC for each row where conditions are met
    condition = (combined_df["14 Day Total Sales (â‚¹)"] > 0) & (combined_df["Clicks"] > 0)

    combined_df.loc[condition, "RPC"] = (
        combined_df.loc[condition, "14 Day Total Sales (â‚¹)"] / 
        combined_df.loc[condition, "Clicks"]
    )
    # Set RPC for remaining rows
    combined_df.loc[~condition & (combined_df["Placement"] == "Top of Search on Amazon"), "RPC"] = top_of_search_rpc
    combined_df.loc[~condition & (combined_df["Placement"] == "Rest of Search on Amazon"), "RPC"] = rest_of_search_rpc

    # Calculate sums
    total_clicks_sum = combined_df["Clicks"].sum()

  

    # Initialize Ideal Bid column
    combined_df.loc[:, "Ideal Bid"] = 0.0

    # Calculate overall CPC
    total_spend_sum = combined_df["Spend"].sum()
    overall_cpc = total_spend_sum / total_clicks_sum if total_clicks_sum > 0 else 0.0
    # Add a column called "Bid Multiplier" which is the ratio of RPC for Top of Search to RPC for Rest of Search for each campaign.
    combined_df.loc[:, "Bid Multiplier"] = 0.0

    # Calculate the ratio for each campaign where Placement is "Top of Search on Amazon"
    unique_campaign_names = combined_df["Campaign Name"].unique()
    for campaign in unique_campaign_names:
        top_of_search_rpc = combined_df[
            (combined_df["Campaign Name"] == campaign) & 
            (combined_df["Placement"] == "Top of Search on Amazon")
        ]["RPC"].values

        rest_of_search_rpc = combined_df[
            (combined_df["Campaign Name"] == campaign) & 
            (combined_df["Placement"] == "Rest of Search on Amazon")
        ]["RPC"].values

        if len(top_of_search_rpc) > 0 and len(rest_of_search_rpc) > 0 and rest_of_search_rpc[0] != 0:
            ratio = top_of_search_rpc[0] / rest_of_search_rpc[0]
            combined_df.loc[
                (combined_df["Campaign Name"] == campaign) & 
                (combined_df["Placement"] == "Top of Search on Amazon"), 
                "Bid Multiplier"
            ] = ratio

    # Create a new DataFrame with only rows where Placement is "Top of Search on Amazon"
    top_of_search_df = combined_df[combined_df["Placement"] == "Top of Search on Amazon"].copy()

    # Ensure the new DataFrame is not empty
    if top_of_search_df.empty:
        print("No rows found with Placement 'Top of Search on Amazon'")

    # Reset the index of the new DataFrame
    top_of_search_df.reset_index(drop=True, inplace=True)

#=========================ideal Bid calculation for Rest of search placement===============================
    # Calculate ideal bids
    for index, row in combined_df.iterrows():
        if row["ACOS"] > target_acos:
            combined_df.loc[index, "Ideal Bid"] = target_acos * row["RPC"]
        else:
            row_cpc = row["Spend"] / row["Clicks"] if row["Clicks"] > 0 else 0.0
            combined_df.loc[index, "Ideal Bid"] = min(1.1 * row_cpc, overall_cpc)

    # Process final bid values
    combined_df.loc[:, "Ideal Bid"] = combined_df["Ideal Bid"].apply(lambda x: max(1.5, round(x, 2)))



    #==============================Placement check==============================
    combined_df["Placement ratio"] = 0.0
    combined_df["Incr/decr"] = ""

    for campaign in unique_campaign_names:
        group = combined_df[combined_df["Campaign Name"] == campaign]
        # Change "ideal bid" to "Ideal Bid" to match the correct column name
        top_of_search_row = group[
            (group["Placement"] == "Top of Search on Amazon") & 
            (group["Ideal Bid"] > 0)  # Changed from "ideal bid" to "Ideal Bid"
        ]
        other_placements_row = group[
            (group["Placement"] == "Rest of Search on Amazon") & 
            (group["Ideal Bid"] > 0)  # Changed from "ideal bid" to "Ideal Bid"
        ]

        if not top_of_search_row.empty and not other_placements_row.empty:
            # Calculate the ratio of ideal bids
            ratio = other_placements_row["Ideal Bid"].values[0] / top_of_search_row["Ideal Bid"].values[0] # Changed from "ideal bid" to "Ideal Bid"
            
            ratio = round((ratio - 1),2)

            if ratio > 0:
                combined_df.loc[other_placements_row.index, "Incr/decr"] = "Increase"
            else:
                combined_df.loc[other_placements_row.index, "Incr/decr"] = "Decrease"
            
            combined_df.loc[other_placements_row.index, "Placement ratio"] = ratio
            combined_df.loc[top_of_search_row.index, "Placement ratio"] = 0.0

    
    rest_of_search_df = combined_df[combined_df["Placement"] == "Rest of Search on Amazon"].copy()

    # Ensure the new DataFrame is not empty
    if rest_of_search_df.empty:
        print("No rows found with Placement 'Rest of Search on Amazon'")

    # Reset the index of the new DataFrame
    rest_of_search_df.reset_index(drop=True, inplace=True)

    return combined_df, rest_of_search_df, top_of_search_df
 
def process_bulk_data(bulk_df: pd.DataFrame, target_acos: float, bid_multiplier_df: pd.DataFrame, placement_df: pd.DataFrame) -> pd.DataFrame:
    bulk_df = bulk_df.copy()
    # Filter bulk_df for rows where the Campaign State (Informational only) is "enabled", State is "enabled",
    # and Entity is either "Keyword" or "Product"
    filtered_bulk_df = bulk_df[
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["State"] == "enabled") &
        (bulk_df["Campaign Serving Status (Informational only)"] == "Running") &
        (bulk_df["Entity"].isin(["Keyword", "Product"]))
    ].copy()

    campaign_id_map = filtered_bulk_df.drop_duplicates(subset=["Campaign Name (Informational only)"]).set_index("Campaign Name (Informational only)")["Campaign ID"]

    # Group filtered_bulk_df by 'Campaign Name (Informational only)' and aggregate the required metrics
    aggregated_df: pd.DataFrame = filtered_bulk_df.groupby("Campaign Name (Informational only)").agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum",
        "Units": "sum"
    }).reset_index()

    # Calculate overall CPC
    total_sales_sum = aggregated_df["Sales"].sum()
    overall_cpc = (total_sales_sum / aggregated_df["Clicks"].sum()) * target_acos if aggregated_df["Clicks"].sum() > 0 else 0.0
    overall_aov = total_sales_sum / aggregated_df["Orders"].sum() if aggregated_df["Orders"].sum() > 0 else 0.0
    overall_Clicks_to_conversion = aggregated_df["Clicks"].sum() / aggregated_df["Orders"].sum() if aggregated_df["Orders"].sum() > 0 else 0.0
    
    # Create a new column 'ideal bid' in filtered_bulk_df and initialize it with default value 0.0
    filtered_bulk_df["ideal bid"] = 0.0

    for index, row in filtered_bulk_df.iterrows():
        if row["Clicks"] == 0:
            filtered_bulk_df.at[index, "ideal bid"] = row["Bid"] * 1.1
        elif row["Clicks"] > 0 and row["Orders"] > 0 and row["ACOS"] > target_acos:
            filtered_bulk_df.at[index, "ideal bid"] = (row["Sales"] / row["Clicks"]) * target_acos
        elif row["Clicks"] > 0 and row["Orders"] > 0 and row["ACOS"] <= target_acos:
            campaign_name = row["Campaign Name (Informational only)"]
            campaign_cpc = (aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Sales"].values[0] / 
                            aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Clicks"].values[0]) * target_acos if aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Clicks"].values[0] > 0 else overall_cpc
            filtered_bulk_df.at[index, "ideal bid"] = min(1.5 * row["CPC"], campaign_cpc)
        elif row["Clicks"] > 0 and row["Orders"] == 0:
            campaign_name = row["Campaign Name (Informational only)"]
            campaign_cpc = (aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Sales"].values[0] / 
                            aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Clicks"].values[0]) * target_acos if aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Clicks"].values[0] > 0 else overall_cpc
            campaign_AOV = aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Sales"].values[0] / aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Orders"].values[0] if aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Orders"].values[0] > 0 else overall_aov
            campaign_Clicks_to_conversion = aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Clicks"].values[0] / aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Orders"].values[0] if aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Orders"].values[0] > 0 else overall_Clicks_to_conversion
            campaign_Clicks_to_conversion = campaign_Clicks_to_conversion if campaign_Clicks_to_conversion > 0 else 1

            bid_value = (campaign_AOV*target_acos)/(row["Clicks"]+campaign_Clicks_to_conversion)
            if bid_value > row["Bid"]:
                filtered_bulk_df.at[index, "ideal bid"] = row["Bid"]
            else:
                filtered_bulk_df.at[index, "ideal bid"] = bid_value
        else:
            filtered_bulk_df.at[index, "ideal bid"] = 5.0
        
    bid_multiplier_df = bid_multiplier_df.copy()
    # Create a new column 'bid multiplier' in filtered_bulk_df and initialize it with default value 1
    filtered_bulk_df["bid multiplier"] = 1.0

    # Iterate over each row in filtered_bulk_df to set the 'bid multiplier' value
    for index, row in filtered_bulk_df.iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        
        # Check if the campaign name exists in bid_multiplier_df
        if campaign_name in bid_multiplier_df["Campaign Name"].values:
            bid_multiplier_value = bid_multiplier_df[bid_multiplier_df["Campaign Name"] == campaign_name]["Bid Multiplier"].values[0]
        else:
            bid_multiplier_value = 1.0
        
        # Check if the row's Sales is 0, then set bid_multiplier to 1
        if row["Sales"] == 0:
            bid_multiplier_value = 1.0

        if row["ACOS"] > target_acos and bid_multiplier_value > 1:
            bid_multiplier_value = 1.0
        
        if bid_multiplier_value > 6:
            bid_multiplier_value = 6
        # Set the 'bid multiplier' value in filtered_bulk_df
        filtered_bulk_df.at[index, "bid multiplier"] = bid_multiplier_value
   
    
    # Create a new column 'final bid' in filtered_bulk_df
    filtered_bulk_df["final bid"] = filtered_bulk_df["ideal bid"] * filtered_bulk_df["bid multiplier"]
    
    # Ensure that 'final bid' is at least 1
    filtered_bulk_df["final bid"] = filtered_bulk_df["final bid"].apply(lambda x: max(x, 1))
    
    # Round the 'final bid' to 2 decimal places
    filtered_bulk_df["final bid"] = filtered_bulk_df["final bid"].round(2)
    
    # Ensure that 'final bid' is at least 1.5
    filtered_bulk_df["final bid"] = filtered_bulk_df["final bid"].apply(lambda x: max(x, 1.5))

    placement_df = placement_df.copy()
    # Add a column called 'Campaign ID' to placement_df
    placement_df["Campaign ID"] = ""

    # Iterate over each unique campaign name in placement_df
    for campaign_name in placement_df["Campaign Name"].unique():
        # Check for Campaign ID in filtered_bulk_df
        campaign_id = filtered_bulk_df[filtered_bulk_df["Campaign Name (Informational only)"] == campaign_name]["Campaign ID"].values
        if len(campaign_id) > 0:
            # Copy the Campaign ID to the 'Campaign ID' column in placement_df
            placement_df.loc[placement_df["Campaign Name"] == campaign_name, "Campaign ID"] = campaign_id[0]
            
    
    return filtered_bulk_df, placement_df

def placement_optimised_mk_rev(placement_df: pd.DataFrame, bulk_df: pd.DataFrame, target_acos: float) -> pd.DataFrame:
    combined_df, rest_of_search_df, top_of_search_df = process_campaign_placement(
        placement_df=placement_df,
        target_acos=target_acos
    )   

    bid_multiplier_df = top_of_search_df.copy()
    placement_df = rest_of_search_df.copy()

    filtered_bulk_df, placement_df = process_bulk_data(
        bulk_df=bulk_df,
        target_acos=target_acos,
        bid_multiplier_df=bid_multiplier_df,
        placement_df=placement_df
    )
    # Drop columns 'ideal bid' and 'bid multiplier' from filtered_bulk_df if they exist
    columns_to_drop = ["ideal bid", "bid multiplier"]
    filtered_bulk_df = filtered_bulk_df.drop(columns=[col for col in columns_to_drop if col in filtered_bulk_df.columns])

    return filtered_bulk_df, placement_df,combined_df, top_of_search_df, rest_of_search_df

if __name__ == "__main__":
    # Define constants
    TARGET_ACOS = 0.3
    PLACEMENT_FILE_PATH = "/mnt/c/Users/arun/Downloads/Reports/shumee sb placement wk9.xlsx"
    PLACEMENT_SHEET_NAME = "Sponsored_Brands_Campaign_place"
    OUTPUT_FILE_PATH = "/mnt/c/Users/arun/Downloads/Reports/Output_data_test.xlsx"
    BULK_FILE_PATH = "/mnt/c/Users/arun/Downloads/Reports/bulk shumee wk9.xlsx"
    BULK_SHEET_NAME = "Sponsored Brands Campaigns"

    # Load data with proper dtypes
    dtype_map = {
        "Campaign ID": str,
        "Ad Group ID": str,
        "Keyword ID": str
    }
    
    # Read and process data
    placement_df = pd.read_excel(
        PLACEMENT_FILE_PATH,
        sheet_name=PLACEMENT_SHEET_NAME,
        dtype=dtype_map
    )
    
    bulk_df = pd.read_excel(
        BULK_FILE_PATH,
        sheet_name=BULK_SHEET_NAME,
        dtype=dtype_map
    )
    
    filtered_bulk_df, placement_df,combined_df, top_of_search_df, rest_of_search_df = placement_optimised_mk_rev(placement_df, bulk_df, TARGET_ACOS)
    
    # Save to Excel
    with pd.ExcelWriter(OUTPUT_FILE_PATH, engine="xlsxwriter") as writer:
        combined_df.to_excel(writer, sheet_name="placement", index=False)
        rest_of_search_df.to_excel(writer, sheet_name="Placement adjustment", index=False)
        top_of_search_df.to_excel(writer, sheet_name="Bid multiplier", index=False)
        filtered_bulk_df.to_excel(writer, sheet_name="Bulk", index=False)
        placement_df.to_excel(writer, sheet_name="Placement_id", index=False)
    

