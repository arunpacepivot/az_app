import pandas as pd

def campaign_negation_sk(str_df: pd.DataFrame, bulk_df: pd.DataFrame, target_acos: float, multiplier: float ) -> pd.DataFrame:
    df_str = str_df.copy()
    # Add "ASIN" column by extracting the first word from "Campaign Name"
    df_str.loc[:, "ASIN"] = df_str["Campaign Name (Informational only)"].apply(lambda x: x.split()[0])
    df_str["Targeting"] = df_str.apply(
        lambda row: row["Keyword Text"] if pd.notna(row["Keyword Text"]) and row["Keyword Text"].strip() != "" else row["Product Targeting Expression"],
        axis=1
    )
    
    # This line fills any NaN values in the "Targeting" column with an empty string and ensures the column is of type string
    df_str["Targeting"] = df_str["Targeting"].fillna("").astype(str)
    #======================================ASIN summary=========================================
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

    #======================================Filtered DF=========================================
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
            conversion = str_summary[str_summary["ASIN"] == asin]["Conversion"].values[0]
            max_spend = aov * target_acos * multiplier
            
            # Filter rows where spend is greater than max_spend
            if spend > max_spend:
                filtered_rows.append(row)
            # Calculate conversion as sum orders / sum clicks where campaign name = campaign_name
            campaign_summary = str_summary[str_summary["ASIN"] == asin]
            if campaign_summary["Clicks"].values[0] == 0 or campaign_summary["Orders"].values[0] == 0:
                # If clicks are 0, use total orders of str_summary / total clicks
                conversion = str_summary["Orders"].sum() / str_summary["Clicks"].sum()
            else:
                conversion = campaign_summary["Orders"].values[0] / campaign_summary["Clicks"].values[0]
            click_to_conversion = 1/conversion if conversion != 0 else 30
            
            if row["Clicks"] > 3*click_to_conversion:
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
                "Product Targeting Expression": " "
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
        lambda row: (row["Campaign Name (Informational only)"], row["Ad Group Name (Informational only)"], row["Product Targeting Expression"]) in 
                    negative_keywords.itertuples(index=False, name=None), axis=1)]  #CHANGE

    # Remove rows in kw_df where the Customer Search Term exists in the negative keywords
    kw_df = kw_df[~kw_df.apply(
        lambda row: (row["Campaign Name (Informational only)"], row["Ad Group Name (Informational only)"], row["Keyword Text"]) in 
                    negative_keywords.itertuples(index=False, name=None), axis=1)]  #CHANGE
    
    return pt_df, kw_df 
