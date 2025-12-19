import os
import re
from datetime import datetime
import numpy as np
import pandas as pd
from netCDF4 import Dataset
from tqdm import tqdm  # For progress bar

def header_aeronet_data(file_path, start_str="AERONET_Site"):
    # Find the header line that starts with "AERONET_Site"
    header_line = None
    header_index = None
    with open(file_path, "r") as file:
        for index, line in enumerate(file):
            # Check if the line starts with "AERONET_Site"
            if line.strip().startswith(start_str):
                header_line = line.strip().replace("<br>", "")  # Clean the line
                header_index = index
                break
    
    if header_line is None:
        raise ValueError("Header line starting with 'AERONET_Site' not found in the file.")
    
    # Parse the header into column names
    header = header_line.split(',')
    
    # Dynamically determine where the data starts (next line after the header)
    data_start = header_index + 1
    
    return data_start, header

def read_aeronet_data_df(cleaned_file_path, data_start, header):
    # Load the cleaned file content into a DataFrame

    df = pd.read_csv(cleaned_file_path, skiprows=data_start, delimiter=',', names=header)
    # Inspect DataFrame
    
    return df

def make_column_names_unique(column_names):
    """
    Ensures column names are unique by appending a suffix (_1, _2, etc.) to duplicates.
    
    Parameters:
    - column_names: List of column names (possibly with duplicates).
    
    Returns:
    - A list of column names with duplicates renamed to unique values.
    """
    seen = {}
    unique_columns = []
    
    for name in column_names:
        if name in seen:
            seen[name] += 1
            unique_columns.append(f"{name}_{seen[name]}")  # Append a unique suffix
        else:
            seen[name] = 0
            unique_columns.append(name)
    
    return unique_columns
    
def split_aeronet_data(input_file, output_dir, column_names, skiprows=6, 
                       site_name="AERONET_Site", date_name="Date(dd:mm:yyyy)", 
                       chunk_size=10**6, overwrite=True, mode='a'):
    """
    Splits a large AERONET data file into smaller CSV files based on site and day.
    Optionally overwrites or skips existing folders.
    
    Parameters:
    - input_file: Path to the AERONET input text file.
    - output_dir: Directory where the split files will be saved.
    - column_names: List of column names in the dataset.
    - site_name: Column name referring to the AERONET site.
    - date_name: Column name referring to the measurement date (in 'dd:mm:yyyy').
    - chunk_size: Number of rows to process at a time (for large files).
    - overwrite: If True, overwrites existing folders for a day; if False, skips those folders.
    - mode='a': append to existing file, since the file is written line by line
    
    Note that, there could be an element of data belong to the next day but at 00:00:00, set overwrite=True
    
    there also could be duplicated elements, need clean up if the file is opened several times
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Estimate total chunks
    total_rows = sum(1 for _ in open(input_file)) - skiprows  # Total rows excluding metadata lines
    total_chunks = total_rows // chunk_size + (1 if total_rows % chunk_size > 0 else 0)
    print("Total rows:", total_rows, "Total chunks:", total_chunks)

    # Track created folders and skipped folders
    created_folders = set()
    skipped_folders = set()
    
    # Read data in chunks
    for chunk in tqdm(pd.read_csv(input_file, names=column_names, 
                                  skiprows=skiprows,  # Skip the AERONET metadata lines
                                  chunksize=chunk_size), total=total_chunks):
        
        # Process each row in the chunk
        for _, row in chunk.iterrows():
            site = row[site_name]  # Get the site name
            date = row[date_name]  # Get the measurement date

            #print(site_name, date_name)
            #print(row)
            
            # Convert date to YYYYMMDD format
            try:
                #print("date:", date)
                formatted_date = datetime.strptime(date, "%d:%m:%Y").strftime("%Y%m%d")
            except ValueError:
                # Skip rows with invalid date formats
                print(f"Skipping invalid date: {date}")
                continue
            
            # Create directory structure and filename
            date_folder = os.path.join(output_dir, formatted_date)  # YYYYMMDD folder

            # Check whether to handle the folder based on the `overwrite` parameter
            if not overwrite:
                # Skip folder if it exists and not overwriting
                if date_folder in skipped_folders or os.path.exists(date_folder):
                    if date_folder not in skipped_folders:
                        print(f"Skipping full folder: {date_folder}")
                        skipped_folders.add(date_folder)
                    continue
            
            # Create the folder for the first time and mark it as created
            if date_folder not in created_folders:
                os.makedirs(date_folder, exist_ok=True)
                created_folders.add(date_folder)
            
            # Final output file
            output_file = os.path.join(date_folder, f"{site}.csv")
            
            # Write or append the row to its corresponding file
            row.to_frame().T.to_csv(output_file, mode=mode, index=False, 
                                    header=not os.path.exists(output_file))  # Add header if file doesn't exist
    
    # Print summary of skipped folders
    if not overwrite:
        print("\nSummary:")
        print(f"Skipped {len(skipped_folders)} existing folders.")
        for folder in skipped_folders:
            print(f"  - {folder}")

def remove_duplicates_in_csv_files(output_dir, key_columns):
    """
    Cleans up duplicates in all CSV files created in the specified output directory.
    Returns a sorted list of site names (from file names) where duplicate rows were removed.

    Parameters:
    - output_dir: The top-level directory where the split CSV files are stored.
    - key_columns: List of column names to identify duplicates (e.g., site, date, and time).

    Files are cleaned and overwritten in place, removing any duplicate rows.
    """
    print("Cleaning CSV files for duplicate rows...")

    # To hold site names where dups were removed
    sites_with_duplicates = set()
    site_pattern = re.compile(r"^(.*?)\.csv$")

    # Walk through the directories to find all CSV files
    for root, _, files in os.walk(output_dir):
        for file in tqdm(files):
            if file.endswith(".csv"):
                file_path = os.path.join(root, file)
                try:
                    # Read the CSV file into a DataFrame
                    df = pd.read_csv(file_path)

                    # Remove duplicate entries based on key columns
                    df_cleaned = df.drop_duplicates(subset=key_columns)

                    # Calculate how many duplicates were removed
                    duplicates_removed = len(df) - len(df_cleaned)

                    # If duplicates were found, overwrite the file and collect site name
                    if duplicates_removed > 0:
                        df_cleaned.to_csv(file_path, index=False)  # Overwrite the file
                        match = site_pattern.match(file)
                        if match:
                            sites_with_duplicates.add(match.group(1))
                        print(f"File: {file_path}, Removed Duplicates: {duplicates_removed}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")

    # Output the sorted list of affected sites
    if sites_with_duplicates:
        print("\nSites with duplicate files detected and cleaned:")
        print(sorted(sites_with_duplicates))
    else:
        print("\nNo duplicate rows found in any site files.")

    # Optionally return the set or list if you want to use it programmatically
    return sorted(sites_with_duplicates)
