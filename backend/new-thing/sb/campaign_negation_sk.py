from typing import List
import pandas as pd

def campaign_negation_sk(bulk_df, str_df, target_acos):
    bulk_df = bulk_df.copy()
    str_df = str_df.copy()

     # Grouped summary of ASIN and Placement
    str_summary = str_df.groupby(["ASIN derived"]).agg({
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

    str_df = str_df[str_df["Sales"] == 0]
    
    filtered_rows = []
    for _, row in str_df.iterrows():
        asin_derived = row["ASIN derived"]
        spend = row["Spend"]
        if asin_derived in str_summary["ASIN derived"].values:
            aov = str_summary[str_summary["ASIN derived"] == asin_derived]["AOV"].values[0]
            max_spend = aov * target_acos 
            if spend > max_spend:
                filtered_rows.append(row)
    
    if filtered_rows:
        filtered_df = pd.DataFrame(filtered_rows)
    else:
        filtered_df = pd.DataFrame()  # Create an empty DataFrame if filtered_rows is empty
    # Add a column "Max Spend" to the filtered DataFrame and populate it with the calculated max_spend values
    if not filtered_df.empty:
        filtered_df["Max Spend"] = filtered_df.apply(
            lambda row: str_summary[str_summary["ASIN derived"] == row["ASIN derived"]]["AOV"].values[0] * target_acos 
        if row["ASIN derived"] in str_summary["ASIN derived"].values else 0, 
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
    
        # Check if the customer search term starts with 'b0' (case insensitive)
        if customer_search_term.lower().startswith("b0"):
            pt_rows.append({
                "Campaign ID": None,  # Placeholder, will be filled later
                "Campaign Name (Informational only)": campaign_name,
                "Customer Search Term": customer_search_term
            })
        else:
            kw_rows.append({
                "Campaign ID": None,  # Placeholder, will be filled later
                "Campaign Name (Informational only)": campaign_name,
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
    
    pt_df_sk=pd.DataFrame()
    kw_df_sk=pd.DataFrame()
    # Load df_bulk_report to get Campaign ID and Ad Group ID
    df_bulk_report = bulk_df

    
    # Create a multi-index map for Campaign Name and Ad Group Name to their respective IDs
    campaign_ad_group_id_map = (
        df_bulk_report
        .groupby(["Campaign Name (Informational only)"])
        .apply(lambda x: x[["Campaign ID"]].iloc[0])
        .to_dict(orient="index")
    )

    if "Campaign Name (Informational only)" not in pt_df.columns:
        print("Campaign Name (Informational only) not found in pt_df")

    else:
            # Start of Selection
            # Map "Campaign ID" and "Ad Group ID" using campaign_ad_group_id_map
            pt_df["Campaign ID"] = pt_df.apply(
                lambda row: campaign_ad_group_id_map.get(
                    (row["Campaign Name (Informational only)"]), {}
                ).get("Campaign ID"),
                axis=1
            )
            pt_df["Campaign ID"] = pt_df["Campaign ID"].apply(lambda x: f"{int(x):.0f}")
            pt_df = pt_df[["Campaign ID", "Campaign Name (Informational only)", "Customer Search Term"]]
    
    if "Campaign Name (Informational only)" not in kw_df.columns:
        print("Campaign Name (Informational only) not found in kw_df")
    else:
        kw_df["Campaign ID"] = kw_df.apply(
            lambda row: campaign_ad_group_id_map.get(
                (row["Campaign Name (Informational only)"]), {}
            ).get("Campaign ID"),
            axis=1
        )
        kw_df["Campaign ID"] = kw_df["Campaign ID"].apply(lambda x: f"{int(x):.0f}")
        kw_df = kw_df[["Campaign ID", "Campaign Name (Informational only)", "Customer Search Term"]]
    pt_df_sk = pt_df
    kw_df_sk = kw_df
    return pt_df_sk, kw_df_sk
