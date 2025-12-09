import os

import sys
import numpy as np
from tqdm import tqdm
import importlib
from datetime import timedelta, datetime

mapol_path=os.path.expanduser('~/github/mapoltool')
sys.path.append(mapol_path)

from tools.aeronet_batch_download import download_aeronet_per_month

# Configuration settings
folder1 = "./aeronet_data"
version1 = "v3"
product1 = "AOD15=1"
avg1 = "AVG=10"
start_date = datetime(2024, 2, 1)
end_date = datetime(2025, 7, 31)

# Path to site list file
sites_file = "aeronet_site_list_aodv3_v1.5_2024.csv"
#sites_file = "test.csv"

if __name__ == "__main__":
    # Read task ID from SLURM
    task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))  # Default task ID is 0
    
    print("task_id", task_id)

    
    # Load sites from the file
    with open(sites_file, "r") as f:
        sites = [line.strip().split(",") for line in f if line.strip()]
    
    # Process the site corresponding to the current task ID
    try:
        site_info = sites[task_id]
        site_name, site_lat, site_lon = site_info[0], site_info[1], site_info[2]
        print(f"Processing site: {site_name}, Latitude: {site_lat}, Longitude: {site_lon}")
        download_aeronet_per_month(folder1, version1, product1, avg1, site_name, start_date, end_date)
    except IndexError:
        print(f"No site information found for task ID {task_id}")
