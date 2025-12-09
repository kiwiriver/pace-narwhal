import os
import shutil
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import glob
import re
from collections import defaultdict
from tools.aeronet_batch_split import remove_duplicates_in_csv_files, header_aeronet_data

import requests
import tarfile

import os
import requests
import tarfile
from datetime import datetime

def download_and_extract_with_date(url, download_dir):
    """
    # Example usage:
    download_dir = "/your/target/folder"  # Change to your desired directory
    url = "https://aeronet.gsfc.nasa.gov/new_web/All_MAN_Data_V3.tar.gz"
    
    download_and_extract_with_date(url, download_dir)
    
    download file name:
    All_MAN_Data_V3_20251020.tar.gz
    """
    os.makedirs(download_dir, exist_ok=True)

    # Make a filename with a date stamp (YYYYMMDD)
    date_stamp = datetime.now().strftime('%Y%m%d')
    basename = os.path.basename(url)
    # Split for .tar.gz
    name_part, ext = os.path.splitext(basename)
    if ext == '.gz':  # handle .tar.gz
        name_part2, ext2 = os.path.splitext(name_part)
        final_basename = f"{name_part2}_{date_stamp}{ext2}{ext}"
    else:
        final_basename = f"{name_part}_{date_stamp}{ext}"

    tar_path = os.path.join(download_dir, final_basename)

    if os.path.exists(tar_path):
        print(f"File {tar_path} already exists. Skipping download.")
    else:
        print(f"Downloading {url} ...")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(tar_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"Downloaded to {tar_path}")

    # Extract the tar.gz
    print("Extracting the archive...")
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(path=download_dir)
    print(f"Extracted all files to {download_dir}")


    
def prepare_man_data(input_folder, output_folder, input_folder2, output_folder2, \
                     pattern1='.*2[4-9].*all_points.*15$'):
    
    """prepare man data, split into daily folders, remove duplicated files"""
    
    #*2[4-9]*all_points.lev15
    
    
    print(pattern1)
    man_copy_matching_files(input_folder, output_folder,pattern=pattern1)
    
    # Path to your text file
    path1=output_folder
    filev=glob.glob(path1+'*')
    file1 = filev[0]
    print(file1)
    data_start, header = header_aeronet_data(file1, start_str='Date(dd:mm:yyyy)')
    print('data_start, header')
    print(data_start, header)
    
    skiprows=data_start-1
    man_split_aeronet_data_folder(
        input_folder=input_folder2,
        output_folder=output_folder2, skiprows=skiprows
    )
    
    #base_out_dir='./MAN_AOD15/'
    base_out_dir=output_folder2
    site_name, date_name, time_name = "AERONET_Site", "Date(dd:mm:yyyy)",'Time(hh:mm:ss)'
    sites_with_duplicates=remove_duplicates_in_csv_files(
        output_dir=base_out_dir,
        key_columns=[site_name, date_name, time_name]
    )
    print(sites_with_duplicates)
    
def man_copy_matching_files(input_folder, output_folder, pattern='.*2[4-9].*all_points.*15$'):
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Define the regex pattern based on the shell pattern
    pattern = re.compile(pattern)
    
    for filename in os.listdir(input_folder):
        if pattern.match(filename):
            src = os.path.join(input_folder, filename)
            dst = os.path.join(output_folder, filename)
            shutil.copy2(src, dst)
            #print(f"Copied: {src} -> {dst}")
    
def man_split_aeronet_data_folder(input_folder, output_folder,
                              skiprows=6,
                              date_name="Date(dd:mm:yyyy)",
                              chunk_size=10**6,
                              overwrite=True,
                              mode='a', site_pattern=r"^(.*?)_\d{2}"):
    """
    Processes all AERONET part files in input_folder.
    Merges all parts per site, splits daily, preserves all columns, and adds "AERONET_Site" as first column.
    Creates <output_dir>/<YYYYMMDD>/<SiteName>.csv for each site & date.

    Get site name based on: site_pattern r"^(.*?)_\d{2}" (string before the first _??)

    Notes:
    add with open(input_file, errors="replace") to avoid break the code, for the following example:
        UnicodeDecodeError on line 4: 'utf-8' codec can't decode byte 0xe9 in position 21: invalid continuation byte
        Problematic line (raw bytes): b'PI=Pawan Gupta_and_St\xe9phane Maritorena,Email=Pawan.Gupta@nasa.gov_and_stephane.maritorena@ucsb.edu\n'

    for pandas, we need to use encoding_errors='replace'
    pd.read_csv(input_file, names=col_names[1:], \
                                     skiprows=skiprows+1, chunksize=chunk_size, \
                                     encoding_errors='replace')
                                     
    """
    os.makedirs(output_folder, exist_ok=True)

    # Find all files matching the general pattern
    pattern = os.path.join(input_folder, "*")
    files = glob.glob(pattern)
    if not files:
        print(f"No files matching pattern in {input_folder}")
        return

    # Group files by site name (everything before the first _??)
    site_files = defaultdict(list)
    site_regex = re.compile(site_pattern)

    for file in files:
        base = os.path.basename(file)
        m = site_regex.match(base)
        if m:
            site = m.group(1)
            site_files[site].append(file)
        else:
            print(f"Skipped file with bad name: {base}")

    # For each site, process all its part-files together
    for site, part_files in site_files.items():
        print(f"\nProcessing site '{site}' with {len(part_files)} file parts")
        dataframes = []

        # Collect all data from each part for this site
        for input_file in part_files:
            # Read header
            with open(input_file, errors="replace") as f:
                for _ in range(skiprows):
                    next(f)
                header_line = next(f)
            col_names = [c.strip() for c in header_line.strip().split(',')]

            # Add AERONET_Site as first column name if not already
            col_names = (["AERONET_Site"] + [cn for cn in col_names if cn != "AERONET_Site"])

            # Load all data in chunks
            for chunk in pd.read_csv(input_file, names=col_names[1:], \
                                     skiprows=skiprows+1, chunksize=chunk_size, \
                                     encoding_errors='replace'):
                # Insert the site name as first column for all rows in chunk
                chunk.insert(0, "AERONET_Site", site)
                dataframes.append(chunk)

        if not dataframes:
            continue  # This site has no valid data

        # Combine all parts for this site
        site_data = pd.concat(dataframes, ignore_index=True)

        # (Optional) Deduplicate rows - up to you! 
        # site_data = site_data.drop_duplicates()  

        # Group by date in "Date(dd:mm:yyyy)" column
        for date_val, date_df in site_data.groupby(date_name):
            try:
                formatted_date = datetime.strptime(str(date_val), "%d:%m:%Y").strftime("%Y%m%d")
            except Exception:
                print(f"Invalid date '{date_val}' for site '{site}' - skipping.")
                continue

            date_folder = os.path.join(output_folder, formatted_date)
            os.makedirs(date_folder, exist_ok=True)

            output_file = os.path.join(date_folder, f"{site}.csv")

            # Write out the data chunk - overwrite or append?
            # If overwrite=False and file exists, skip
            if not overwrite and os.path.exists(output_file):
                print(f"  (skipped existing {output_file})")
                continue

            # Always write header since we've ensured column order and content
            write_header = overwrite or not os.path.exists(output_file)
            date_df.to_csv(output_file, mode='w' if overwrite else 'a',
                           index=False, header=write_header)
            print(f"  Wrote {len(date_df)} records to {output_file}")