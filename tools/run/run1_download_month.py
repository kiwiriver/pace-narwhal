import os
from datetime import datetime
from my_aeronet_package.aeronet_utils import download_aeronet_per_month

# Configuration settings
folder1 = "./aeronet_data"
version1 = "v3"
product1 = "AOD15=1"
avg1 = "AVG=10"
start_date = datetime(2025, 2, 1)
end_date = datetime(2025, 7, 31)

# Path to site list file
sites_file = "aeronet_sites.txt"

if __name__ == "__main__":
    # Read task ID from SLURM
    task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))  # Default task ID is 0
    
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