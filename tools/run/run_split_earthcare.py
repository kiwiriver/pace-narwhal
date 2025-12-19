"""
download earthcare data, and save matchup to csv

"""

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

mapol_path = os.path.expanduser('/mnt/mfs/mgao1/analysis/github/pace-narwhal')
sys.path.append(mapol_path)

# Import your custom modules (preferably explicitly)
from tools.narwhal_matchup import narwhal_matchup_daily
from tools.narwhal_tools import print_threads_info, get_rules_str

from tools.validation_earthcare_matchup import run_earthcare_matchup
from tools.validation_earthcare_csv import split_earthcare_csv

val_source = 'EARTHCARE'
product1 = "spexone_fastmapol"
input_folder = "/accounts/mgao1/mfs_pace/pace/validation/val5/test0/"

tspan = ("2024-09-01", "2025-09-02")

#do it day by day
#matchup may not handle too many days together

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