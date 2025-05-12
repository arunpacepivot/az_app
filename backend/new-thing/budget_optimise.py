import pandas as pd

def budget_optimisation(bulk_df, target_acos):
    budget_bulk_df = bulk_df[
        (bulk_df["Entity"].isin(["Campaign"])) &
        (bulk_df["State"] == "enabled") &
        (bulk_df["Campaign State (Informational only)"] == "enabled")      
    ].copy()  # Create explicit copy

    
    for _, row in budget_bulk_df.iterrows():
        if row["ACOS"] < target_acos*0.5 and row["ACOS"] > 0:
            new_budget = min(row["Daily Budget"] * 2, row["Spend"]*10)
            budget_bulk_df.at[row.name, "Daily Budget"] =max(new_budget, 200)
        elif row["ACOS"] < target_acos*0.75 and row["ACOS"] > target_acos*0.5:
            new_budget = min(row["Daily Budget"] * 1.5, row["Spend"]*10)
            budget_bulk_df.at[row.name, "Daily Budget"] =max(new_budget, 200)
        elif row["ACOS"] < target_acos*0.9 and row["ACOS"] > target_acos*0.75:
            new_budget = min(row["Daily Budget"] * 1.1, row["Spend"]*10)
            budget_bulk_df.at[row.name, "Daily Budget"] =max(new_budget, 200)
        elif row["ACOS"] > target_acos*0.9:
            new_budget = (row["Daily Budget"])
            budget_bulk_df.at[row.name, "Daily Budget"] =max(new_budget, 200)
        else:
            new_budget = (row["Daily Budget"])
            budget_bulk_df.at[row.name, "Daily Budget"] =max(new_budget, 200)

    budget_bulk_df["Daily Budget"] = budget_bulk_df["Daily Budget"].round(2)
    for _, row in budget_bulk_df.iterrows():
        budget_bulk_df.at[row.name, "Bidding Strategy"] = "dynamic bids - down only"
    return budget_bulk_df

