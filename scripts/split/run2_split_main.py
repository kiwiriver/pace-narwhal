import os
import sys
import numpy as np
from datetime import datetime, timedelta
import argparse
from tqdm import tqdm

# Modify the library path on different machine
mapol_path = os.path.expanduser('~/github/mapoltool')
sys.path.append(mapol_path)
from tools.aeronet_batch_split import *

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = f"Not a valid date: '{s}'. Expected format: YYYY-MM-DD."
        raise argparse.ArgumentTypeError(msg)

def main():
    parser = argparse.ArgumentParser(
        description='Split AERONET data files based on product and date range.'
    )
    parser.add_argument('--suite1', type=str, required=True, help='AERONET Product Suite (e.g., AOD15=1)')
    parser.add_argument('--version1', type=str, required=True, help='AERONET Version (e.g., v3, inv_v3)')
    parser.add_argument('--start_date', type=valid_date, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=valid_date, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--input_dir', type=str, required=True, help='Base directory for downloaded aeronet_data')
    parser.add_argument('--output_dir', type=str, required=True, help='Path for split output data')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files (default: False)')
    args = parser.parse_args()

    # Product subdirectory
    prod_short = args.suite1.split('=')[0]

    # Dynamically create output directory
    base_out_dir = os.path.join(args.output_dir, prod_short)
    os.makedirs(base_out_dir, exist_ok=True)

    # Dynamically build the input file path
    path1 = os.path.join(args.input_dir, prod_short)
    filename = f"aeronet_{args.version1}_{prod_short}_ALL_{args.start_date.strftime('%Y%m%d')}_{args.end_date.strftime('%Y%m%d')}.txt"
    input_file = os.path.join(path1, filename)

    print("Processing file:", input_file)

    # Extract header information and data start line
    data_start, header = header_aeronet_data(input_file)
    print("Data start at line:", data_start, "Header:", header)

    # Dynamically assign the key column names for site and date from the file header
    site_name = header[0]
    date_name = header[1]
    time_name = header[2]

    # Handle duplicates in header names
    header = make_column_names_unique(header)

    # Prepare for chunk processing
    column_names = header
    skiprows = data_start - 1
    #chunk_size = 10**4
    chunk_size = 10**3 #good for one day

    # Call Data Processing Function
    split_aeronet_data(
        input_file=input_file,
        output_dir=base_out_dir,
        column_names=column_names,
        skiprows=skiprows,
        site_name=site_name,
        date_name=date_name,
        chunk_size=chunk_size,
        overwrite=args.overwrite
    )

    
    
    # Remove duplicates ONLY in folders corresponding to processed dates
    current_date = args.start_date
    while current_date <= args.end_date:
        subfolder = os.path.join(base_out_dir, current_date.strftime("%Y%m%d"))
        if os.path.isdir(subfolder):
            print(f"Removing duplicates in: {subfolder}")
            remove_duplicates_in_csv_files=remove_duplicates_in_csv_files(
                output_dir=subfolder,
                key_columns=[site_name, date_name, time_name]
            )
            print("verify duplicated sites", remove_duplicates_in_csv_files)
        else:
            print(f"Subfolder does not exist: {subfolder}, skipping duplicate removal.")
        current_date += timedelta(days=1)
        
    # Remove duplicates (all subfolders)
    #creat new data for each day, no need to remove duplicate elementss
    #remove_duplicates_in_csv_files(
    #    output_dir=base_out_dir,
    #    key_columns=[site_name, date_name, time_name]
    #)

if __name__ == '__main__':
    main()
