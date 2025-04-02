import pandas as pd
import os
from fuzzywuzzy import process

def read_sqp(file_path):
    """Read and standardize SQP CSV file."""
    try:
        df = pd.read_csv(file_path)
        df = standardize_headers(df)
        return df
    except Exception as e:
        raise Exception(f"Error reading SQP file: {str(e)}")

def calculate_sqp(df):
    """Calculate SQP metrics and identify different groups of keywords."""
    try:
        # Calculate key metrics
        df["impression share"] = df["Impressions: ASIN Count"]/df["Impressions: Total Count"]
        df["click share"] = df["Clicks: ASIN Count"]/df["Clicks: Total Count"]
        df["purchase share"] = df["Purchases: ASIN Count"]/df["Purchases: Total Count"]
        df["ctr asin"] = df["Clicks: ASIN Count"]/df["Impressions: ASIN Count"]
        df["cvr asin"] = df["Purchases: ASIN Count"]/df["Clicks: ASIN Count"]
        df["ctr overall"] = df["Clicks: Total Count"]/df["Impressions: Total Count"]
        df["cvr overall"] = df["Purchases: ASIN Count"]/df["Clicks: Total Count"]

        # Identify target keywords (good CTR and CVR)
        target_df = df[(df["ctr asin"] > df["ctr overall"]) & 
                     (df["cvr asin"] > df["cvr overall"]) & 
                     (df["Purchases: ASIN Count"] > 1)]
        
        # Identify keywords needing CTR improvement
        ctr_improve = df[(df["ctr asin"] < df["ctr overall"]) & 
                       (df["cvr asin"] > df["cvr overall"])]
        
        # Identify keywords needing CVR improvement
        cvr_improve = df[(df["ctr asin"] > df["ctr overall"]) & 
                       (df["cvr asin"] < df["cvr overall"])]

        return target_df, ctr_improve, cvr_improve
    except Exception as e:
        raise Exception(f"Error calculating SQP metrics: {str(e)}")

def timeline_sqp(df):
    """Analyze timeline trends in SQP data."""
    try:
        # Convert date and sort
        df["Reporting Date"] = pd.to_datetime(df["Reporting Date"], errors="coerce")
        df = df.sort_values(by="Reporting Date")

        # Calculate rolling average and trend
        df["Rolling Purchases"] = df.groupby("Search Query")["Purchases: ASIN Count"].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean()
        )

        df["Purchases Trend"] = df.groupby("Search Query")["Rolling Purchases"].diff()

        # Extract declining trends
        declining_trend_df = df[df["Purchases Trend"] < 0]
        declining_trend_df = declining_trend_df.drop(columns=["Rolling Purchases", "Purchases Trend"])

        return declining_trend_df
    except Exception as e:
        raise Exception(f"Error analyzing timeline trends: {str(e)}")

def match_headers(actual_headers):
    """Match headers using fuzzy matching for standardization."""
    expected_headers = [
        "ASIN", "Search Query", "Search Query Score", "Search Query Volume",
        "Impressions: Total Count", "Impressions: ASIN Count", "Impressions: ASIN Share %",
        "Clicks: Total Count", "Clicks: Click Rate %", "Clicks: ASIN Count",
        "Clicks: ASIN Share %", "Clicks: Price (Median)", "Clicks: ASIN Price (Median)",
        "Clicks: Same Day Shipping Speed", "Clicks: 1D Shipping Speed", "Clicks: 2D Shipping Speed",
        "Cart Adds: Total Count", "Cart Adds: Cart Add Rate %", "Cart Adds: ASIN Count",
        "Cart Adds: ASIN Share %", "Cart Adds: Price (Median)", "Cart Adds: ASIN Price (Median)",
        "Cart Adds: Same Day Shipping Speed", "Cart Adds: 1D Shipping Speed", "Cart Adds: 2D Shipping Speed",
        "Purchases: Total Count", "Purchases: Purchase Rate %", "Purchases: ASIN Count",
        "Purchases: ASIN Share %", "Purchases: Price (Median)", "Purchases: ASIN Price (Median)",
        "Purchases: Same Day Shipping Speed", "Purchases: 1D Shipping Speed", "Purchases: 2D Shipping Speed",
        "Marketplace", "Reporting Date"
    ]
    
    header_mapping = {}
    for header in actual_headers:
        match, score = process.extractOne(header, expected_headers)
        if score > 80:  # Threshold for similarity
            header_mapping[header] = match
    return header_mapping

def standardize_headers(df):
    """Standardize column headers using fuzzy matching."""
    actual_headers = df.columns.tolist()
    header_mapping = match_headers(actual_headers)
    return df.rename(columns=header_mapping)

def process_sqp_file(input_path, output_path):
    """Main function to process SQP file and save results."""
    try:
        # Read and process the file
        df = read_sqp(input_path)
        target_df, ctr_improve, cvr_improve = calculate_sqp(df)
        declining_trend_df = timeline_sqp(df)
        sqp_kw = target_df["Search Query"].unique()
        
        # Create a dataframe with just the keywords for a dedicated sheet
        keywords_df = pd.DataFrame({"Keywords": sqp_kw})

        # Export results to Excel
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            target_df.to_excel(writer, sheet_name="Good CTR & CVR", index=False)
            ctr_improve.to_excel(writer, sheet_name="CTR Improve", index=False)
            cvr_improve.to_excel(writer, sheet_name="CVR Improve", index=False)
            declining_trend_df.to_excel(writer, sheet_name="Declining Trend", index=False)
            keywords_df.to_excel(writer, sheet_name="Keywords", index=False)

        return {
            "target_df": target_df,
            "ctr_improve": ctr_improve,
            "cvr_improve": cvr_improve,
            "declining_trend_df": declining_trend_df,
            "sqp_kw": sqp_kw
        }
    except Exception as e:
        raise Exception(f"Failed to process SQP file: {str(e)}") 