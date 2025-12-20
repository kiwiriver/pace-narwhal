import os
import sys
from datetime import datetime, timedelta
from tqdm import tqdm
#modify the library path on different machine
mapol_path = os.path.expanduser('/mnt/mfs/mgao1/analysis/github/pace-narwhal/')
sys.path.append(mapol_path)
from tools.narwhal_split_aeronet import *

path0='./aeronet_data_split/'
overwrite=True

# Product name (suite1)
#version1 = "v3"
#suite1 = "AOD15=1"  # Example use case
#suite1 = "SDA15=1"  # Example use case
#suite1 = "LWN15=1"  # Example use case

version1 = "inv_v3"
suite1 = "ALM15=1"  # Example use case

start_date = datetime(2024, 2, 1)  # Start of analysis period
#end_date = datetime(2024, 4, 1)   # End of analysis period
end_date = datetime(2025, 10, 1)   # End of analysis period


# **Automatically Create Output Directory and File Names**
# Use the suite name, start date, and end date to define paths and filenames dynamically
output_dir = f"{path0}{suite1.split('=')[0]}/"  # Use the product name (without "=1")
os.makedirs(output_dir, exist_ok=True)

# Base path and filenames for input data
path1 = f"/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/t01_aeronet_download/aeronet_data/{suite1.split('=')[0]}/"
filename = f"aeronet_{version1}_{suite1.split('=')[0]}_ALL_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.txt"
file1 = os.path.join(path1, filename)  # Full path to the input file
print(filename)

# **Extract Header Information and Data Start Line**
# Assuming `header_aeronet_data` is a helper function you already have
data_start, header = header_aeronet_data(file1)  # Extract headers and data start line
print(data_start, header)

# Dynamically assign the key column names for site and date from the file header
site_name = header[0]  # Assume the first header column is 'Site'
date_name = header[1]  # Assume the second header column is 'Date'
time_name= header[2]

# **Handle Duplicates in Header Names**
header = make_column_names_unique(header)  # Use the helper to ensure column names are unique

# Prepare input file and column names for chunk processing
column_names = header
input_file = file1
skiprows = data_start - 1  # Skip to the actual data rows

# Define chunk size for processing large files
#chunk_size = 10**3  # Adjust chunk size for memory efficiency (e.g., 1000 rows per chunk)
chunk_size = 10**4  # Adjust chunk size for memory efficiency (e.g., 1000 rows per chunk)

# **Call Data Processing Function**
split_aeronet_data(
    input_file=input_file,
    output_dir=output_dir,
    column_names=column_names,
    skiprows=skiprows,
    site_name=site_name,
    date_name=date_name,
    chunk_size=chunk_size,
    overwrite=overwrite
)

remove_duplicates_in_csv_files(
    output_dir=output_dir,
    key_columns=[site_name, date_name, time_name]
)
