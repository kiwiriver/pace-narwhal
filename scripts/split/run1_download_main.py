import os
import sys
import time
from datetime import datetime
import argparse
from tqdm import tqdm

# Modify the library path on different machine
mapol_path = os.path.expanduser('~/github/mapoltool')
sys.path.append(mapol_path)
from tools.aeronet_batch_download import download_aeronet_all  # Import the function

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = f"Not a valid date: '{s}'. Expected format: YYYY-MM-DD."
        raise argparse.ArgumentTypeError(msg)

def main():
    parser = argparse.ArgumentParser(description='Download AERONET data with custom suite/version and dates.')
    parser.add_argument('--suite1', type=str, required=True, help='Product suite (e.g., AOD15=1, SDA15=1, LWN15=1, ALM15=1)')
    parser.add_argument('--version1', type=str, required=True, help='AERONET version (e.g., v3, inv_v3)')
    parser.add_argument('--start_date', type=valid_date, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=valid_date, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--folder1', type=str, required=True, help='output folder')


    args = parser.parse_args()

    # Static configuration
    #folder1 = "./aeronet_data"
    folder1 = args.folder1
    avg1 = "AVG=10"
    product1 = "product=ALL"

    # Call the download function
    time.sleep(5)
    download_aeronet_all(folder1, args.version1, args.suite1, product1, avg1, args.start_date, args.end_date)

if __name__ == '__main__':
    main()
