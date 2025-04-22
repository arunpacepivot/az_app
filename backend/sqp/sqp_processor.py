import pandas as pd
import os
from fuzzywuzzy import process

def read_sqp(file_path):
    """Read and standardize SQP CSV or Excel file."""
    try:
        # Determine file type based on extension
        file_extension = os.path.splitext(file_path.lower())[1]
        
        # Read file based on its extension
        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise Exception(f"Unsupported file format: {file_extension}. Please use CSV or Excel files.")
            
        df = standardize_headers(df)
        return df
    except Exception as e:
        raise Exception(f"Error reading SQP file: {str(e)}")

def calculate_sqp(df):
    """Calculate SQP metrics and identify different groups of keywords."""
    try:
        # Handle empty dataframe
        if df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
        # Create safe division function to handle zeros
        def safe_div(a, b):
            return a / b if b != 0 else 0
            
        # Apply safe division function to calculate metrics
        df["impression share"] = df.apply(
            lambda row: safe_div(row["Impressions: ASIN Count"], row["Impressions: Total Count"]), 
            axis=1
        )
        df["click share"] = df.apply(
            lambda row: safe_div(row["Clicks: ASIN Count"], row["Clicks: Total Count"]), 
            axis=1
        )
        df["purchase share"] = df.apply(
            lambda row: safe_div(row["Purchases: ASIN Count"], row["Purchases: Total Count"]), 
            axis=1
        )
        df["ctr asin"] = df.apply(
            lambda row: safe_div(row["Clicks: ASIN Count"], row["Impressions: ASIN Count"]), 
            axis=1
        )
        df["cvr asin"] = df.apply(
            lambda row: safe_div(row["Purchases: ASIN Count"], row["Clicks: ASIN Count"]), 
            axis=1
        )
        df["ctr overall"] = df.apply(
            lambda row: safe_div(row["Clicks: Total Count"], row["Impressions: Total Count"]), 
            axis=1
        )
        df["cvr overall"] = df.apply(
            lambda row: safe_div(row["Purchases: ASIN Count"], row["Clicks: Total Count"]), 
            axis=1
        )
        
        # Handle NaN values by replacing with zeros
        df = df.fillna(0)

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
        
        # Handle empty result dataframes
        target_df = target_df if not target_df.empty else pd.DataFrame()
        ctr_improve = ctr_improve if not ctr_improve.empty else pd.DataFrame()
        cvr_improve = cvr_improve if not cvr_improve.empty else pd.DataFrame()

        return target_df, ctr_improve, cvr_improve
    except Exception as e:
        raise Exception(f"Error calculating SQP metrics: {str(e)}")

def timeline_sqp(df):
    """Analyze timeline trends in SQP data."""
    try:
        # Handle empty dataframe
        if df.empty:
            return pd.DataFrame()
            
        # Check if required columns exist
        required_columns = ["Reporting Date", "Search Query", "Purchases: ASIN Count"]
        for col in required_columns:
            if col not in df.columns:
                return pd.DataFrame()
        
        # Convert date and sort, handle errors
        try:
            df["Reporting Date"] = pd.to_datetime(df["Reporting Date"], errors="coerce")
            # Filter out rows with invalid dates
            df = df.dropna(subset=["Reporting Date"])
            
            # If after conversion we have no data, return empty DataFrame
            if df.empty:
                return pd.DataFrame()
                
            df = df.sort_values(by="Reporting Date")
        except Exception:
            # If date conversion fails completely, return empty DataFrame
            return pd.DataFrame()

        # Group by search query and calculate rolling means
        try:
            # Calculate rolling average and trend
            df["Rolling Purchases"] = df.groupby("Search Query")["Purchases: ASIN Count"].transform(
                lambda x: x.rolling(window=3, min_periods=1).mean()
            )

            df["Purchases Trend"] = df.groupby("Search Query")["Rolling Purchases"].diff()
            
            # Handle NaN values that might result from diff operation
            df = df.fillna(0)

            # Extract declining trends
            declining_trend_df = df[df["Purchases Trend"] < 0]
            
            # If no declining trends, return empty DataFrame
            if declining_trend_df.empty:
                return pd.DataFrame()
                
            declining_trend_df = declining_trend_df.drop(columns=["Rolling Purchases", "Purchases Trend"])
            return declining_trend_df
        except Exception:
            # If rolling calculations fail, return empty DataFrame
            return pd.DataFrame()
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
        
        # Extract keywords, with fallbacks
        sqp_kw = []
        if not target_df.empty:
            sqp_kw = target_df["Search Query"].unique()
        elif not ctr_improve.empty:
            # Fallback 1: Use CTR improvement keywords
            sqp_kw = ctr_improve["Search Query"].unique()
        elif not cvr_improve.empty:
            # Fallback 2: Use CVR improvement keywords
            sqp_kw = cvr_improve["Search Query"].unique()
        elif not declining_trend_df.empty:
            # Fallback 3: Use declining trend keywords
            sqp_kw = declining_trend_df["Search Query"].unique()
        
        # Create a dataframe with just the keywords for a dedicated sheet
        if len(sqp_kw) > 0:
            keywords_df = pd.DataFrame({"Keywords": sqp_kw})
        else:
            # Add a note if no keywords found
            keywords_df = pd.DataFrame({"Note": ["No keywords found that meet analysis criteria"]})

        # Export results to Excel with error handling
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            # Handle empty dataframes by writing a note
            if target_df.empty:
                pd.DataFrame({"Note": ["No keywords found with good CTR & CVR"]}).to_excel(
                    writer, sheet_name="Good CTR & CVR", index=False
                )
            else:
                target_df.to_excel(writer, sheet_name="Good CTR & CVR", index=False)
                
            if ctr_improve.empty:
                pd.DataFrame({"Note": ["No keywords found that need CTR improvement"]}).to_excel(
                    writer, sheet_name="CTR Improve", index=False
                )
            else:
                ctr_improve.to_excel(writer, sheet_name="CTR Improve", index=False)
                
            if cvr_improve.empty:
                pd.DataFrame({"Note": ["No keywords found that need CVR improvement"]}).to_excel(
                    writer, sheet_name="CVR Improve", index=False
                )
            else:
                cvr_improve.to_excel(writer, sheet_name="CVR Improve", index=False)
                
            if declining_trend_df.empty:
                pd.DataFrame({"Note": ["No keywords found with declining trend"]}).to_excel(
                    writer, sheet_name="Declining Trend", index=False
                )
            else:
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