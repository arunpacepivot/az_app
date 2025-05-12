import pandas as pd
import numpy as np

#==========================Filter placement data=========================================
def placement_optimize_sk_ab_net( bulk_df: pd.DataFrame, target_acos: float ) -> pd.DataFrame:
    # Filter bulk_df for the required conditions to create df_placement
    df_placement = bulk_df[
        (bulk_df["Entity"] == "Bidding Adjustment") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Placement"].isin(["Placement Product Page", "Placement Top", "Placement Rest Of Search"]))
    ].copy() 

#Derive ASIN from campaign name
    df_placement["ASIN_Derived"] = df_placement["Campaign Name (Informational only)"].str.split().str[0]
    if df_placement.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
#Grouped Summary by ASIN & Placement    
    # Grouped summary of ASIN and Placement
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

#Caluclate RPC for each placement
    # Calculate `RPC` and create new DataFrame
    RPC_df = df_placement.copy()

    # Extract ASIN (first word of Campaign Name) for new DataFrame
    RPC_df["RPC"] = RPC_df.apply(
        lambda x: x["Sales"] / x["Clicks"] if x["Clicks"] > 0 else 0,
        axis=1
    )

    # Initialize ideal bid and multiplier columns
    RPC_df["Ideal Bid"] = 0.0
    RPC_df["Multiplier"] = 0.0

#Calculate aggregate CPC for each placement as a fallback - Move this up before any case handling
    placement_aggregate_cpc = asin_summary.groupby("Placement", observed=True)["CPC"].mean().to_dict()

#Ideal Bid Calculation
    # Iterate over each unique Campaign Name to apply the logic for Ideal Bid calculation
    for campaign_name, group in RPC_df.groupby("Campaign Name (Informational only)"):
        group_indices = group.index
        rpc_greater_than_zero = group[group["RPC"] > 0]
        
        # Case: All three rows have RPC == 0
        if len(rpc_greater_than_zero) == 0:
            RPC_df.loc[group_indices, "Ideal Bid"] = np.nan

        # Case 1: All three placements have RPC > 0
        elif len(rpc_greater_than_zero) == 3:
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
                # Calculate aggregate CPC for each placement as a fallback
                placement_aggregate_cpc = asin_summary.groupby("Placement", observed=True)["CPC"].mean().to_dict()
                    
        # Case 2: Only one placement has RPC > 0
        elif len(rpc_greater_than_zero) == 1:
            idx = rpc_greater_than_zero.index[0]
            row = RPC_df.loc[idx]
            
            if row["ACOS"] > target_acos:
                RPC_df.at[idx, "Ideal Bid"] = row["RPC"] * target_acos
            else:
                # Attempt to get CPC for the specific ASIN-placement, fall back to placement aggregate CPC if missing
                asin_cpc = asin_summary[(asin_summary["ASIN_Derived"] == row["ASIN_Derived"]) & (asin_summary["Placement"] == row["Placement"])]["CPC"].values

                asin_cpc = asin_cpc[0] if len(asin_cpc) > 0 and not pd.isna(asin_cpc[0]) else placement_aggregate_cpc.get(row["Placement"], 0)

                if row["ACOS"] < 0.5 * target_acos:
                    multiplier = 1.5
                elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                    multiplier = 1.25
                else:
                    multiplier = 1.1

                RPC_df.at[idx, "Ideal Bid"] = min(asin_cpc*multiplier, row["CPC"]*1.1)

            # Calculate bids for other placements based on ASIN CPC ratio
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

        # Case 3: Two placements have RPC > 0
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
                    RPC_df.at[idx, "Ideal Bid"] = min(asin_cpc*multiplier, row["CPC"]*1.1)

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
                    
                     

     #================multiplier calculation=================
        # Calculate Multiplier for each row
        valid_bids = RPC_df.loc[group_indices]
        valid_bids = valid_bids[valid_bids["Ideal Bid"].notna()]  # Use notna() instead of != np.nan
        if not valid_bids.empty:
            min_bid = valid_bids["Ideal Bid"].min()
            if min_bid > 0:  # Only calculate multiplier if min_bid is greater than 0
                RPC_df.loc[group_indices, "Multiplier"] = valid_bids["Ideal Bid"].apply(
                    lambda x: (x / min_bid) - 1 if pd.notna(x) else np.nan
                )
            else:
                RPC_df.loc[group_indices, "Multiplier"] = 0  # Set multiplier to 0 if min_bid is 0
    
    #================final bid calculation=================
    # Load the bulk file into a DataFrame
    bulk_df = bulk_df

    valid_campaigns = df_placement.copy()
    # Iterate over each unique campaign in bid_df
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        # Filter the rows for the current campaign
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign].copy()
        campaign_rows["ASIN_Derived_bulk"] = campaign_rows["Campaign Name (Informational only)"].str.split().str[0]
        # Extract the ideal bids for each placement
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Multiplier"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Multiplier"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Multiplier"].values[0]
            

        # Check if none of the three ideal bids are not 0
        if top_of_search_bid != 0 or product_pages_bid != 0 or rest_of_search_bid != 0 :
            campaign_id_values = bulk_df[bulk_df["Campaign Name (Informational only)"] == campaign]["Campaign ID"].values
            if len(campaign_id_values) > 0:
                for campaign_id in campaign_id_values:
                    # Update the existing valid_campaigns DataFrame
                    
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Top"), "Percentage"] = min(round(top_of_search_bid * 100, 2), 900)
                    
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Product Page"), "Percentage"] = min(round(product_pages_bid * 100, 2), 900)

                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Rest Of Search"), "Percentage"] = min(round(rest_of_search_bid * 100, 2), 900)

                        

    # Create the valid_campaigns DataFrame from the valid_campaigns_data
    valid_campaigns_sk = valid_campaigns.copy()
        
        # Initialize a list to store the rows for the new DataFrame
    campaign_bid_data = []

    # Iterate over each unique campaign in valid_campaigns
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        # Filter the rows for the current campaign
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign]

        # Extract the ideal bids for each placement
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Ideal Bid"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Ideal Bid"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Ideal Bid"].values[0]

        #Extract the multiplier for each placement
        top_of_search_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Multiplier"].values[0]
        product_pages_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Multiplier"].values[0]
        rest_of_search_multiplier = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Multiplier"].values[0]

        # Check if all three ideal bids are not 0
        if top_of_search_bid != np.nan and product_pages_bid != np.nan and rest_of_search_bid != np.nan:
            # Find the minimum ideal bid
            min_ideal_bid = min(top_of_search_bid, product_pages_bid, rest_of_search_bid)

            # Append the row to campaign_bid_data
            campaign_bid_data.append({
                "Campaign Name": campaign,
                "Bid": min_ideal_bid,
                "Multiplier": max(top_of_search_multiplier, product_pages_multiplier, rest_of_search_multiplier)
            })
            
    # Convert campaign_bid_data to DataFrame before returning
    campaign_bid_df = pd.DataFrame(campaign_bid_data)
    
    # Filter the DataFrame for rows where Entity is "Keyword" or "Product Targeting"
    filtered_bulk_df = bulk_df[
        (bulk_df["Entity"].isin(["Keyword", "Product Targeting"])) &
        (bulk_df["State"] == "enabled") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Ad Group State (Informational only)"] == "enabled")
    ].copy()  # Create explicit copy

    # Now modify the copy
    filtered_bulk_df["ASIN"] = filtered_bulk_df["Campaign Name (Informational only)"].fillna("").astype(str).apply(
        lambda x: x.split()[0] if x.strip() else None
    )

    # Grouped summary of ASIN
    bulk_asin_summary = filtered_bulk_df.groupby("ASIN").agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum"
    }).reset_index()

    # Calculate additional metrics
    bulk_asin_summary["AOV"] = bulk_asin_summary["Sales"] / bulk_asin_summary["Orders"]
    bulk_asin_summary["Click to Conversion"] = bulk_asin_summary["Clicks"] / bulk_asin_summary["Orders"]
    bulk_asin_summary["CPC"] = bulk_asin_summary["Spend"] / bulk_asin_summary["Clicks"]
    # Create a new column "New bid" in filtered_bulk_df and initialize with None
    filtered_bulk_df["New bid"] = pd.NA  # Using pd.NA instead of None for better pandas compatibility
    
    # fill new bid with campaign bid
    for _, row in campaign_bid_df.iterrows():
        campaign_name = row["Campaign Name"]
        bid_value = row["Bid"]

        # Update the "New bid" column in filtered_bulk_df where the campaign name matches
        filtered_bulk_df.loc[filtered_bulk_df["Campaign Name (Informational only)"] == campaign_name, "New bid"] = bid_value
    # fill new bid with CPC * 1.1 if clicks are 0
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna()].iterrows():
        # Check if clicks are 0
        if row["Clicks"] == 0:
            # Extract the ASIN from the first word of the campaign name
            campaign_name = row["Campaign Name (Informational only)"]
            # Skip if campaign_name is NaN or not a string
            if pd.isna(campaign_name) or not isinstance(campaign_name, str):
                continue
                
            asin = campaign_name.split()[0]
            # Find the CPC for the ASIN from bulk_asin_summary
            asin_cpc = bulk_asin_summary[bulk_asin_summary["ASIN"] == asin]["CPC"].values[0]
            # Calculate the new bid as the minimum of row CPC * 1.1 and the CPC derived from bulk_asin_summary
            new_bid = min(row["Bid"] * 1.1, asin_cpc)
            # Update the "New bid" column in filtered_bulk_df
            filtered_bulk_df.at[row.name, "New bid"] = new_bid
    # fill new bid with AOV * target_acos / (row clicks + click to conversion) if clicks are greater than 0 and orders are 0
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna() & (filtered_bulk_df["Clicks"] > 0)].iterrows():
        # Check if 14 Day Total Orders is 0
        if row["Orders"] == 0:
            # Extract the ASIN from the first word of the campaign name
            campaign_name = row["Campaign Name (Informational only)"]
            
            # Skip if campaign_name is NaN or not a string
            if pd.isna(campaign_name) or not isinstance(campaign_name, str):
                continue
                
            asin = campaign_name.split()[0]
            # Get the Click to Conversion and AOV metrics from bulk_asin_summary
            asin_matches = bulk_asin_summary[bulk_asin_summary["ASIN"] == asin]
            if asin_matches.empty:
                continue
                
            click_to_conversion = asin_matches["Click to Conversion"].values[0]
            aov = asin_matches["AOV"].values[0]
            # Calculate the new bid as AOV * target_acos / (row clicks + click to conversion)
            new_bid = (aov * target_acos) / (row["Clicks"] + click_to_conversion)
            if new_bid > row["Bid"]:
                new_bid = row["Bid"]
            else:
                new_bid = new_bid
            # Update the "New bid" column in filtered_bulk_df
            filtered_bulk_df.at[row.name, "New bid"] = new_bid
    # fill new bid with CPC * (target ACOS / row ACOS) if ACOS is greater than target ACOS
    for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna()].iterrows():
        # Check if ACOS is greater than target ACOS
        if row["ACOS"] > target_acos:
            # Calculate the new bid as row CPC * (target ACOS / row ACOS)
            new_bid = row["CPC"] * (target_acos / row["ACOS"])
        else:
            # Extract the ASIN from the first word of the campaign name
            campaign_name = row["Campaign Name (Informational only)"]
            # Skip if campaign_name is NaN or not a string
            if pd.isna(campaign_name) or not isinstance(campaign_name, str):
                continue
                
            asin = campaign_name.split()[0]
            # Find the CPC for the ASIN from bulk_asin_summary
            asin_cpc = bulk_asin_summary[bulk_asin_summary["ASIN"] == asin]["CPC"].values[0]
            # Calculate the new bid as the minimum of row CPC * 1.1 and the CPC derived from bulk_asin_summary
            new_bid = round(min(row["CPC"] * 1.1, asin_cpc), 2)
            if new_bid < 1:
                new_bid = 1
        
        # Update the "New bid" column in filtered_bulk_df
        filtered_bulk_df.at[row.name, "New bid"] = new_bid
    if filtered_bulk_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame() 
    # Create the placement_df DataFrame from placement_data

    def adjust_bid(bid):
            new_bid = max(bid, 1.00)
            return round(new_bid, 2)
    filtered_bulk_df["New bid"] = filtered_bulk_df["New bid"].apply(adjust_bid)
   
    amazon_business_df = bulk_df[bulk_df["Placement"] == "Placement Amazon Business"].copy()

    # Filter amazon_business_df for rows where "Campaign State (Informational only)" is "enabled"
    amazon_business_df = amazon_business_df[amazon_business_df["Campaign State (Informational only)"] == "enabled"]
    # Iterate over each row in amazon_business_df
    for idx, row in amazon_business_df.iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        
        # Skip if campaign_name is NaN or not a string
        if pd.isna(campaign_name) or not isinstance(campaign_name, str):
            continue
        
        # Get the corresponding data from campaign_bid_df
        campaign_data = campaign_bid_df[campaign_bid_df["Campaign Name"] == campaign_name]
        
        if campaign_data.empty:
            continue
        
        # Get the multiplier from campaign_data
        multiplier = campaign_data["Multiplier"].values[0]
        
        # Set the multiplier in the Placement column
        amazon_business_df.at[idx, "Percentage"] = multiplier*100
    # Drop the "Multiplier" column from amazon_business_df
    if "Multiplier" in amazon_business_df.columns:
        amazon_business_df = amazon_business_df.drop(columns=["Multiplier"])
    
    # Append all rows of amazon_business_df below the rows of filtered_bulk_df
    combined_df = pd.concat([filtered_bulk_df, amazon_business_df], ignore_index=True)

    






    return combined_df, valid_campaigns_sk, RPC_df, asin_summary
    

