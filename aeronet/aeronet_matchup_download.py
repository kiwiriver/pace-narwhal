import os
import requests
import csv
import glob
import shutil
from urllib.parse import urlparse
from io import StringIO
import pandas as pd
import earthaccess
from matplotlib import rcParams
from datetime import datetime, timedelta
from tools.detection_util import setup_data
from tools.detection_download import download_l2_cloud, download_l2_web

def get_aeronet_file(path, aeronet_url):
    """
    Check if file exists in folder; if not, download from url or copy from path and save.
    Returns the DataFrame read from the file.
    
    Parameters:
    folder: str - Destination folder path
    url: str - Either a URL to download from or a local file path to copy from
    
    Returns:
    pandas.DataFrame - DataFrame read from the file
    """

    print("input url:", aeronet_url)
    def is_url(string):
        """Check if string is a valid URL"""
        try:
            result = urlparse(string)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    if not os.path.isfile(path):
        if is_url(aeronet_url):
            print(f"File not found at {path}. Downloading from {aeronet_url}")
            # Download and store as CSV file
            response = requests.get(aeronet_url)
            response.raise_for_status()
            # Process the text as in your original function
            lines = response.text.strip().split('\n')
            lines = lines[1:]  # Skip first line
            csv_text = "\n".join(lines)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(csv_text)
        else:
            # Assume it's a local path
            if os.path.isfile(aeronet_url):
                print(f"File not found at {path}. Copying from local path {aeronet_url}")
                shutil.copy2(aeronet_url, path)
            else:
                raise ValueError(f"Invalid input: '{aeronet_url}' is neither a valid URL nor an existing file path")
    else:
        print(f"File found at {path}. Using local copy.")
    
    # Read and return DataFrame
    aeronet_list_df1=pd.read_csv(path)
    return aeronet_list_df1

def process_local_nc_files(tspan, l2_data_folder, product, path1=None):
    """
    Process local PACE NetCDF files by checking timestamps in filenames
    and copying files within the specified time range to the l2_path.
    
    Parameters:
    -----------
    tspan : list
        Time span as [start_date, end_date] in 'YYYYMMDD' format
    l2_data_folder : str
        Path to the folder containing local L2 data files
    product : str
        Product type ('harp2_fastmapol', 'spexone_fastmapol', 'spexone_remotap')
    path1 : str, optional
        Output path for selected files (if None, uses the path from setup_data)
    
    Returns:
    --------
    list : copied_files
        List of paths to copied files
    """
    # Product mapping
    if product == 'harp2_fastmapol':
        sensor = "PACE_HARP2"
        suite2 = "MAPOL_OCEAN"
    elif product == 'spexone_fastmapol':
        sensor = "PACE_SPEXONE"
        suite2 = "MAPOL_OCEAN"
    elif product == 'spexone_remotap':
        sensor = "PACE_SPEXONE"
        suite2 = "RTAP_OC"
    else:
        print(f"{product} not available")
        return []
    
    # Setup output directories using the existing setup_data function
    day1 = f"{tspan[0]}_{tspan[1]}"
    l2_path, l1c_path, plot_path, html_path = setup_data(tspan, sensor=sensor, suite=suite2, path1=path1)
    
    # Check if source folder exists
    if not os.path.exists(l2_data_folder):
        print(f"Source folder not found: {l2_data_folder}")
        return []
    
    # Convert tspan to datetime objects for comparison
    start_date = datetime.strptime(tspan[0], '%Y-%m-%d')
    end_date = datetime.strptime(tspan[1], '%Y-%m-%d')
    
    # Find all NetCDF files in the data folder
    nc_files = glob.glob(os.path.join(l2_data_folder, "*.nc"))
    
    print(f"Found {len(nc_files)} nc files in {l2_data_folder}")
    
    copied_files = []
    
    for nc_file in nc_files:
        try:
            # Extract timestamp from filename
            # Format: PACE_SPEXONE.20240306T184049.L2.MAPOL_OCEAN.V3_0.nc
            filename = os.path.basename(nc_file)
            
            # Extract date part using a simple split
            parts = filename.split('.')
            if len(parts) >= 2:
                timestamp_str = parts[1]  # e.g., "20240306T184049"
                date_part = timestamp_str.split('T')[0]  # e.g., "20240306"

                #print(date_part)
                
                # Convert to datetime
                file_date = datetime.strptime(date_part, '%Y%m%d')

                #print(start_date , file_date, end_date)
                # Check if file date is within the specified range
                if start_date <= file_date <= end_date:
                    # Copy file to L2 directory
                    dest_file = os.path.join(l2_path, filename)
                    shutil.copy2(nc_file, dest_file)
                    copied_files.append(dest_file)
                    print(f"Copied: {filename} -> {l2_path}")
        except Exception as e:
            print(f"Error processing {nc_file}: {str(e)}")
            continue
    
    print(f"Successfully copied {len(copied_files)} files to {l2_path}")
    
    return l2_path, l1c_path, plot_path, html_path


def get_pace_data_info(product):
    """
    get pace data info
    """
    
    if(product=='harp2_fastmapol'):
        outputfile_header='harp2_fastmapol_'
        product_info_nrt={"short_name": "PACE_HARP2_L2_MAPOL_OCEAN_NRT", "sensor_id": 48, "dtid":1546, \
                             "sensor":"PACE_HARP2","suite1":"L1C.V3.5km", "suite2":"L2.MAPOL_OCEAN.V3.0.NRT"}
        product_info_refined={"short_name": "PACE_HARP2_L2_MAPOL_OCEAN", "sensor_id": 48, "dtid":1547, \
                              "sensor":"PACE_HARP2", "suite1":"L1C.V3.5km", "suite2":"L2.MAPOL_OCEAN.V3.0"}
    elif(product=='spexone_fastmapol'):
        outputfile_header='spexone_fastmapol_'
        product_info_nrt={"short_name": "PACE_SPEXONE_L2_MAPOL_OCEAN_NRT", "sensor_id": 41, "dtid":1970, \
                             "sensor":"PACE_SPEXONE","suite1":"L1C.V3.5km", "suite2":"L2.MAPOL_OCEAN.V3.0.NRT"}
        product_info_refined={"short_name": "PACE_SPEXONE_L2_MAPOL_OCEAN", "sensor_id": 41, "dtid":1971, \
                              "sensor":"PACE_SPEXONE", "suite1":"L1C.V3.5km", "suite2":"L2.MAPOL_OCEAN.V3.0"}
    
    elif(product=='spexone_remotap'):
        outputfile_header='spexone_remotap_'
        product_info_nrt={"short_name": "PACE_SPEXONE_L2_AER_RTAPOCEAN_NRT", "sensor_id": 41, "dtid":1350, \
                             "sensor":"PACE_SPEXONE","suite1":"L1C.V3.5km", "suite2":"L2.RTAP_OC.V3.0.NRT"}
        product_info_refined={"short_name": "PACE_SPEXONE_L2_AER_RTAPOCEAN", "sensor_id": 41, "dtid":1420, \
                              "sensor":"PACE_SPEXONE", "suite1":"L1C.V3.5km", "suite2":"RTAP_OC.V3.0"}
    else:
        print(product, "not available")
        outputfile_header=None
        product_info_nrt={}
        product_info_refined={}
        
    return outputfile_header, product_info_nrt, product_info_refined

def download_pace_data(tspan, product, appkey, api_key, path1='./pace_tmp/', \
                       flag_earthdata_cloud = False):
    #setup_data(tspan, sensor='PACE_HARP2', suite='MAPOL_OCEAN.V3.0', path1='./pace_tmp/')
    
    outputfile_header, product_info_nrt, product_info_refined = get_pace_data_info(product)
    
    if(flag_earthdata_cloud):
        auth = earthaccess.login(persist=True)
    
        
    # Change default font to something available
    rcParams['font.family'] = 'serif' 
    rcParams['font.size'] = '12' 
    
    day1 = tspan[0]+'_'+tspan[1]
    
    try:
        short_name=product_info_refined["short_name"]
        sensor_id=product_info_refined["sensor_id"]
        dtid=product_info_refined["dtid"]
        sensor =product_info_refined["sensor"]
        suite1 =product_info_refined["suite1"]
        suite2 = product_info_refined["suite2"]
        filelist_name=sensor+'_'+suite2+'_'+day1+'_filelist.txt'

        
        l2_path, l1c_path, plot_path, html_path = setup_data(tspan, sensor=sensor, suite=suite2, path1=path1)

        #print(sensor, suite1, suite2)
        #print(l2_path)
        
        if(flag_earthdata_cloud):
            filelist_l2 = download_l2_cloud(tspan, short_name=short_name, output_folder=l2_path)
        else:
            filelist_l2 = download_l2_web(tspan, appkey, output_folder=l2_path,  \
                                          sensor_id=sensor_id, dtid=dtid, filelist_name=filelist_name)

        #print(filelist_l2)
    except:
        short_name=product_info_nrt["short_name"]
        sensor_id=product_info_nrt["sensor_id"]
        dtid=product_info_nrt["dtid"]
        sensor =product_info_nrt["sensor"]
        suite1 =product_info_nrt["suite1"]
        suite2 = product_info_nrt["suite2"]
        filelist_name=sensor+'_'+suite2+'_'+day1+'_filelist.txt'
        l2_path, l1c_path, plot_path, html_path = setup_data(tspan, sensor=sensor, suite=suite2, path1=path1)
        if(flag_earthdata_cloud):
            filelist_l2 = download_l2_cloud(tspan, short_name=short_name, output_folder=l2_path)
        else:
            filelist_l2 = download_l2_web(tspan, appkey, output_folder=l2_path,\
                                         sensor_id=sensor_id, dtid=dtid, filelist_name=filelist_name)
    return l2_path, l1c_path, plot_path, html_path