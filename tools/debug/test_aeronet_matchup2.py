import os
import re
import pickle
import glob
import shutil
import sys
import traceback

import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from tqdm import tqdm 
from datetime import datetime
import matplotlib.pyplot as plt

mapol_path = os.path.expanduser('/mnt/mfs/mgao1/analysis/github/pace-narwhal/')
sys.path.append(mapol_path)
from tools.aeronet_matchup_search import check_netcdf_file

from tools.aeronet_matchup_extract import subset_time_pace_aeronet, subset_loc_pace_data, \
                                            prepare_date, prepare_vars
from tools.narwhal_matchup_plot import plot_corr_one_density_kde, plot_four_csv_maps
from tools.narwhal_tools import find_closest_wavelength_vars
from tools.aeronet_matchup_man import get_man_all

from tools.aeronet_matchup_download import get_aeronet_file, process_local_nc_files
from tools.narwhal_pace import download_pace_data
from tools.aeronet_matchup_search import aeronet_search, plot_search
from tools.aeronet_matchup_format import clean_pace_data

from tools.narwhal_matchup_html_suite import create_html_with_embedded_images
from tools.narwhal_matchup_order import get_image_files,ordered_image_list
from tools.narwhal_tools import get_rules_str, get_filter_rules, clean_value

from tools.aeronet_oc import get_f0_tsis

val_source1='AERONET_OC'
val_path1='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data_split/'
loc_suite1='LWN15'
loc_search_path = os.path.join(val_path1, loc_suite1)
print(loc_search_path)
tspan=('2024-09-06', '2024-09-06')

aeronet_list_df1 = get_man_all(loc_search_path, tspan, flag_man=False, flag_list=True)

l2_path1 ='/mnt/mfs/mgao1/analysis/github/pace-narwhal/test/test0/spexone_fastmapol/pace_aeronet_oc_c5.0_r10_h2.0_chi22.0_nvref120_nvdolp120_qf5/daily/data_l2/PACE_SPEXONE_L2.MAPOL_OCEAN.V3.0_2024-09-06_2024-09-06/'
filev = glob.glob(os.path.join(l2_path1,'*.nc'))
filev = [filev[0]]
print(filev)

search_center_radius = 5
len(filev)

##############

        
file1 = '/mnt/mfs/mgao1/analysis/github/pace-narwhal/test/test0/spexone_fastmapol/pace_aeronet_oc_c5.0_r10_h2.0_chi22.0_nvref120_nvdolp120_qf5/daily/data_l2/PACE_SPEXONE_L2.MAPOL_OCEAN.V3.0_2024-09-06_2024-09-06/PACE_SPEXONE.20240906T235839.L2.MAPOL_OCEAN.V3_0.nc'
print("***nc path:", file1)
#check_netcdf_file(file1)

##############
indexvv, boundingboxv = aeronet_search(aeronet_list_df1, filev, search_center_radius=search_center_radius)
