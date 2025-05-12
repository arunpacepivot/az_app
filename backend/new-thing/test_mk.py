import pandas as pd
import numpy as np

def calculate_summary(df_placement):
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
    return summary

def calculate_rpc(df_placement):
    RPC_df = df_placement.copy()
    RPC_df["RPC"] = RPC_df.apply(
        lambda x: x["Sales"] / x["Clicks"] if x["Clicks"] > 0 else 0,
        axis=1
    )
    return RPC_df

def initialize_bid_and_multiplier(RPC_df):
    RPC_df["Ideal Bid"] = 0.0
    RPC_df["Multiplier"] = 0.0
    return RPC_df

def calculate_ideal_bid(RPC_df, summary, target_acos):
    placement_aggregate_cpc = summary.groupby("Placement", observed=True)["CPC"].mean().to_dict()

    for campaign_name, group in RPC_df.groupby("Campaign Name (Informational only)"):
        group_indices = group.index
        rpc_greater_than_zero = group[group["RPC"] > 0]
        
        if len(rpc_greater_than_zero) == 0:
            RPC_df.loc[group_indices, "Ideal Bid"] = np.nan

        elif len(rpc_greater_than_zero) == 3:
            for idx in group_indices:
                row = RPC_df.loc[idx]
                if row["ACOS"] > target_acos:
                    RPC_df.at[idx, "Ideal Bid"] = row["RPC"] * target_acos
                else:
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
                        RPC_df.at[idx, "Ideal Bid"] = min(placement_cpc*multiplier, row["CPC"]*1.1)
                    else:
                        RPC_df.at[idx, "Ideal Bid"] = row["CPC"] * 1.1
        elif len(rpc_greater_than_zero) == 2:
            idx = rpc_greater_than_zero.index[0]
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
        elif len(rpc_greater_than_zero) == 1:
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
                    RPC_df.at[idx, "Ideal Bid"] =  min(placement_cpc * multiplier, row["CPC"] * multiplier)     

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
    return RPC_df

def calculate_multiplier(RPC_df):
    for campaign_name, group in RPC_df.groupby("Campaign Name (Informational only)"):
        group_indices = group.index
        valid_bids = RPC_df.loc[group_indices]
        valid_bids = valid_bids[valid_bids["Ideal Bid"].notna() & (valid_bids["Ideal Bid"] > 0)]
        
        if not valid_bids.empty:
            min_bid = valid_bids["Ideal Bid"].min()
            if min_bid > 0:
                RPC_df.loc[group_indices, "Multiplier"] = valid_bids["Ideal Bid"].apply(
                    lambda x: (x / min_bid) - 1 if pd.notna(x) and x > 0 else 0
                )
            else:
                RPC_df.loc[group_indices, "Multiplier"] = 0
        else:
            RPC_df.loc[group_indices, "Multiplier"] = 0
    return RPC_df

def update_valid_campaigns(RPC_df, bulk_df, df_placement):
    valid_campaigns = df_placement.copy()
    
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign].copy()
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Multiplier"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Multiplier"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Multiplier"].values[0]
        
        if top_of_search_bid != 0 or product_pages_bid != 0 or rest_of_search_bid != 0:
            campaign_id_values = bulk_df[bulk_df["Campaign Name (Informational only)"] == campaign]["Campaign ID"].values
            if len(campaign_id_values) > 0:
                for campaign_id in campaign_id_values:
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Top"), "Percentage"] = min(round(top_of_search_bid * 100, 2), 900)
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Product Page"), "Percentage"] = min(round(product_pages_bid * 100, 2), 900)
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Rest Of Search"), "Percentage"] = min(round(rest_of_search_bid * 100, 2), 900)
    return valid_campaigns

def create_campaign_bid_df(RPC_df):
    campaign_bid_data = []

    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign].copy()
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Ideal Bid"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Ideal Bid"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Ideal Bid"].values[0]
        top_of_search_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Multiplier"].values[0]
        product_pages_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Multiplier"].values[0]
        rest_of_search_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Multiplier"].values[0]

        if top_of_search_bid != np.nan and product_pages_bid != np.nan and rest_of_search_bid != np.nan:
            min_ideal_bid = min(top_of_search_bid, product_pages_bid, rest_of_search_bid)
            campaign_bid_data.append({
                "Campaign Name (Informational only)": campaign,
                "Bid": min_ideal_bid,
                "Multiplier": max(top_of_search_multiplier, product_pages_multiplier, rest_of_search_multiplier)
            })
    campaign_bid_df = pd.DataFrame(campaign_bid_data)
    return campaign_bid_df

def update_filtered_bulk_df(filtered_bulk_df: pd.DataFrame, campaign_bid_df: pd.DataFrame, target_acos: float, bulk_summary: pd.DataFrame) -> pd.DataFrame:
    # Create a copy to avoid SettingWithCopyWarning
    filtered_bulk_df = filtered_bulk_df.copy()   
    for _, row in campaign_bid_df.iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        multiple = row["Multiplier"]
        
        filtered_bulk_df.loc[filtered_bulk_df["Campaign Name (Informational only)"] == campaign_name, "New bid"] = ((filtered_bulk_df.apply(
            lambda row: row["RPC"] if row["Campaign Name (Informational only)"] == campaign_name else row["New bid"],
            axis=1
        ))*target_acos)/(1+multiple)
        filtered_bulk_df["Remark"] = "Placement Optimized"
    # Iterate over each row in filtered_bulk_df where "New bid" is not NaN
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].notna()].iterrows():
        # Check if the new bid is greater than 1.2 times the original bid
        Bids_multiplier = 1.0
        if row["ACOS"] < 0.5 * target_acos:
            Bids_multiplier = 1.5
        elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
            Bids_multiplier = 1.25
        else:
            Bids_multiplier = 1.1
        if row["New bid"] > Bids_multiplier * row["Bid"]:
            # Set the new bid to 1.2 times the original bid
            filtered_bulk_df.at[row.name, "New bid"] = Bids_multiplier * row["Bid"]
    
    for index, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna() | (filtered_bulk_df["New bid"] == 0)].iterrows():

        campaign_name = row["Campaign Name (Informational only)"]
        
        # Skip if campaign_name is NaN or not a string
        if pd.isna(campaign_name) or not isinstance(campaign_name, str):
            continue

        # Get campaign data
        campaign_data = filtered_bulk_df[filtered_bulk_df["Campaign Name (Informational only)"] == campaign_name]
        campaign_summary = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign_name]
        
        
        # Process each row in the campaign
        for idx in campaign_data.index:
            row = campaign_data.loc[idx]
            
            if row["Clicks"] == 0:
                filtered_bulk_df.loc[idx, "New bid"] = row["Bid"] * 1.1

            elif row["Clicks"] > 0 and row["Orders"] > 0 and row["ACOS"] > target_acos:
                filtered_bulk_df.loc[idx, "New bid"] = (row["Sales"] / row["Clicks"]) * target_acos

            elif row["Clicks"] > 0 and row["Orders"] > 0 and row["ACOS"] <= target_acos:
                campaign_cpc = campaign_summary["CPC"].iloc[0] if not campaign_summary.empty else 0.0
                if row["ACOS"] < 0.5 * target_acos:
                    multiplier = 1.5
                elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                    multiplier = 1.25
                else:
                    multiplier = 1.1

                filtered_bulk_df.loc[idx, "New bid"] = min(multiplier * row["CPC"], campaign_cpc*multiplier)
                filtered_bulk_df.loc[idx, "Remark"] = "0 clicks Optimized"
            elif row["Clicks"] > 0 and row["Orders"] == 0:
                campaign_cpc = campaign_summary["CPC"].iloc[0] if not campaign_summary.empty else 0.0
                campaign_AOV = campaign_summary["AOV"].iloc[0] if not campaign_summary.empty else 0.0
                campaign_Clicks_to_conversion = campaign_summary["Click to Conversion"].iloc[0] if not campaign_summary.empty else 1.0
                bid = row["Bid"] if not pd.isna(row["Bid"]) and row["Bid"] > 0 else row["Ad Group Default Bid (Informational only)"]

                new_bid = (campaign_AOV * target_acos) / (row["Clicks"] + campaign_Clicks_to_conversion)
                if new_bid < 1:
                    new_bid = 5
                
                if new_bid > bid:
                    new_bid = bid

                filtered_bulk_df.loc[idx, "New bid"] = new_bid
                filtered_bulk_df.loc[idx, "Remark"] = "0 orders Optimized"
            else:
                filtered_bulk_df.loc[idx, "New bid"] = 5.0
                filtered_bulk_df.loc[idx, "Remark"] = "Default bid optimised"
    
    

    return filtered_bulk_df

def placement_optimize_mk_ab_net(bulk_df: pd.DataFrame, target_acos: float) -> pd.DataFrame:
    df_placement = bulk_df[
        (bulk_df["Entity"] == "Bidding Adjustment") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Placement"].isin(["Placement Product Page", "Placement Top", "Placement Rest Of Search"]))
    ].copy() 
    
    if df_placement.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    summary = calculate_summary(df_placement)
    RPC_df = calculate_rpc(df_placement)
    RPC_df = initialize_bid_and_multiplier(RPC_df)
    RPC_df = calculate_ideal_bid(RPC_df, summary, target_acos)
    RPC_df = calculate_multiplier(RPC_df)
    valid_campaigns = update_valid_campaigns(RPC_df, bulk_df, df_placement)
    campaign_bid_df = create_campaign_bid_df(RPC_df)

    filtered_bulk_df = bulk_df[
        (bulk_df["Entity"].isin(["Keyword", "Product Targeting"])) &
        (bulk_df["State"] == "enabled") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Ad Group State (Informational only)"] == "enabled")
    ].copy()

    filtered_bulk_df["Bid"] = filtered_bulk_df["Bid"].astype(float)
    filtered_bulk_df["key"] = filtered_bulk_df.apply(
        lambda row: row["Keyword Text"] if pd.notna(row["Keyword Text"]) and row["Keyword Text"].strip() != "" else row["Product Targeting Expression"],
        axis=1
    )
    filtered_bulk_df["RPC"] = filtered_bulk_df.apply(
        lambda row: row["Sales"] / row["Clicks"] if row["Clicks"] > 0 else 0,
        axis=1
    )

    print(filtered_bulk_df.columns)

    bulk_summary = filtered_bulk_df.groupby("Campaign Name (Informational only)").agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum"
    }).reset_index()

    bulk_summary["AOV"] = bulk_summary["Sales"] / bulk_summary["Orders"]
    bulk_summary["Click to Conversion"] = bulk_summary["Clicks"] / bulk_summary["Orders"]
    bulk_summary["CPC"] = bulk_summary["Spend"] / bulk_summary["Clicks"]
    bulk_summary["RPC"] = bulk_summary["Sales"] / bulk_summary["Clicks"]

    # Fill NaN values with appropriate defaults
    bulk_summary["AOV"] = bulk_summary["AOV"].fillna(0.0)
    bulk_summary["Click to Conversion"] = bulk_summary["Click to Conversion"].fillna(1.0)
    bulk_summary["CPC"] = bulk_summary["CPC"].fillna(0.0)

    # Initialize the ideal bid column
    filtered_bulk_df["New bid"] = pd.NA

    filtered_bulk_df = update_filtered_bulk_df(filtered_bulk_df, campaign_bid_df, target_acos,bulk_summary)
    

    # Drop the column named "key" from filtered_bulk_df
    if "key" in filtered_bulk_df.columns:
        filtered_bulk_df = filtered_bulk_df.drop(columns=["key"])
  

    filtered_bulk_df_mk = filtered_bulk_df
    RPC_df_mk = RPC_df
    bulk_summary_mk = bulk_summary
    valid_campaigns_mk = valid_campaigns
    return filtered_bulk_df_mk, RPC_df_mk, bulk_summary_mk, valid_campaigns_mk
