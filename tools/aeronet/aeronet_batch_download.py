import os
from datetime import datetime, timedelta
import requests

import requests
import os
from datetime import datetime, timedelta


"""
(py3.12) mgao1@gs616-analysis703:/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/t01_aeronet_download$ curl ifconfig.me
169.154.128.87

(py3.12) [mgao@poseidon t01_aeronet_download]$ srun --partition=research --nodelist=poseidon-compute-1 curl ifconfig.me
2001:4d0:2418:128::87

The observation that the IP address is the same across different nodes when submitting jobs suggests that your SLURM cluster or network configuration uses techniques like NAT (Network Address Translation) or shared outbound IP for all nodes accessing external services. This is common in many cluster setups where multiple nodes share the same public-facing IP address.

"""

#
def download_aeronet_all(folder1, version1, suite1, product1, avg1, start_date, end_date):
    """
    if existed, abandon, to save disk and time
    aronet is very easy to timeout, try download all
    suite1: AOD15, SDA15, ALM15
    product1: product=ALL
    
    """
    # Extract the suite name before the '=' and create a folder for it
    suite_folder =folder1+ f'/{suite1.split("=")[0]}'  # Keep only the part before '='
    if not os.path.exists(suite_folder):
        os.makedirs(suite_folder)
        print(f"Created suite folder: {suite_folder}")
    


    # Determine the first day and last day 
    year1 = start_date.year
    month1 = start_date.month
    day1 = start_date.day

    # Determine the first day and last day 
    year2 = end_date.year
    month2 = end_date.month
    day2 = end_date.day
    
    # Generate the filename dynamically
    try:
        product_str=product1.split("=")[1]
        print("get product_str", product_str)
    except:
        product_str='ALL'
        print("default product_str", product_str)
    aeronet_aod_file1 = f'{suite_folder}/aeronet_{version1}_{suite1.split("=")[0]}_{product_str}_{year1}{month1:02d}{day1:02d}_{year2}{month2:02d}{day2:02d}.txt'
    
    # Check if the file already exists in the folder
    if os.path.exists(aeronet_aod_file1):
        print(f"File already exists: {aeronet_aod_file1}, skipping download.")
    else:
        # Generate the URL dynamically
        url1 = 'https://aeronet.gsfc.nasa.gov/cgi-bin/print_web_data_{}?year={}&month={}&day={}&year2={}&month2={}&day2={}&{}&{}&{}&if_no_html=1'
        url2 = url1.format(version1, year1, month1, day1, year2, month2, day2, product1, suite1, avg1)
        print(f"Requesting data from URL: {url2}")
        
        # Download the file and save it
        try:
            r = requests.get(url2)
            r.raise_for_status()  # Raise an error for failed responses
            with open(aeronet_aod_file1, 'w') as file:
                file.write(r.text)
            print(f"File saved: {aeronet_aod_file1}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download data for {year1}-{month1}: {e}")

    
def download_aeronet_per_month(folder1, version1, product1, avg1, site1, start_date, end_date):
    """
    Downloads AERONET data per month and stores it in folders.
    Skips download if file or folder already exists.
    """
    # Extract the product name before '=' and create folder for it
    product_folder = os.path.join(folder1, product1.split("=")[0])
    if not os.path.exists(product_folder):
        os.makedirs(product_folder)
        print(f"Created product folder: {product_folder}")
    
    # Create a site folder inside product folder
    site_folder = os.path.join(product_folder, site1)
    if not os.path.exists(site_folder):
        os.makedirs(site_folder)
        print(f"Created site folder: {site_folder}")
    
    current_date = start_date
    while current_date <= end_date:
        year1, month1, day1 = current_date.year, current_date.month, 1
        next_month = current_date.replace(day=28) + timedelta(days=4)
        last_day = next_month.replace(day=1) - timedelta(days=1)
        year2, month2, day2 = last_day.year, last_day.month, last_day.day
        
        aeronet_aod_file1 = os.path.join(
            site_folder,
            f'aeronet_{version1}_{product1.split("=")[0]}_{avg1.split("=")[0]}_{site1}_{year1}{month1:02d}{day1:02d}_{year2}{month2:02d}{day2:02d}.txt'
        )
        
        if os.path.exists(aeronet_aod_file1):
            print(f"File already exists: {aeronet_aod_file1}, skipping download.")
        else:
            url1 = 'https://aeronet.gsfc.nasa.gov/cgi-bin/print_web_data_{}?site={}&year={}&month={}&day={}&year2={}&month2={}&day2={}&{}&{}&if_no_html=1'
            url2 = url1.format(version1, site1, year1, month1, day1, year2, month2, day2, product1, avg1)
            print(f"Requesting data from URL: {url2}")
            try:
                r = requests.get(url2)
                r.raise_for_status()
                with open(aeronet_aod_file1, 'w') as file:
                    file.write(r.text)
                print(f"File saved: {aeronet_aod_file1}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download data for {site1}: {e}")
        
        current_date = current_date.replace(day=28) + timedelta(days=4)
        current_date = current_date.replace(day=1)