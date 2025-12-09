import os
import sys
from datetime import datetime, timedelta
from tqdm import tqdm
#modify the library path on different machine
mapol_path=os.path.expanduser('~/github/mapoltool')
sys.path.append(mapol_path)
from tools.aeronet_batch_download import download_aeronet_all  # Import the function


# Configuration settings
folder1 = "./aeronet_data"       # Base folder for downloaded data
avg1 = "AVG=10"                  # Average strategy
product1 = "product=ALL"

#for aod, sda, lwn
version1 = "v3"                  # AERONET version
#suite1 = "AOD15=1"             # Product name
#suite1 = "SDA15=1"             # Product name
suite1 = 'LWN15=1'

#for inversion suite, alm
#version1 = "inv_v3"                  # AERONET version
#suite1 = "ALM15=1"             # Product name, also need product name
#product1 = "product=ALL"

start_date = datetime(2024, 2, 1)  # Start of analysis period
end_date = datetime(2025, 9, 1)   # End of analysis period
#end_date = datetime(2024, 4, 1)   # End of analysis period

# Call the download function for the site
download_aeronet_all(folder1, version1, suite1, product1, avg1, start_date, end_date)
