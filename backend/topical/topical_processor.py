import pandas as pd
from typing import Dict, List
import warnings
import os
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def load_data(file_path: str, sheet_name: str) -> pd.DataFrame:
    """Load Excel data from the specified file and sheet."""
    data = pd.read_excel(file_path, sheet_name=sheet_name)
    data["ASIN"] = data["Campaign Name (Informational only)"].apply(lambda x: x.split()[0] if isinstance(x, str) else None)
    return data

def summarize_data(data: pd.DataFrame) -> pd.DataFrame:
    """Generate a grouped summary for ASIN data."""
    summary = data.groupby(["ASIN"]).agg({
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
    summary["Conversion"] = summary["Orders"] / summary["Clicks"]
    return summary

def filter_data(data: pd.DataFrame) -> pd.DataFrame:
    """Filter rows based on ASIN and Customer Search Term criteria."""
    filtered_data = data[data['ASIN'].str.startswith('B0', na=False)]
    return filtered_data

def filter_data_mk(data: pd.DataFrame) -> pd.DataFrame:
    """Filter rows based on ASIN and Customer Search Term criteria."""
    filtered_data_mk = data[~data['ASIN'].str.startswith('B0', na=False)]
    return filtered_data_mk

def aggregate_metrics(filtered_data: pd.DataFrame, metrics: List[str]) -> pd.DataFrame:
    """Aggregate metrics for rows with the same ASIN and Customer Search Term."""
    data_filtered = filtered_data[['ASIN', 'Customer Search Term'] + metrics].dropna(subset=['Customer Search Term'])
    aggregated_data = data_filtered.groupby(['ASIN', 'Customer Search Term']).agg({
        'Impressions': 'sum',
        'Clicks': 'sum',
        'Spend': 'sum',
        'Sales': 'sum',
        'Orders': 'sum'
    }).reset_index()
    return aggregated_data

def process_asin_data(data: pd.DataFrame, target_acos: float) -> Dict[str, pd.DataFrame]:
    """Process data for each ASIN and filter to top 80% revenue rows and ACOS threshold."""
    asin_groups = data.groupby("ASIN")
    asin_results: Dict[str, pd.DataFrame] = {}

    for asin, group in asin_groups:
        group = group.copy()
        group["Total Revenue"] = group["Sales"]
        group_sorted = group.sort_values(by="Total Revenue", ascending=False)
        group_sorted["Cumulative Revenue"] = group_sorted["Total Revenue"].cumsum()
        total_revenue = group_sorted["Total Revenue"].sum()
        group_sorted["Cumulative Revenue Percentage"] = group_sorted["Cumulative Revenue"] / total_revenue
        top_80_percent_data = group_sorted[group_sorted["Cumulative Revenue Percentage"] <= 0.80].copy()

        if top_80_percent_data.empty:
            continue
        else:
            asin_results[asin] = top_80_percent_data

        current_asin_data = asin_results.get(asin)
        if current_asin_data is None:
            continue

        filtered_data = current_asin_data[current_asin_data["Orders"] >= 2].copy()
        filtered_data["ACOS"] = filtered_data["Spend"] / filtered_data["Sales"]
        filtered_data = filtered_data[filtered_data["ACOS"] <= target_acos]

        exclusion_words: List[str] = ["skillofun"]
        if exclusion_words:
            pattern = "|".join(exclusion_words)
            filtered_data = filtered_data[~filtered_data["Customer Search Term"].str.contains(pattern, case=False, na=False)]
        asin_results[asin] = filtered_data

    return asin_results

def process_asin_results(asin_results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Process ASIN data and concatenate into a single DataFrame."""
    dataframes = []
    for asin, df in asin_results.items():
        df = df.copy()  # Create a copy to avoid modifying original
        df["ASIN"] = asin
        # Rename 'Customer Search Term' to 'KW/PT' to match with result_df
        df = df.rename(columns={"Customer Search Term": "KW/PT"})
        dataframes.append(df)
    
    if not dataframes:
        return pd.DataFrame()  # Return empty DataFrame if no data
    
    return pd.concat(dataframes, ignore_index=True)

def read_and_prepare_bulk_data(bulk_file_path: str, bulk_sheet_name: str) -> pd.DataFrame:
    """Read and prepare bulk data efficiently."""
    # Choose the appropriate engine based on file type
    engine = "openpyxl" if bulk_file_path.endswith(".xlsx") else "pyxlsb" if bulk_file_path.endswith(".xlsb") else None
    
    bulk_df = pd.read_excel(
        bulk_file_path,
        sheet_name=bulk_sheet_name,
        usecols=["Campaign Name (Informational only)", "Product Targeting Expression", "Keyword Text", "Match Type"],
        dtype={"Campaign Name (Informational only)": "string", "Product Targeting Expression": "string", "Keyword Text": "string", "Match Type": "string"},
        engine=engine
    )
    
    # Extract ASIN from "Campaign Name (Informational only)" column
    bulk_df["ASIN"] = bulk_df["Campaign Name (Informational only)"].str.split().str[0]
    
    return bulk_df

def extract_asin_kw_match_data(bulk_df: pd.DataFrame) -> pd.DataFrame:
    """Extract ASIN keyword match data."""
    # Only include rows with valid data and exclude negative keywords
    kw_match_df = bulk_df.dropna(subset=["Campaign Name (Informational only)", "Keyword Text", "Match Type"])
    kw_match_df = kw_match_df[~kw_match_df["Match Type"].str.contains("Negative", na=False, case=False)]
    
    # Create a copy to avoid warnings
    kw_match_df = kw_match_df[["Campaign Name (Informational only)", "Keyword Text", "Match Type"]].copy()
    
    # Extract ASIN and standardize match types
    kw_match_df["ASIN"] = kw_match_df["Campaign Name (Informational only)"].str.split().str[0]
    kw_match_df["Match Type"] = kw_match_df["Match Type"].str.lower()
    
    # Rename keyword column
    kw_match_df = kw_match_df.rename(columns={"Keyword Text": "KW/PT"})
    
    return kw_match_df[["ASIN", "KW/PT", "Match Type"]]

def filter_product_targeting_data(bulk_df: pd.DataFrame) -> pd.DataFrame:
    """Filter rows for Product Targeting Expressions that start with 'asin'."""
    filtered_pt_df = bulk_df[bulk_df["Product Targeting Expression"].str.startswith("asin", na=False)].copy()
    filtered_pt_df["ASIN"] = filtered_pt_df["Campaign Name (Informational only)"].str.split().str[0]
    filtered_pt_df["KW/PT"] = filtered_pt_df["Product Targeting Expression"].str.split('"').str[1]
    filtered_pt_df["Match Type"] = "PT"
    return filtered_pt_df[["ASIN", "KW/PT", "Match Type"]]

def prepare_result_dataframe(asin_kw_match_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare result DataFrame with Broad, Phrase, Exact, and PT columns."""
    # Get unique ASIN and KW/PT combinations
    if asin_kw_match_df.empty:
        return pd.DataFrame(columns=["ASIN", "KW/PT", "Broad", "Phrase", "Exact", "PT"])
        
    unique_asin_kw = asin_kw_match_df[["ASIN", "KW/PT"]].drop_duplicates()
    result_df = unique_asin_kw.copy()
    
    # Initialize match type columns with "doesn't exist"
    for col in ["Broad", "Phrase", "Exact", "PT"]:
        result_df[col] = "doesn't exist"
    
    # Update match types that exist
    match_types = {
        "broad": "Broad",
        "phrase": "Phrase",
        "exact": "Exact",
        "pt": "PT"
    }
    
    # Process each row in the input DataFrame
    for _, row in asin_kw_match_df.iterrows():
        match_type = row["Match Type"].lower()
        if match_type in match_types:
            col_name = match_types[match_type]
            mask = (result_df["ASIN"] == row["ASIN"]) & (result_df["KW/PT"] == row["KW/PT"])
            result_df.loc[mask, col_name] = "exists"
    
    return result_df

def merge_data_and_export(writer, combined_df: pd.DataFrame, result_df: pd.DataFrame, sheet_name: str) -> None:
    """Merge result DataFrame with combined ASIN data and export to Excel."""
    if combined_df.empty:
        # If there's no data, create an empty DataFrame with headers
        empty_df = pd.DataFrame(columns=["ASIN", "KW/PT", "Broad", "Phrase", "Exact", "PT", 
                                        "Impressions", "Clicks", "Spend", "Sales", "Orders"])
        empty_df.to_excel(writer, sheet_name=sheet_name, index=False)
        return
        
    merged_df = combined_df.merge(result_df, on=["ASIN", "KW/PT"], how="left")
    
    # Fill NaN values in match columns
    match_cols = ["Broad", "Phrase", "Exact", "PT"]
    merged_df = merged_df.assign(**{
        col: merged_df[col].fillna("doesn't exist") 
        for col in match_cols
    })

    # Export to Excel with specified sheet name
    merged_df.to_excel(writer, sheet_name=sheet_name, index=False)

def process_topical_file(bulk_file_path: str, output_file_path: str, target_acos: float = 0.25) -> Dict:
    """Main function to process topical analysis."""
    try:
        sheet_name = 'SP Search Term Report'
        bulk_sheet_name = 'Sponsored Products Campaigns'
        
        # Load and process data
        data = load_data(bulk_file_path, sheet_name)
        summarized_data = summarize_data(data)
        filtered_data = filter_data(data)
        filtered_data_mk = filter_data_mk(data)
        metrics = ['Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'Units']
        aggregated_data = aggregate_metrics(filtered_data, metrics)
        aggregated_data_mk = aggregate_metrics(filtered_data_mk, metrics)
        asin_results = process_asin_data(aggregated_data, target_acos)
        asin_results_mk = process_asin_data(aggregated_data_mk, target_acos)
        
        # Export data to Excel file
        with pd.ExcelWriter(output_file_path, engine="xlsxwriter") as writer:
            bulk_df = read_and_prepare_bulk_data(bulk_file_path, bulk_sheet_name)
            asin_kw_match_data = extract_asin_kw_match_data(bulk_df)
            product_targeting_data = filter_product_targeting_data(bulk_df)
            
            # Handle case where one might be empty
            if not asin_kw_match_data.empty or not product_targeting_data.empty:
                all_match_data = pd.concat([asin_kw_match_data, product_targeting_data], ignore_index=True) if not product_targeting_data.empty else asin_kw_match_data
            else:
                all_match_data = pd.DataFrame(columns=["ASIN", "KW/PT", "Match Type"])
                
            result_df = prepare_result_dataframe(all_match_data)
            
            # Export B0 ASINs to first sheet
            combined_df = process_asin_results(asin_results)
            merge_data_and_export(writer, combined_df, result_df, "B0 ASINs")
            
            # Export non-B0 ASINs to second sheet
            combined_df_mk = process_asin_results(asin_results_mk)
            merge_data_and_export(writer, combined_df_mk, result_df, "Non-B0 ASINs")
        
        return {
            "status": "success",
            "message": "Topical analysis completed successfully",
            "b0_asin_count": len(asin_results),
            "non_b0_asin_count": len(asin_results_mk)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        } 