import earthaccess
import requests
import os

import sys
import time
import numpy as np
import xarray as xr
import pandas as pd
import json
import argparse
import pickle
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from pathlib import Path
from matplotlib import rcParams

# Add the path of the tools
#mapol_path = os.path.expanduser('~/github/mapoltool')
mapol_path = os.path.expanduser('/mnt/mfs/mgao1/analysis/github/mapoltool')
sys.path.append(mapol_path)

# Import your custom modules (preferably explicitly)
from tools.aeronet_matchup_summary import aeronet_matchup_summary
from tools.narwhal_tools import print_threads_info, get_rules_str

from tools.validation_earthcare_matchup import run_earthcare_matchup
from tools.validation_earthcare_csv import split_earthcare_csv

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def main():
    """
    search_center_radius = 5 #km #center distance
    search_grid_delta=2 #number of pixels around center
    delta_hour=1  #hours for aeronet colocation
    #first round mathchups to find center
    #current, center 5km, 2pixel, 1hour
    #plan: 5km, 10pixel, 2hour
        
    """
    print_threads_info()
    
    parser = argparse.ArgumentParser(description="Run PACE L2 daily processing script.")
    parser.add_argument("--val_source", type=str, default='AERONET', help="AERONET, AERONET_OC, MAN, etc")
    parser.add_argument("--input_folder", type=str, default=".", \
                        help="Path to the input folder containing data files (default: current directory).")
    parser.add_argument("--l2_data_folder", type=str, default=None, 
               help="Path to data folder (default: None), if available, search this folder")
    parser.add_argument("--share_dir_base", type=str, default="/mnt/mfs/FILESHARE/meng_gao/pace/validation", 
               help="Path to save in fileshare")
    parser.add_argument("--val_url", type=str, default="https://aeronet.gsfc.nasa.gov/aeronet_locations_v3921.txt", 
               help="Path to data folder (default: None), if available, search this folder")

    parser.add_argument("--val_path", type=str, default='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data_split/', 
               help="Path to data folder (default: None), if available, search this folder")
    
    parser.add_argument("--loc_suite", type=str, default="AOD15", 
               help="if search loc for AERONET, use AOD15 in default, for MAN: MAN_AOD15_series")
    parser.add_argument("--f0_file", type=str, default='f0_tsis_aeronet_oc_bw10.csv', 
               help="located at the data folder")
    
    parser.add_argument("--tspan_start", type=str, help="Start date of the time span (YYYY-MM-DD).")
    parser.add_argument("--tspan_end", type=str, help="End date of the time span (YYYY-MM-DD).")
    parser.add_argument("--product", type=str, help="product: harp2_fastmapol, ...")
    
    #parser.add_argument("--search_center_radius", type=float, default=5, help="center radius between two pixels, ...")
    #parser.add_argument("--search_grid_delta", type=int, default=5, help="product: aod, ...")
    #parser.add_argument("--delta_hour", type=float, default=2, help="product: aod, ...")
    
    parser.add_argument('--all_rules', type=str, \
      default='{"search_center_radius": 5, "search_grid_delta":5, "delta_hour":2, "chi2":[0,2], "nv_ref":[120,170], "nv_dolp":[120,170], "quality_flag":[0,5]}', \
                        help='Filter rule as JSON string')

    parser.add_argument("--no_rm", action="store_true",
                       help="Do NOT remove files after finish (default: remove files)")
    parser.add_argument("--no_cloud", action="store_true",
                       help="Do NOT use Earthdata cloud (default: use cloud)")
    parser.add_argument("--save_subset_loc_path", type=str, default=None, help="Default do not save subset, If path is given, save")
    
    
    args = parser.parse_args()
    l2_data_folder=args.l2_data_folder
    share_dir_base = args.share_dir_base
    val_url=args.val_url.lower()
    if val_url in ['none', 'null']:
        val_url = None
        print("no input val url, search file")
    
    val_path1=args.val_path
    input_folder = args.input_folder
    tspan_start = args.tspan_start 
    tspan_end = args.tspan_end
    tspan = (tspan_start, tspan_end)
    product1 = args.product
    val_source = args.val_source
    print("val_source:", val_source)
    
    if(val_source=='AERONET_OC'):
        print("===read f0 is AERONET_OC===")
        f0_file = args.f0_file
        f0_file = os.path.join(mapol_path, "data", f0_file)
        print("****Found f0_file:", f0_file)
        df0=pd.read_csv(f0_file,index_col=0)
    else:
        df0=None

    loc_suite1 = args.loc_suite
    print(f"***Search {val_source} data and timespan: ", val_path1, tspan)
        
    flag_rm = not args.no_rm  # True by default, False if --no_rm is specified
    flag_earthdata_cloud = not args.no_cloud  # True by default, False if --no_cloud is specified
    
    print(args.all_rules)
    all_rules = json.loads(args.all_rules)
    all_rules_str = get_rules_str(all_rules)
    
    save_subset_loc_path=args.save_subset_loc_path
    if(save_subset_loc_path):
        os.makedirs(save_subset_loc_path, exist_ok=True)


    ###########################
    print_threads_info()
    
    ####DO NOT SHARE###########
    appkey=<appkey>
    api_key=<api_key>

    save_path1 = os.path.join(input_folder,product1, f"pace_{val_source.lower()}_{all_rules_str}")
    print("   ***path to save data:", save_path1)
    
    #######################################################################################################
    #for earchcare data, download data, and create csv in split folder
    #need a few new packages to be installed
    #also the pace l2 files are also downloaded already
    if(val_source.upper()=='EARTHCARE'):
        #product1 = "spexone_fastmapol"  # or whatever product name you use
        #input_folder = "/accounts/mgao1/mfs_pace/pace/validation/val5/test0/"
        #tspan = ("2024-09-01", "2024-09-02")
        
        bbox = (-180, 0, 180, 80)
        token_path='./earthcare_credentials_v20251205.txt'
        shortnames_earthcare1="ATL_ALD_2A"
    
        matchups, earthcare_save_folder = run_earthcare_matchup(
            product=product1,
            input_folder=input_folder,
            tspan=tspan,
            bbox=bbox,
            limit=50000,
            shortnames_earthcare1=shortnames_earthcare1,
            token_path=token_path,
            verbose=True
        )

        #save the csv file here
        if(len(matchups)>0):
            folder1='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data_split/'
            output_file_path=os.path.join(folder1, 'ATL_ALD_2A')
            print("   ***split earth data into csv into:", output_file_path)
            os.makedirs(output_file_path, exist_ok=True)
            
            split_earthcare_csv(earthcare_save_folder, output_file_path, tspan=tspan, \
                                    bbox=(-180, -80, 180, 80), filter_by_time_bbox = False, \
                                   csv_filename='EarthCARE.csv')
        else:
            print("abord, not valid retrievals")
            sys.exit(1)

    #######################################################################################################
    
    #### download active aeronet site #
    matchup_save_folder = os.path.join(save_path1,'matchup')
    os.makedirs(matchup_save_folder, exist_ok=True)

    #for each date range folder, this is almost always done per day through slurm
    str2 = tspan[0]+'-'+tspan[1]
    matchup_save_folder2 = os.path.join(matchup_save_folder, str2)
    os.makedirs(matchup_save_folder2, exist_ok=True)

    #put the html here, not need to create daily folder, since the html contain time, and one html per day
    #l2 and l1 foder contains mutliple granules
    html_save_folder = os.path.join(save_path1,'html')
    os.makedirs(html_save_folder, exist_ok=True)
    
    ###################################################################################################
    t1=time.time()
    logo_path = os.path.join(mapol_path, "img", 'narwhal_logo.png')
    print("logo location:", logo_path)
    aeronet_matchup_summary(matchup_save_folder, matchup_save_folder2, html_save_folder,\
                            val_url, val_path1, loc_suite1, tspan, \
                            product1, appkey, api_key, \
                            save_path1, l2_data_folder, \
                            all_rules, \
                            save_subset_loc_path, share_dir_base,\
                            val_source=val_source, flag_rm=flag_rm, \
                            flag_earthdata_cloud=flag_earthdata_cloud, df0=df0, logo_path=logo_path)
    
    t2=time.time()
    print("===total time for processing===", t2-t1)
    
    #####################################################################################################
    
    if(flag_rm and val_source.upper()=='EARTHCARE'):
        path1 = earthcare_save_folder
        try:
            shutil.rmtree(path1)
            print(f"✅ EarthCARE Folder removed: {path1}")
        except:
            print("ready to remove, but cannot find path", path1)
            
    #####################################################################################################
    
if __name__ == '__main__':
    main()