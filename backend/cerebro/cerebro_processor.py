import pandas as pd
import warnings
import os
import numpy as np
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def import_data(path: str) -> pd.DataFrame:
    """Read Excel file and preprocess the data."""
    try:
        # Read the Excel file from the given path into a pandas DataFrame
        df = pd.read_excel(path, dtype={0: str})  # Ensure the first column is read as string

        # Required columns for the analysis
        required_columns = [
            "Search Volume",
            "Position (Rank)",
            "Competitor Performance Score",
            "Competitor Rank (avg)",
            "Sponsored Rank (avg)",
            "Sponsored Rank (count)",
            "Ranking Competitors (count)"
        ]

        # Optional columns that will be created if missing
        optional_columns = {
            "Sponsored Product": 0  # Default value for missing Sponsored Product column
        }

        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Add optional columns with default values if they don't exist
        for col, default_value in optional_columns.items():
            if col not in df.columns:
                print(f"Warning: Column '{col}' not found. Creating it with default value {default_value}")
                df[col] = default_value

        # Convert all other columns to float
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        score_index = df.columns.get_loc("Competitor Performance Score")
        # Count the number of cells to the right of the "Competitor Performance Score" column 
        df["Competitor Count"] = df.iloc[:, score_index + 1:].apply(lambda row: ((row >= 1) & (row <= 30)).sum(), axis=1)

        # Insert the "Competitor Count" column before the "Competitor Performance Score" column
        competitor_performance_score_index = df.columns.get_loc("Competitor Performance Score")
        columns = list(df.columns)
        columns.insert(competitor_performance_score_index, columns.pop(columns.index("Competitor Count")))
        df = df[columns]

        # Count the number of cells to the right of the "Competitor Performance Score" column that have a value > 0 and < 30
        df["Rel Score"] = df.iloc[:, score_index + 1:].apply(lambda row: ((row > 0) & (row < 30)).sum(), axis=1)-1
        
        return df
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file at path {path} was not found.")
    except ValueError as ve:
        raise ValueError(f"Error: {str(ve)}")
    except Exception as e:
        raise Exception(f"An error occurred while reading the Excel file: {e}")

def competitor_gap(df, min_search_volume):
    """Identify keywords where competitors rank but you don't."""
    filtered_df = df[(df["Search Volume"]>min_search_volume) & (df["Position (Rank)"] == 0) & (df["Sponsored Product"]==0)]
    # Filter rows where at least one of the values to the right of "Competitor Performance Score" column is between 1 and 10 inclusive
    def is_value_between_1_and_10(row):
        # Get the index of the "Competitor Performance Score" column
        score_index = df.columns.get_loc("Competitor Performance Score")
        # Check if any value to the right of the "Competitor Performance Score" column is between 1 and 10
        return any(1 <= value <= 10 for value in row[score_index + 1:])

    filtered_df = filtered_df[filtered_df.apply(is_value_between_1_and_10, axis=1)]
    filtered_df["Remark"] = "Competitor Gap"
    return filtered_df

def competitor_lag(df, min_search_volume):
    """Identify keywords where you rank lower (15-306)."""
    # Filter for rows where "Position (Rank)" is between 15 and 306 inclusive
    filtered_df = df[(df["Search Volume"]>min_search_volume) & (df["Position (Rank)"] >= 15) & (df["Position (Rank)"] <= 306) & (df["Sponsored Product"]==0)]

    def is_value_between_1_and_10(row):
        # Get the index of the "Competitor Performance Score" column
        score_index = df.columns.get_loc("Competitor Performance Score")
        return any(1 <= value <= 10 for value in row[score_index + 1:])
    
    filtered_df = filtered_df[filtered_df.apply(is_value_between_1_and_10, axis=1)]
    filtered_df["Remark"] = "Competitor Lag"

    return filtered_df

def top_kw(df, min_search_volume):
    """Identify top keywords."""
    filtered_df = df[(df["Search Volume"]>min_search_volume) & (df["Competitor Rank (avg)"]>=1) & (df["Competitor Rank (avg)"]<=40)]
    
    score_index = df.columns.get_loc("Competitor Performance Score")
    # Filter rows where the count of values > 0 to the right of "Competitor Performance Score" is greater than the number of columns to the right of "Competitor Performance Score" - 1
    def count_ranking(row):
        score_index = df.columns.get_loc("Competitor Performance Score")
        # Count the number of cells to the right of the "Competitor Performance Score" column that have a value > 0
        count = sum(1 for value in row[score_index + 1:] if value > 0)
        return count

    # Apply the count_ranking function to each row and filter based on the condition
    filtered_df = filtered_df[filtered_df.apply(lambda row: count_ranking(row) > (len(df.columns) - score_index - 1), axis=1)]
    filtered_df["Remark"] = "Top KW"
    return filtered_df

def opportunity_kw(df, min_search_volume):
    """Identify opportunity keywords."""
    filtered_df=df[(df["Search Volume"]>min_search_volume) & (df["Competitor Performance Score"]<=5) & (df["Ranking Competitors (count)"]>=1) & (df["Ranking Competitors (count)"]<=2)]
    score_index = df.columns.get_loc("Competitor Performance Score")
   
    def is_value_between_1_and_15(row):
        # Get the index of the "Competitor Performance Score" column
        score_index = df.columns.get_loc("Competitor Performance Score")
        # Check if any value to the right of the "Competitor Performance Score" column is between 1 and 15
        return any(1 <= value <= 15 for value in row[score_index + 1:])

    filtered_df = filtered_df[filtered_df.apply(is_value_between_1_and_15, axis=1)]
    filtered_df["Remark"] = "Opportunity KW"
    return filtered_df

def sponsored_top_15(df, min_search_volume):
    """Identify top 15 sponsored keywords."""
    filtered_df=df[(df["Search Volume"]>min_search_volume) & (df["Sponsored Rank (avg)"]>=1) & (df["Sponsored Rank (avg)"]<=15) & (df["Sponsored Product"]==0) ].copy()
    filtered_df["Remark"] = "Sponsored Top 15"
    return filtered_df

def ppc_kw(df, min_search_volume):
    """Identify PPC keywords."""
    filtered_df=df[(df["Search Volume"]>min_search_volume*2) & (df["Sponsored Rank (count)"]>=1) & (df["Sponsored Rank (count)"]<=3)& (df["Sponsored Rank (avg)"]>=1) & (df["Sponsored Rank (avg)"]<=5) ].copy()
    filtered_df["Remark"] = "PPC KW"
    return filtered_df

def top_position_all_competitors(df, min_search_volume, position_limit):
    """Identify keywords in top positions."""
    filtered_df=df[(df["Search Volume"]>min_search_volume) & (df["Position (Rank)"]<=position_limit) & (df["Position (Rank)"]>0)].copy()
    filtered_df["Remark"] = f"Top {position_limit} Position All Competitors"
    return filtered_df

def top_position_competitor_count_less(df, min_search_volume, position_limit, comp_count, less_by):
    """Identify keywords in top positions with fewer competitors."""
    filtered_df=df[(df["Search Volume"]>min_search_volume) & (df["Position (Rank)"]<=position_limit) & (df["Position (Rank)"]>0)].copy()
    filtered_df=filtered_df[filtered_df["Ranking Competitors (count)"]<comp_count-less_by].copy()
    filtered_df["Remark"] = f"Top {position_limit} Position Competitor Count Less {less_by}"
    return filtered_df

def grade_column(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """Grade values in a column from 1-10."""
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in DataFrame.")
    
    # Ensure the column contains float values
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    
    # Calculate dynamic thresholds based on the column's values
    min_value = df[column_name].min()
    max_value = df[column_name].max()
    range_value = max_value - min_value
    num_thresholds = 10  # Define the number of thresholds
    thresholds = [min_value + (range_value / num_thresholds) * i for i in range(1, num_thresholds + 1)]
    
    def assign_grade(value: float) -> int:
        for i, threshold in enumerate(thresholds, start=1):
            if value <= threshold:
                return i
        return num_thresholds  # If value exceeds all thresholds, assign the highest grade
    
    # Apply the grading function to the specified column
    df[f"{column_name} Grade"] = df[column_name].apply(assign_grade)
    
    return df

def cerebro_process(path, min_search_volume=100):
    """Main function to process Cerebro data."""
    try:
        df = import_data(path)
        comp_count = max(df["Ranking Competitors (count)"])
        
        # List of analysis functions to apply
        analyses = [
            competitor_gap,
            competitor_lag,
            top_kw,
            opportunity_kw,
            sponsored_top_15,
            ppc_kw
        ]
        
        # Apply all analyses and combine results
        result_dfs = [func(df, min_search_volume) for func in analyses]
        
        # Add top position analyses
        for position in [10, 25, 55]:
            result_dfs.append(top_position_all_competitors(df, min_search_volume, position))
            
            # Add competitor count variations
            for less_by in range(1, 10):
                result_dfs.append(top_position_competitor_count_less(df, min_search_volume, position, comp_count, less_by))
        
        # Combine all results
        combined_df = pd.concat(result_dfs, ignore_index=True)
        
        # Remove duplicate rows based on the first column, keeping the first occurrence
        combined_df = combined_df.drop_duplicates(subset=combined_df.columns[0], keep="first")
        
        # Grade columns
        combined_df = grade_column(combined_df, "Search Volume")
        combined_df = grade_column(combined_df, "Competing Products")
        
        # Calculate scores
        combined_df["Average Grade"] = (combined_df["Search Volume Grade"] + combined_df["Competing Products Grade"])/2
        combined_df["score"] = combined_df["Competitor Count"]/combined_df["Average Grade"]
        
        # Add relevance based on score
        def assign_remark(score: float) -> str:
            if 0 < score <= 0.4:
                return "Good"
            elif 0.4 < score <= 0.7:
                return "Average"
            elif score > 0.7:
                return "Bad"
            else:
                return "Undefined"

        combined_df["Relevance"] = combined_df["score"].apply(assign_remark)
        cerebro_kw = combined_df.iloc[:, 0].unique()
        
        return combined_df, cerebro_kw
        
    except Exception as e:
        raise Exception(f"Error in Cerebro processing: {str(e)}")

def export_data(df, path):
    """Export DataFrame to Excel file."""
    try:
        if df is None:
            raise ValueError("Error: Cannot export None DataFrame")
            
        if df.empty:
            print("Warning: Exporting empty DataFrame")
            
        df.to_excel(path, index=False)
        return df
    except Exception as e:
        raise Exception(f"Error exporting data: {str(e)}")

def process_cerebro_file(input_path, output_path, min_search_volume=100):
    """Process a Cerebro file and save results to output path."""
    try:
        combined_df, cerebro_kw = cerebro_process(input_path, min_search_volume)
        
        # Create a dataframe with just the keywords for a dedicated sheet
        keywords_df = pd.DataFrame({"Keywords": cerebro_kw})
        
        # Export main results and keywords to separate sheets
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            combined_df.to_excel(writer, sheet_name="Analysis", index=False)
            keywords_df.to_excel(writer, sheet_name="Keywords", index=False)
        
        return combined_df, cerebro_kw
    except Exception as e:
        raise Exception(f"Failed to process Cerebro file: {str(e)}") 