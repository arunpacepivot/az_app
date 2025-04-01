import pandas as pd
from fuzzywuzzy import process

#load excel sheet
def input_excel(input_file_path, input_sheet_name):
    return pd.read_excel(input_file_path, sheet_name=input_sheet_name)


#filter for columns
def filter_columns(bulk_df):
    filtered_bulk_df = bulk_df[
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["State"] == "enabled") &
        (bulk_df["Ad Group State (Informational only)"] == "enabled") &
        (bulk_df["Entity"].isin(["Contextual Targeting", "Audience Targeting"]))
    ].copy()
    return filtered_bulk_df

#summarize by campaign
def summarize_by_campaign(bulk_df):
    aggregated_df: pd.DataFrame = bulk_df.groupby("Campaign Name (Informational only)").agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum",
        "Units": "sum"
    }).reset_index()
    return aggregated_df

#add ideal bid
def add_ideal_bid(bulk_df):
    bulk_df["ideal bid"] = 0.0
    return bulk_df


#calculate bids
def calculate_bids(bulk_df, aggregated_df, target_acos):
    filtered_df=bulk_df.copy()
    for index, row in filtered_df.iterrows():
        if row["Clicks"] == 0:
            # Case 1: Clicks = 0
            filtered_df.at[index, "ideal bid"] = row["Bid"] * 1.1
        elif row["Orders"] > 0 and row["ACOS"] > target_acos:
            # Case 2: Orders > 0 and ACOS > target ACOS
            filtered_df.at[index, "ideal bid"] = (row["Sales"] / row["Clicks"]) * target_acos
        elif row["Orders"] > 0 and row["ACOS"] <= target_acos:
            # Case 3: Orders > 0 and ACOS <= target ACOS
            if row["ACOS"] < 0.5 * target_acos:
                multiplier = 1.5
            elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                multiplier = 1.25
            else:
                multiplier = 1.1

            campaign_name = row["Campaign Name (Informational only)"]
            overall_cpc = aggregated_df["Spend"].sum() / aggregated_df["Clicks"].sum() if aggregated_df["Clicks"].sum() > 0 else 0.0
            campaign_cpc = (aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Spend"].values[0] / 
                            aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Clicks"].values[0]) if aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Clicks"].values[0] > 0 else overall_cpc
            filtered_df.at[index, "ideal bid"] = row["CPC"] * multiplier
        elif row["Clicks"] > 0 and row["Orders"] == 0:
            # Case 4: Clicks > 0 and Orders = 0
            campaign_name = row["Campaign Name (Informational only)"]

            campaign_aov = aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Sales"].values[0] / aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Orders"].values[0] if aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Orders"].values[0] > 0 else 0.0

            campaign_clicks_to_conversion = aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Clicks"].values[0] / aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Orders"].values[0] if aggregated_df[aggregated_df["Campaign Name (Informational only)"] == campaign_name]["Orders"].values[0] > 0 else 0.0

            overall_aov = aggregated_df["Sales"].sum() / aggregated_df["Orders"].sum() if aggregated_df["Orders"].sum() > 0 else 0.0

            overall_clicks_to_conversion = aggregated_df["Clicks"].sum() / aggregated_df["Orders"].sum() if aggregated_df["Orders"].sum() > 0 else 0.0

            aov = campaign_aov if campaign_aov > 0 else overall_aov
            clicks_to_conversion = campaign_clicks_to_conversion if campaign_clicks_to_conversion > 0 else overall_clicks_to_conversion
            clicks_to_conversion = clicks_to_conversion if clicks_to_conversion > 0 else 1

            filtered_df.at[index, "ideal bid"] = (aov * target_acos) / (row["Clicks"] + clicks_to_conversion)
    return filtered_df

#print in excel
def print_in_excel(optimised_df, output_file_path):
    optimised_df.to_excel(output_file_path, sheet_name="Optimised Bids", index=False)

#main functions
def load_and_process_reports(input_file_path, input_sheet_name, output_file_path, target_acos):
    bulk_df=input_excel(input_file_path, input_sheet_name)
    bulk_df=filter_columns(bulk_df)
    aggregated_df=summarize_by_campaign(bulk_df)
    bulk_df=add_ideal_bid(bulk_df)
    optimised_df=calculate_bids(bulk_df, aggregated_df, target_acos)
    print_in_excel(optimised_df, output_file_path)
    

if __name__ == "__main__":
    # This block is only used for local testing
    input_file_path = "example_bulk_file.xlsx"
    input_sheet_name = "Sponsored Display Campaigns"
    output_file_path = "output_sd.xlsx"
    target_acos = 0.3

    load_and_process_reports(input_file_path, input_sheet_name, output_file_path, target_acos)

