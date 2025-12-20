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
from tools.aeronet_matchup_extract import subset_time_pace_aeronet
        
file1 = '/mnt/mfs/mgao1/analysis/github/pace-narwhal/test/test0/spexone_fastmapol/pace_aeronet_oc_c5.0_r10_h2.0_chi22.0_nvref120_nvdolp120_qf5/daily/data_l2/PACE_SPEXONE_L2.MAPOL_OCEAN.V3.0_2024-09-06_2024-09-06/PACE_SPEXONE.20240906T235839.L2.MAPOL_OCEAN.V3_0.nc'
print("***nc path:", file1)
check_netcdf_file(file1)