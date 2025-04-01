import pandas as pd

def campaign_negation_mk(str_df: pd.DataFrame, bulk_df: pd.DataFrame, target_acos: float, multiplier: float ) -> pd.DataFrame:
    df_str = str_df
    df_str["Targeting"] = df_str.apply(
        lambda row: row["Keyword Text"] if pd.notna(row["Keyword Text"]) and row["Keyword Text"].strip() != "" else row["Product Targeting Expression"],
        axis=1
    )
    df_str["Targeting"] = df_str["Targeting"].fillna("").astype(str)

    #======================================STR summary=========================================
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

    #======================================Filtered DF=========================================
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

            # Calculate conversion as sum orders / sum clicks where campaign name = campaign_name
            campaign_summary = str_summary[str_summary["Campaign Name (Informational only)"] == campaign_name]
            if campaign_summary["Clicks"].values[0] == 0 or campaign_summary["Orders"].values[0] == 0:
                # If clicks are 0, use total orders of str_summary / total clicks
                conversion = str_summary["Orders"].sum() / str_summary["Clicks"].sum()
            else:
                conversion = campaign_summary["Orders"].values[0] / campaign_summary["Clicks"].values[0]
            click_to_conversion = 1/conversion if conversion != 0 else 30
            if row["Clicks"] > 3*click_to_conversion:
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
                "Product": "Sponsored Products",
                "Entity": "Negative Product Targeting",
                "Operation": "Create",
                "Campaign ID": str(campaign_id),  # Placeholder, will be filled later
                "Ad Group ID": str(ad_group_id),  # Placeholder, will be filled later
                "Campaign Name (Informational only)": campaign_name,
                "Ad Group Name (Informational only)": ad_group_name,
                "State": "enabled",
                "Keyword Text": " ",
                "Match Type": " ",
                "Product Targeting Expression": f"asin:\"{customer_search_term.upper()}\""
            })
        else:
            kw_rows.append({
                "Product": "Sponsored Products",
                "Entity": "Negative Keyword",
                "Operation": "Create",
                "Campaign ID": str(campaign_id),  # Placeholder, will be filled later
                "Ad Group ID": str(ad_group_id),  # Placeholder, will be filled later
                "Campaign Name (Informational only)": campaign_name,
                "Ad Group Name (Informational only)": ad_group_name,
                "State": "enabled",
                "Keyword Text": customer_search_term,
                "Match Type": "Negative Exact",
                "Product Targeting Expression": ""
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
        pt_df = pt_df[["Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Campaign Name (Informational only)", "Ad Group Name (Informational only)", "State", "Product Targeting Expression"]]
    if not kw_df.empty:     
        kw_df = kw_df[["Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Campaign Name (Informational only)", "Ad Group Name (Informational only)", "State", "Keyword Text"]]
     #CHANGE: Filter pt_df and kw_df based on conditions from df_bulk_report
    negative_keywords = df_bulk_report[
        df_bulk_report["Match Type"].isin(["Negative Exact", "Negative Phrase"])
    ][["Campaign Name (Informational only)", "Ad Group Name (Informational only)", "Keyword Text"]]

    # Remove rows in pt_df where the Customer Search Term exists in the negative keywords
    pt_df = pt_df[~pt_df.apply(
        lambda row: (row["Campaign Name (Informational only)"], row["Ad Group Name (Informational only)"], row["Product Targeting Expression"]) in 
                    negative_keywords.itertuples(index=False, name=None), axis=1)]  #CHANGE
    # Remove rows in kw_df where the Customer Search Term exists in the negative keywords
    kw_df = kw_df[~kw_df.apply(
        lambda row: (row["Campaign Name (Informational only)"], row["Ad Group Name (Informational only)"], row["Keyword Text"]) in 
                    negative_keywords.itertuples(index=False, name=None), axis=1)]  #CHANGE
    pt_df_mk = pt_df
    kw_df_mk = kw_df
    
    return pt_df_mk, kw_df_mk
