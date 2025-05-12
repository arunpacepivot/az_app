import pandas as pd
import numpy as np

def filter_placement_data(bulk_df: pd.DataFrame) -> pd.DataFrame:
    df_placement = bulk_df[
        (bulk_df["Entity"] == "Bidding Adjustment") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Placement"].isin(["Placement Product Page", "Placement Top", "Placement Rest Of Search", "Placement Amazon Business"]))
    ].copy()
    df_placement["ASIN_Derived"] = df_placement["Campaign Name (Informational only)"].str.split().str[0]
    return df_placement

def calculate_asin_summary(df_placement: pd.DataFrame) -> pd.DataFrame:
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
    return asin_summary

def calculate_rpc(df_placement: pd.DataFrame) -> pd.DataFrame:
    RPC_df = df_placement.copy()
    RPC_df["RPC"] = RPC_df.apply(
        lambda x: x["Sales"] / x["Clicks"] if x["Clicks"] > 0 else 0,
        axis=1
    )
    RPC_df["Ideal Bid"] = 0.0
    RPC_df["Multiplier"] = 0.0
    return RPC_df

def calculate_placement_aggregate_cpc(asin_summary: pd.DataFrame) -> dict:
    return asin_summary.groupby("Placement", observed=True)["CPC"].mean().to_dict()

def calculate_ideal_bid(RPC_df: pd.DataFrame, asin_summary: pd.DataFrame, target_acos: float) -> pd.DataFrame:
    placement_aggregate_cpc = calculate_placement_aggregate_cpc(asin_summary)
    for campaign_name, group in RPC_df.groupby("Campaign Name (Informational only)"):
        group_indices = group.index
        rpc_greater_than_zero = group[group["RPC"] > 0]
        
        if len(rpc_greater_than_zero) == 0:
            RPC_df.loc[group_indices, "Ideal Bid"] = np.nan
        elif len(rpc_greater_than_zero) == 4:
            for idx in group_indices:
                row = RPC_df.loc[idx]
                if row["ACOS"] > target_acos:
                    RPC_df.at[idx, "Ideal Bid"] = row["RPC"] * target_acos
                else:
                    asin_placement_data = asin_summary[
                        (asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & 
                        (asin_summary["Placement"] == row["Placement"])
                    ]
                    if len(asin_placement_data) > 0:
                        asin_cpc = asin_placement_data["CPC"].values[0]
                        if row["ACOS"] < 0.5 * target_acos:
                            multiplier = 1.5
                        elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                            multiplier = 1.25
                        else:
                            multiplier = 1.1
                        RPC_df.at[idx, "Ideal Bid"] = min(asin_cpc * multiplier, row["CPC"] * 1.1)
                    else:
                        RPC_df.at[idx, "Ideal Bid"] = row["CPC"] * 1.1
        elif len(rpc_greater_than_zero) == 1:
            idx = rpc_greater_than_zero.index[0]
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
            reference_placement = RPC_df.at[idx, "Placement"]
            reference_cpc = asin_summary[(asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & (asin_summary["Placement"] == reference_placement)]["CPC"].values
            reference_cpc = reference_cpc[0] if len(reference_cpc) > 0 and not pd.isna(reference_cpc[0]) else placement_aggregate_cpc.get(reference_placement, 5)
            reference_ideal_bid = RPC_df.at[idx, "Ideal Bid"]
            for other_idx in group_indices:
                placement = RPC_df.at[other_idx, "Placement"]
                asin_cpc = asin_summary[(asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & (asin_summary["Placement"] == placement)]["CPC"].values
                asin_cpc = asin_cpc[0] if len(asin_cpc) > 0 and not pd.isna(asin_cpc[0]) else placement_aggregate_cpc.get(placement, 0)
                if other_idx != idx:
                    RPC_df.at[other_idx, "Ideal Bid"] = reference_ideal_bid * (asin_cpc / reference_cpc)
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
        elif len(rpc_greater_than_zero) == 3:
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
        valid_bids = RPC_df.loc[group_indices]
        valid_bids = valid_bids[valid_bids["Ideal Bid"].notna()]
        if not valid_bids.empty:
            min_bid = valid_bids["Ideal Bid"].min()
            if min_bid > 0:
                RPC_df.loc[group_indices, "Multiplier"] = valid_bids["Ideal Bid"].apply(
                    lambda x: (x / min_bid) - 1 if pd.notna(x) else np.nan
                )
            else:
                RPC_df.loc[group_indices, "Multiplier"] = 0
    return RPC_df

def calculate_final_bids(bulk_df: pd.DataFrame, RPC_df: pd.DataFrame, df_placement: pd.DataFrame) -> pd.DataFrame:
    valid_campaigns = df_placement.copy()
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign].copy()
        campaign_rows["ASIN_Derived_bulk"] = campaign_rows["Campaign Name (Informational only)"].str.split().str[0]
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Multiplier"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Multiplier"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Multiplier"].values[0]
        amazon_business_bid = campaign_rows[campaign_rows["Placement"] == "Placement Amazon Business"]["Multiplier"].values[0]
        if top_of_search_bid != 0 or product_pages_bid != 0 or rest_of_search_bid != 0 or amazon_business_bid != 0:
            campaign_id_values = bulk_df[bulk_df["Campaign Name (Informational only)"] == campaign]["Campaign ID"].values
            if len(campaign_id_values) > 0:
                for campaign_id in campaign_id_values:
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Top"), "Percentage"] = min(round(top_of_search_bid * 100, 2), 900)
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Product Page"), "Percentage"] = min(round(product_pages_bid * 100, 2), 900)
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Rest Of Search"), "Percentage"] = min(round(rest_of_search_bid * 100, 2), 900)
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Amazon Business"), "Percentage"] = min(round(amazon_business_bid * 100, 2), 900)
    return valid_campaigns

def create_campaign_bid_df(RPC_df: pd.DataFrame) -> pd.DataFrame:
    campaign_bid_data = []
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign]
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Ideal Bid"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Ideal Bid"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Ideal Bid"].values[0]
        amazon_business_bid = campaign_rows[campaign_rows["Placement"] == "Placement Amazon Business"]["Ideal Bid"].values[0]
        top_of_search_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Multiplier"].values[0]
        product_pages_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Multiplier"].values[0]
        rest_of_search_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Multiplier"].values[0]
        amazon_business_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Amazon Business"]["Multiplier"].values[0]
        if top_of_search_bid != np.nan and product_pages_bid != np.nan and rest_of_search_bid != np.nan and amazon_business_bid != np.nan:
            min_ideal_bid = min(top_of_search_bid, product_pages_bid, rest_of_search_bid, amazon_business_bid)
            campaign_bid_data.append({
                "Campaign Name": campaign,
                "Bid": min_ideal_bid,
                "Multiplier": max(top_of_search_multiplier, product_pages_multiplier, rest_of_search_multiplier, amazon_business_multiplier)
            })
    return pd.DataFrame(campaign_bid_data)

def filter_bulk_df(bulk_df: pd.DataFrame) -> pd.DataFrame:
    filtered_bulk_df = bulk_df[
        (bulk_df["Entity"].isin(["Keyword", "Product Targeting"])) &
        (bulk_df["State"] == "enabled") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Ad Group State (Informational only)"] == "enabled")
    ].copy()
    filtered_bulk_df["ASIN"] = filtered_bulk_df["Campaign Name (Informational only)"].fillna("").astype(str).apply(
        lambda x: x.split()[0] if x.strip() else None
    )
    return filtered_bulk_df

def calculate_bulk_asin_summary(filtered_bulk_df: pd.DataFrame) -> pd.DataFrame:
    bulk_asin_summary = filtered_bulk_df.groupby("ASIN").agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum"
    }).reset_index()
    bulk_asin_summary["AOV"] = bulk_asin_summary["Sales"] / bulk_asin_summary["Orders"]
    bulk_asin_summary["Click to Conversion"] = bulk_asin_summary["Clicks"] / bulk_asin_summary["Orders"]
    bulk_asin_summary["CPC"] = bulk_asin_summary["Spend"] / bulk_asin_summary["Clicks"]
    return bulk_asin_summary

def fill_new_bid(filtered_bulk_df: pd.DataFrame, campaign_bid_df: pd.DataFrame, bulk_asin_summary: pd.DataFrame, target_acos: float) -> pd.DataFrame:
    filtered_bulk_df["New bid"] = pd.NA
    for _, row in campaign_bid_df.iterrows():
        campaign_name = row["Campaign Name"]
        bid_value = row["Bid"]
        filtered_bulk_df.loc[filtered_bulk_df["Campaign Name (Informational only)"] == campaign_name, "New bid"] = bid_value
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna()].iterrows():
        if row["Clicks"] == 0:
            campaign_name = row["Campaign Name (Informational only)"]
            if pd.isna(campaign_name) or not isinstance(campaign_name, str):
                continue
            asin = campaign_name.split()[0]
            asin_cpc = bulk_asin_summary[bulk_asin_summary["ASIN"] == asin]["CPC"].values[0]
            new_bid = min(row["Bid"] * 1.1, asin_cpc)
            filtered_bulk_df.at[row.name, "New bid"] = new_bid
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna() & (filtered_bulk_df["Clicks"] > 0)].iterrows():
        if row["Orders"] == 0:
            campaign_name = row["Campaign Name (Informational only)"]
            if pd.isna(campaign_name) or not isinstance(campaign_name, str):
                continue
            asin = campaign_name.split()[0]
            asin_matches = bulk_asin_summary[bulk_asin_summary["ASIN"] == asin]
            if asin_matches.empty:
                continue
            click_to_conversion = asin_matches["Click to Conversion"].values[0]
            aov = asin_matches["AOV"].values[0]
            new_bid = (aov * target_acos) / (row["Clicks"] + click_to_conversion)
            if new_bid > row["Bid"]:
                new_bid = row["Bid"]
            filtered_bulk_df.at[row.name, "New bid"] = new_bid
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna()].iterrows():
        if row["ACOS"] > target_acos:
            new_bid = row["CPC"] * (target_acos / row["ACOS"])
        else:
            campaign_name = row["Campaign Name (Informational only)"]
            if pd.isna(campaign_name) or not isinstance(campaign_name, str):
                continue
            asin = campaign_name.split()[0]
            asin_cpc = bulk_asin_summary[bulk_asin_summary["ASIN"] == asin]["CPC"].values[0]
            new_bid = round(min(row["CPC"] * 1.1, asin_cpc), 2)
            if new_bid < 1:
                new_bid = 1
        filtered_bulk_df.at[row.name, "New bid"] = new_bid
    return filtered_bulk_df

def adjust_bid(bid):
    new_bid = max(bid, 1.00)
    return round(new_bid, 2)

def placement_optimize_sk_ab_net(bulk_df: pd.DataFrame, target_acos: float) -> pd.DataFrame:
    df_placement = filter_placement_data(bulk_df)
    if df_placement.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    asin_summary = calculate_asin_summary(df_placement)
    RPC_df = calculate_rpc(df_placement)
    RPC_df = calculate_ideal_bid(RPC_df, asin_summary, target_acos)
    valid_campaigns_sk = calculate_final_bids(bulk_df, RPC_df, df_placement)
    campaign_bid_df = create_campaign_bid_df(RPC_df)
    filtered_bulk_df = filter_bulk_df(bulk_df)
    bulk_asin_summary = calculate_bulk_asin_summary(filtered_bulk_df)
    filtered_bulk_df = fill_new_bid(filtered_bulk_df, campaign_bid_df, bulk_asin_summary, target_acos)
    if filtered_bulk_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    filtered_bulk_df["New bid"] = filtered_bulk_df["New bid"].apply(adjust_bid)
    return filtered_bulk_df, valid_campaigns_sk, RPC_df, asin_summary
    

