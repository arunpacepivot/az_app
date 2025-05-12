import pandas as pd
import numpy as np

def placement_optimize_mk_ab_net( bulk_df: pd.DataFrame, target_acos: float ) -> pd.DataFrame:
    # Load and create `df` and `processed_df` from previous steps
    df_placement = bulk_df[
        (bulk_df["Entity"] == "Bidding Adjustment") &
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["Placement"].isin(["Placement Product Page", "Placement Top", "Placement Rest Of Search"]))
    ].copy() 
    
    if df_placement.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    # Grouped summary of ASIN and Placement
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

    # Calculate aggregate CPC for each placement as a fallback
    placement_aggregate_cpc = summary.groupby("Placement", observed=True)["CPC"].mean().to_dict()

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

        # Case 2: Only one placement has RPC > 0
        elif len(rpc_greater_than_zero) == 2:
            idx = rpc_greater_than_zero.index[0]
            row = RPC_df.loc[idx]
            if row["ACOS"] > target_acos:
                RPC_df.at[idx, "Ideal Bid"] = row["RPC"] * target_acos
            else:
                # Attempt to get CPC for the specific placement, fall back to placement aggregate CPC if missing
                placement_cpc = summary[(summary["Placement"] == row["Placement"])]["CPC"].values
                placement_cpc = placement_cpc[0] if len(placement_cpc) > 0 and not pd.isna(placement_cpc[0]) else placement_aggregate_cpc.get(row["Placement"], 0)

                if row["ACOS"] < 0.5 * target_acos:
                    multiplier = 1.5
                elif 0.5 * target_acos <= row["ACOS"] < 0.75 * target_acos:
                    multiplier = 1.25
                else:
                    multiplier = 1.1
                RPC_df.at[idx, "Ideal Bid"] = min(placement_cpc * multiplier, row["CPC"] * 1.1)
                

            # Calculate bids for other placements based on ASIN CPC ratio
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

        # Case 3: Two placements have RPC > 0
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
                    RPC_df.at[idx, "Ideal Bid"] =  min(placement_cpc * multiplier, row["CPC"] * 1.1)     

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

        # Calculate Multiplier for each row
        valid_bids = RPC_df.loc[group_indices]
        # Filter out NaN values and zeros
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

     # Load the bulk file into a DataFrame
    bulk_df = bulk_df

    # Initialize valid_campaigns DataFrame outside the loop
    valid_campaigns = df_placement.copy()
    
    # Iterate over each unique campaign in bid_df
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        # Filter the rows for the current campaign
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign].copy()
        # campaign_rows.loc[:, "ASIN_Derived_bulk"] = campaign_rows["Campaign Name (Informational only)"].str.split().str[0]

        # Extract the ideal bids for each placement
        top_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Top"]["Multiplier"].values[0]
        product_pages_bid = campaign_rows[campaign_rows["Placement"] == "Placement Product Page"]["Multiplier"].values[0]
        rest_of_search_bid = campaign_rows[campaign_rows["Placement"] == "Placement Rest Of Search"]["Multiplier"].values[0]
        
        
        # Check if all three ideal bids are not 0
        if top_of_search_bid != 0 or product_pages_bid != 0 or rest_of_search_bid != 0 :
            campaign_id_values = bulk_df[bulk_df["Campaign Name (Informational only)"] == campaign]["Campaign ID"].values
            if len(campaign_id_values) > 0:
                for campaign_id in campaign_id_values:
                    # Update the existing valid_campaigns DataFrame
                    
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Top"), "Percentage"] = min(round(top_of_search_bid * 100, 2), 900)
                    
                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Product Page"), "Percentage"] = min(round(product_pages_bid * 100, 2), 900)

                    valid_campaigns.loc[(valid_campaigns["Campaign Name (Informational only)"] == campaign) & (valid_campaigns["Placement"] == "Placement Rest Of Search"), "Percentage"] = min(round(rest_of_search_bid * 100, 2), 900)

   
    valid_campaigns_mk = valid_campaigns.copy()
        # Initialize a list to store the rows for the new DataFrame
    campaign_bid_data = []

    # Iterate over each unique campaign in valid_campaigns
    for campaign in RPC_df["Campaign Name (Informational only)"].unique():
        # Filter the rows for the current campaign
        campaign_rows = RPC_df[RPC_df["Campaign Name (Informational only)"] == campaign].copy()
        # campaign_rows.loc[:, "ASIN_Derived_bulk"] = campaign_rows["Campaign Name (Informational only)"].str.split().str[0]
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
                "Campaign Name (Informational only)": campaign,
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
    # Convert all values in the "Bid" column of filtered_bulk_df to float
    filtered_bulk_df["Bid"] = filtered_bulk_df["Bid"].astype(float)
    
    filtered_bulk_df["key"] = filtered_bulk_df.apply(
        lambda row: row["Keyword Text"] if pd.notna(row["Keyword Text"]) and row["Keyword Text"].strip() != "" else row["Product Targeting Expression"],
        axis=1
    )

    filtered_bulk_df["RPC"] = filtered_bulk_df.apply(
        lambda row: row["Sales"] / row["Clicks"] if row["Clicks"] > 0 else 0,
        axis=1
    )

    # Grouped summary of ASIN
    bulk_summary = filtered_bulk_df.groupby("Campaign Name (Informational only)").agg({
        "Impressions": "sum",
        "Clicks": "sum",
        "Spend": "sum",
        "Sales": "sum",
        "Orders": "sum"
    }).reset_index()

    # Calculate additional metrics
    bulk_summary["AOV"] = bulk_summary["Sales"] / bulk_summary["Orders"]
    bulk_summary["Click to Conversion"] = bulk_summary["Clicks"] / bulk_summary["Orders"]
    bulk_summary["CPC"] = bulk_summary["Spend"] / bulk_summary["Clicks"]
    bulk_summary["RPC"] = bulk_summary["Sales"] / bulk_summary["Clicks"]
    # Create a new column "key" in bulk_summary
    
    # Create a new column "New bid" in filtered_bulk_df and initialize with None
    filtered_bulk_df["New bid"] = pd.NA  # Using pd.NA instead of None for better pandas compatibility

    # Iterate over each row in campaign_bid_df
    for _, row in campaign_bid_df.iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        multiple = row["Multiplier"]
       
        # Update the "New bid" column in filtered_bulk_df where the campaign name matches
        filtered_bulk_df.loc[filtered_bulk_df["Campaign Name (Informational only)"] == campaign_name, "New bid"] = ((filtered_bulk_df.apply(
            lambda row: row["RPC"] if row["Campaign Name (Informational only)"] == campaign_name else row["New bid"],
            axis=1
        ))*target_acos)/(1+multiple)
    
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
            
#==================================================Plcement done==================================================
    # Iterate over each row in filtered_bulk_df where "New bid" is blank and "Clicks" is 0
    for index, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna() | (filtered_bulk_df["New bid"] == 0)].iterrows():
        
        campaign_name = row["Campaign Name (Informational only)"]
        
        # Skip if campaign_name is NaN or not a string
        if pd.isna(campaign_name) or not isinstance(campaign_name, str):
            continue

        # Find the CPC for the campaign from bulk_summary
        campaign_cpc_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["CPC"].values
        # Use default CPC of 5 if no CPC values are found or if CPC is NaN or 0
        campaign_cpc = campaign_cpc_values[0] if len(campaign_cpc_values) > 0 and not pd.isna(campaign_cpc_values[0]) and campaign_cpc_values[0] > 0 else 5

        # Handle invalid or missing bid values
        bid = row["Bid"] if not pd.isna(row["Bid"]) and row["Bid"] > 0 else row["Ad Group Default Bid (Informational only)"]

        # Calculate New Bid
        if row["Clicks"] == 0:
            # If clicks are 0, use the default logic
            new_bid = max(1, min(bid * 1.1, campaign_cpc))  # At least 1
            filtered_bulk_df.at[index, "New bid"] = new_bid
            
        elif row["Orders"] == 0 and row["Clicks"] > 0:
            campaign_name = row["Campaign Name (Informational only)"]
        
            # Skip if campaign_name is NaN or not a string
            if pd.isna(campaign_name) or not isinstance(campaign_name, str):
                continue
            
            # Find the CPC for the campaign from bulk_summary
            campaign_cpc_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["CPC"].values
            campaign_aov_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["AOV"].values
            campaign_clicks_to_conversion_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["Click to Conversion"].values
            # Use default CPC of 5 if no CPC values are found or if CPC is NaN or 0
            campaign_cpc = campaign_cpc_values[0] if len(campaign_cpc_values) > 0 and not pd.isna(campaign_cpc_values[0]) and campaign_cpc_values[0] > 0 else 5
            
            campaign_aov = campaign_aov_values[0] if len(campaign_aov_values) > 0 and not pd.isna(campaign_aov_values[0]) and campaign_aov_values[0] > 0 else 0
            
            campaign_clicks_to_conversion = campaign_clicks_to_conversion_values[0] if len(campaign_clicks_to_conversion_values) > 0 and not pd.isna(campaign_clicks_to_conversion_values[0]) and campaign_clicks_to_conversion_values[0] > 0 else 0
            bid = row["Bid"] if not pd.isna(row["Bid"]) and row["Bid"] > 0 else row["Ad Group Default Bid (Informational only)"]
            # Convert bid to float
            bid = float(bid)
            # Calculate New Bid
            new_bid = (campaign_aov * target_acos) / (campaign_clicks_to_conversion + row["Clicks"])
            new_bid = float(new_bid)
            if new_bid < 1:
                new_bid = 1
            
            if new_bid > bid:
                new_bid = bid
        
            # Assign new bid
            filtered_bulk_df.at[row.name, "New bid"] = new_bid
            

        elif row["Orders"] > 0 and row["Clicks"] > 0:
            # If clicks are greater than 0, adjust the bid based on ACOS
            if row["ACOS"] > target_acos:
                new_bid = row["CPC"] * (target_acos / row["ACOS"])
                
            else:
                if row["CPC"] < 0.5 * campaign_cpc:
                    new_bid = row["CPC"] * 1.5
                    
                elif row["CPC"] >= 0.5 * campaign_cpc and row["CPC"] < 0.75 * campaign_cpc:
                    new_bid = row["CPC"] * 1.25
                else:
                    new_bid = row["CPC"] * 1.1
                
                if new_bid < 1:
                    new_bid = 1
        else:
            filtered_bulk_df.at[index, "New bid"] = 4
            

        # Debug log for problematic cases
        if new_bid == 0:
            print(f"ERROR: Campaign '{campaign_name}' Row ID {index} resulted in New bid 0. Bid: {bid}, CPC: {campaign_cpc}")

        # Assign new bid
        filtered_bulk_df.at[index, "New bid"] = new_bid 

    # Iterate over each row in filtered_bulk_df where "New bid" is still NaN and "Clicks" > 0
    # for _, row in filtered_bulk_df[(filtered_bulk_df["New bid"].isna() | (filtered_bulk_df["New bid"] == 0)) & (filtered_bulk_df["Orders"] == 0) & (filtered_bulk_df["Clicks"] > 0)].iterrows():
    #     campaign_name = row["Campaign Name (Informational only)"]
        
    #     # Skip if campaign_name is NaN or not a string
    #     if pd.isna(campaign_name) or not isinstance(campaign_name, str):
    #         continue
        
    #     # Find the CPC for the campaign from bulk_summary
    #     campaign_cpc_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["CPC"].values
    #     campaign_aov_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["AOV"].values
    #     campaign_clicks_to_conversion_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["Clicks to Conversion"].values
    #     # Use default CPC of 5 if no CPC values are found or if CPC is NaN or 0
    #     campaign_cpc = campaign_cpc_values[0] if len(campaign_cpc_values) > 0 and not pd.isna(campaign_cpc_values[0]) and campaign_cpc_values[0] > 0 else 5
        
    #     campaign_aov = campaign_aov_values[0] if len(campaign_aov_values) > 0 and not pd.isna(campaign_aov_values[0]) and campaign_aov_values[0] > 0 else 0
        
    #     campaign_clicks_to_conversion = campaign_clicks_to_conversion_values[0] if len(campaign_clicks_to_conversion_values) > 0 and not pd.isna(campaign_clicks_to_conversion_values[0]) and campaign_clicks_to_conversion_values[0] > 0 else 0
    #     # Handle invalid or missing bid values
    #     bid = row["Bid"] if not pd.isna(row["Bid"]) and row["Bid"] > 0 else row["Ad Group Default Bid (Informational only)"]
    #     # Convert bid to float
    #     bid = float(bid)
    #     # Calculate New Bid
    #     new_bid = (campaign_aov * target_acos) / (campaign_clicks_to_conversion + row["Clicks"])
    #     new_bid = float(new_bid)
    #     if new_bid < 1:
    #         new_bid = 1
        
    #     if new_bid > bid:
    #         new_bid = bid
       
    #     # Assign new bid
    #     filtered_bulk_df.at[row.name, "New bid"] = new_bid
    #     filtered_bulk_df.at[row.name, "Remark5"] = "0 Order rows"
    # for _, row in filtered_bulk_df[filtered_bulk_df["New bid"].isna() | (filtered_bulk_df["New bid"] == 0) & (filtered_bulk_df["Orders"] > 0) & (filtered_bulk_df["Clicks"] > 0)].iterrows():
    #     campaign_name = row["Campaign Name (Informational only)"]
        
    #     # Skip if campaign_name is NaN or not a string
    #     if pd.isna(campaign_name) or not isinstance(campaign_name, str):
    #         continue
        
    #     # Find the CPC for the campaign from bulk_summary
    #     campaign_cpc_values = bulk_summary[bulk_summary["Campaign Name (Informational only)"] == campaign]["CPC"].values
    #     # Use default CPC of 5 if no CPC values are found or if CPC is NaN or 0
    #     campaign_cpc = campaign_cpc_values[0] if len(campaign_cpc_values) > 0 and not pd.isna(campaign_cpc_values[0]) and campaign_cpc_values[0] > 0 else 5

    #     # Handle invalid or missing bid values
    #     bid = row["Bid"] if not pd.isna(row["Bid"]) and row["Bid"] > 0 else row["Ad Group Default Bid (Informational only)"]

    #     # Check if ACOS is greater than target ACOS
    #     if row["ACOS"] > target_acos:
    #         # Calculate the new bid as row CPC * (target ACOS / row ACOS)
    #         new_bid = row["CPC"] * (target_acos / row["ACOS"])
    #         filtered_bulk_df.at[row.name, "Remark6"] = "acos limited"
    #     else:
    #         # Calculate the new bid as the minimum of row CPC * 1.1 and the CPC derived from bulk_summary
    #         new_bid = round(min(row["CPC"] * 1.1, campaign_cpc), 2)
    #         filtered_bulk_df.at[row.name, "Remark7"] = "cpc limited"
    #         if new_bid < 1:
    #             new_bid = 1
            
        
    #     # Update the "New bid" column in filtered_bulk_df
    #     filtered_bulk_df.at[row.name, "New bid"] = new_bid
    #     filtered_bulk_df.at[row.name, "Remark8"] = "final bid optimised"
    
    def adjust_bid(bid):
        new_bid = max(bid, 1.00)
        return round(new_bid, 2)
    filtered_bulk_df["New bid"] = filtered_bulk_df["New bid"].apply(adjust_bid)



    amazon_business_df = bulk_df[bulk_df["Placement"] == "Placement Amazon Business"].copy()
    amazon_business_df = amazon_business_df[amazon_business_df["Campaign State (Informational only)"] == "enabled"]
    # Iterate over each row in amazon_business_df
    for idx, row in amazon_business_df.iterrows():
        campaign_name = row["Campaign Name (Informational only)"]
        
        # Skip if campaign_name is NaN or not a string
        if pd.isna(campaign_name) or not isinstance(campaign_name, str):
            continue
        
        # Get the corresponding data from campaign_bid_df
        campaign_data = campaign_bid_df[campaign_bid_df["Campaign Name (Informational only)"] == campaign_name]
        
        if campaign_data.empty:
            continue
        
        # Get the multiplier from campaign_data
        multiplier = campaign_data["Multiplier"].values[0]
        
        # Set the multiplier in the Placement column
        amazon_business_df.at[idx, "Percentage"] = multiplier*100
    
    # Append all rows of amazon_business_df below the rows of filtered_bulk_df
    combined_df = pd.concat([filtered_bulk_df, amazon_business_df], ignore_index=True)

    # Create the placement_df DataFrame from placement_data
    filtered_bulk_df_mk = combined_df
    RPC_df_mk = RPC_df
    bulk_summary_mk = bulk_summary
    valid_campaigns_mk = valid_campaigns_mk
    return filtered_bulk_df_mk, RPC_df_mk, bulk_summary_mk, valid_campaigns_mk
