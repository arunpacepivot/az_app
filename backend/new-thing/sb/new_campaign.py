import pandas as pd
from typing import List, Tuple
import warnings
warnings.filterwarnings("ignore")

#filter for rows where campaign state is enabled, state is enabled, sales>=2
def filter_sbr_single_keyword_df(df):
    keyword_filtered_df = df[
        (df["Campaign State (Informational only)"] == "enabled") &
        (df["State"] == "enabled") &
        (df["Orders"] >= 2) &
        (df["Keyword Text"].notna()) &
        (df["Keyword Text"] != "")&
        (df["Match Type"].str.lower() != "exact")
    ].copy()
    
    keyword_filtered_df["ASIN"] = keyword_filtered_df["Campaign Name (Informational only)"].str.split(",").str[0]
    return keyword_filtered_df

def filter_sbr_single_product_df(df):
    product_filtered_df = df[
        (df["Campaign State (Informational only)"] == "enabled") &
        (df["State"] == "enabled") &
        (df["Sales"] >= 2) &
        (df["Match Type"].str.startswith("asin"))
    ].copy()
    product_filtered_df["ASIN"] = product_filtered_df["Campaign Name (Informational only)"].str.split(",").str[0]
    return product_filtered_df

def check_duplication(bulk_df, keyword_filtered_df, product_filtered_df, target_acos):
    bulk_df = bulk_df.copy()
    filtered_bulk_df = bulk_df[
        (bulk_df["Campaign State (Informational only)"] == "enabled") &
        (bulk_df["State"] == "enabled") &
        (bulk_df["Campaign State (Informational only)"] == "Running") &
        (bulk_df["Entity"].isin(["Keyword", "Product"]))
    ].copy()
    filtered_bulk_df["ASIN"] = filtered_bulk_df["Campaign Name (Informational only)"].str.split(",").str[0]
    # Iterate over each row in keyword_filtered_df
    for index, row in keyword_filtered_df.iterrows():
        asin = row["ASIN"]
        customer_search_term = row["Customer Search Term"]
        
        # Check if a row exists in filtered_bulk_df with the same ASIN and Keyword Text
        if not filtered_bulk_df[
            (filtered_bulk_df["ASIN"] == asin) & 
            (filtered_bulk_df["Keyword Text"] == customer_search_term)
        ].empty:
            # If true, delete the row from keyword_filtered_df
            keyword_filtered_df.drop(index, inplace=True)
    
    for index, row in product_filtered_df.iterrows():
        asin = row["ASIN"]
        customer_search_term = row["Customer Search Term"]
        
        # Check if a row exists in filtered_bulk_df with the same ASIN and Keyword Text
        if not filtered_bulk_df[
            (filtered_bulk_df["ASIN"] == asin) & 
            (filtered_bulk_df["Product Targeting Expression"] == customer_search_term)
        ].empty:
            # If true, delete the row from keyword_filtered_df
            product_filtered_df.drop(index, inplace=True)
    
    # Combine keyword_filtered_df and product_filtered_df into a new DataFrame
    combined_df = pd.concat([keyword_filtered_df, product_filtered_df], ignore_index=True)

    # Reset the index of the new DataFrame
    combined_df.reset_index(drop=True, inplace=True)
    # Add a new column 'ideal bid' in combined_df and initialize it with default value 0.0
    combined_df["ideal bid"] = 0.0

    # Iterate over each row in combined_df to set the 'ideal bid' value
    for index, row in combined_df.iterrows():
        if row["ACOS"] < target_acos:
            combined_df.at[index, "ideal bid"] = row["CPC"] * 1.1
        elif row["ACOS"] > target_acos:
            combined_df.at[index, "ideal bid"] = (row["Sales"] / row["Clicks"]) * target_acos

    # Drop all columns except 'ASIN', 'Customer Search Term', and 'ideal bid'
    target_df = combined_df[["ASIN", "Customer Search Term", "ideal bid"]]

    return target_df,combined_df

def harvest_sb(bulk_df, data, target_acos):
    keyword_filtered_df=filter_sbr_single_keyword_df(data)
    
    product_filtered_df=filter_sbr_single_product_df(data)
    
    target_df,combined_df=check_duplication(bulk_df, keyword_filtered_df, product_filtered_df, target_acos)
    return target_df,combined_df

if __name__ == "__main__":
    bulk_df=pd.read_csv("bulk_df.csv")
    target_acos=0.3
    target_df,combined_df=harvest_sb(bulk_df, target_acos)
    print(target_df)
    print(combined_df)



