import pandas as pd
import numpy as np
import datetime

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

#==========================Summary DF=========================================
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

#==========================Filtered DF=========================================
    # Filter df_str for where match type is not equal to "exact", targeting does not begin with "asin" and 14 day total orders >= 2
    filtered_df_str = df_str[
        (df_str["Match Type"] != "Exact") &
        (~df_str["Product Targeting Expression"].fillna("").astype(str).str.startswith("asin")) &
        (df_str["Orders"] >= 2)
    ]
#==========================STR analysis=========================================
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
#==========================Bulk file processing=========================================
    # Load the bulk file into a DataFrame
    bulk_df_str = bulk_df.copy()
    # Filter the DataFrame for rows where Match Type is in ["Broad", "Phrase", "Exact"]
    filtered_kw_df = bulk_df_str[bulk_df_str["Match Type"].isin(["Broad", "Phrase", "Exact"])]

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
    filtered_pt_df = bulk_df_str[bulk_df_str["Product Targeting Expression"].str.startswith("asin", na=False)]

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
#==========================Deduplication analysis=========================================
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

def build_campaign_rows(deduped_df: pd.DataFrame) -> pd.DataFrame:

    def generate_amazon_kw_campaign_table(asin, keyword, bid):
        campaign_name = f"{asin} KW - Harvest - {keyword} - Exact"
        ad_group_name = campaign_name
        # Set start_date to tomorrow's date
        start_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y%m%d")
        daily_budget = 200
        default_bid = 3
        entity_data = [
            ["Sponsored Products", "Campaign", "Create", campaign_name, "", "", "", "", "", campaign_name, "", start_date, "", "Manual", "enabled", daily_budget, "", "", "", "", "", "", "", "", "Fixed bid", "", "", ""],
            ["Sponsored Products", "Bidding adjustment", "Create", campaign_name, "", "", "", "", "", "", "", "", "", "", "enabled", "", "", "", "", "", "", "", "","", "Fixed bid", "placementTop", 50, ""],
            ["Sponsored Products", "Ad group", "Create", campaign_name, ad_group_name, "", "", "", "", "",ad_group_name, "", "", "", "enabled", "", "", "", default_bid, "", "", "", "", "", "", "", "", ""],
            ["Sponsored Products", "Product ad", "Create", campaign_name, ad_group_name, "", "", "", "", "", "", "", "", "", "enabled", "", "", asin, "", "", "", "", "", "", "", "", "", ""],
            ["Sponsored Products", "Keyword", "Create", campaign_name, ad_group_name, "", "", "", "", "", "", "", "", "", "enabled", "", "", "", "", bid, keyword, "", "", "Exact", "", "", "", ""]
        ]
        
        columns = [
            "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Portfolio ID", "Ad ID", "Keyword ID", "Product Targeting ID", 
            "Campaign Name", "Ad Group Name", "Start Date", "End Date", "Targeting Type", "State", "Daily Budget", "SKU", "ASIN", 
            "Ad Group Default Bid", "Bid", "Keyword Text", "Native Language Keyword", "Native Language Locale", "Match Type", 
            "Bidding Strategy", "Placement", "Percentage", "Product Targeting Expression"
        ]
        
        df = pd.DataFrame(entity_data, columns=columns)
        return df
    def generate_amazon_product_campaign_table(asin, product_asin_target, bid):
        campaign_name = f"{asin} - asin=\" - {product_asin_target} - Harvest"
        ad_group_name = campaign_name
        start_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y%m%d")
        daily_budget = 200
        default_bid = 3
        entity_data = [
            ["Sponsored Products", "Campaign", "Create", campaign_name, "", "", "", "", "", campaign_name, "", start_date, "", "Manual", "enabled", daily_budget, "", "", "", "", "", "", "", "", "Fixed bid", "", "", ""],
            ["Sponsored Products", "Ad group", "Create", campaign_name, ad_group_name, "", "", "", "", "",ad_group_name, "", "", "", "enabled", "", "", "", default_bid, "", "", "", "", "", "", "", "", ""],
            ["Sponsored Products", "Product ad", "Create", campaign_name, ad_group_name, "", "", "", "", "", "", "", "","", "enabled", "", "", asin, "", "", "", "", "", "", "", "", "", ""],
            ["Sponsored Products", "Product targeting", "Create", campaign_name, ad_group_name, "", "", "", "", "", "", "", "","", "enabled", "", "", "", "", bid, "", "", "", "", "", "","", f"asin=\"{product_asin_target}\""]
        ]
        
        columns = [
            "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Portfolio ID", "Ad ID", "Keyword ID", "Product Targeting ID", 
            "Campaign Name", "Ad Group Name", "Start Date", "End Date", "Targeting Type", "State", "Daily Budget", "SKU", "ASIN", 
            "Ad Group Default Bid", "Bid", "Keyword Text", "Native Language Keyword", "Native Language Locale", "Match Type", 
            "Bidding Strategy", "Placement", "Percentage", "Product Targeting Expression"
        ]
        
        df = pd.DataFrame(entity_data, columns=columns)
        return df
    # Filter deduped_df where "KW/PT" equals "KW" and "Exact" equals "doesn't exist"
    kw_filtered_deduped_df = deduped_df[(deduped_df["Type"] == "KW") & (deduped_df["Exact"] == "doesn't exist")]
    pt_filtered_deduped_df = deduped_df[(deduped_df["Type"] == "PT") & (deduped_df["PT"] == "doesn't exist")]

    # Initialize empty DataFrames with correct columns
    columns = [
        "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Portfolio ID", 
        "Ad ID", "Keyword ID", "Product Targeting ID", "Campaign Name", "Ad Group Name", 
        "Start Date", "End Date", "Targeting Type", "State", "Daily Budget", "SKU", 
        "ASIN", "Ad Group Default Bid", "Bid", "Keyword Text", "Native Language Keyword", 
        "Native Language Locale", "Match Type", "Bidding Strategy", "Placement", 
        "Percentage", "Product Targeting Expression"
    ]
    
    campaign_df = pd.DataFrame(columns=columns)
    
    # Only process if we have rows to process
    if not kw_filtered_deduped_df.empty:
        campaign_kw_rows = []
        for _, row in kw_filtered_deduped_df.iterrows():
            asin = row["ASIN"]
            keyword = row["KW/PT"]
            bid = row["CPC"]  # Changed from Bid to CPC
            campaign_kw_rows.append(generate_amazon_kw_campaign_table(asin, keyword, bid))
        
        if campaign_kw_rows:  # Only concatenate if we have rows
            campaign_kw_df = pd.concat(campaign_kw_rows, ignore_index=True)
            campaign_df = pd.concat([campaign_df, campaign_kw_df], ignore_index=True)

    if not pt_filtered_deduped_df.empty:
        campaign_pt_rows = []
        for _, row in pt_filtered_deduped_df.iterrows():
            asin = row["ASIN"]
            product_asin_target = row["KW/PT"]
            bid = row["CPC"]  # Changed from Bid to CPC
            campaign_pt_rows.append(generate_amazon_product_campaign_table(asin, product_asin_target, bid))
        
        if campaign_pt_rows:  # Only concatenate if we have rows
            campaign_pt_df = pd.concat(campaign_pt_rows, ignore_index=True)
            campaign_df = pd.concat([campaign_df, campaign_pt_df], ignore_index=True)
    
    return campaign_df 
