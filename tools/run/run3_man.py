"""
We can run this file periodically, maybe monthly etc, no need to run daily
since the cruite is not as regular as the AERONET 
Meng Gao
Oct 21, 2025

"""

import os
import numpy as np
import sys

mapol_path=os.path.expanduser('~/github/mapoltool')
sys.path.append(mapol_path)
from tools.aeronet_batch_man import *

print("========download man data===========")
download_dir ="/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data/MAN/"
url = "https://aeronet.gsfc.nasa.gov/new_web/All_MAN_Data_V3.tar.gz"
download_and_extract_with_date(url, download_dir)

### specify data range #######
suite1='all_points'
level1='15'
year1='2[4-9]'
pattern1 = r'.*' + year1 + r'.*' + suite1 + r'.*' + level1 + r'$'

input_folder_base='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data/'
output_folder_base = '/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data/'
output_folder2_base = '/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data_split/'
print("======== prepare aod data===========")
input_folder = input_folder_base+'/MAN/AOD/'    # Replace with your actual input folder
output_folder = output_folder_base+'/MAN_AOD15/'      # Replace with your actual output folder
## for data split
input_folder2 = output_folder
output_folder2= output_folder2_base+'/MAN_AOD15/'
prepare_man_data(input_folder, output_folder, input_folder2, output_folder2, \
                     pattern1=pattern1)

print("======== prepare sda data===========")
input_folder = input_folder_base+'/MAN/SDA/'
output_folder = output_folder_base+'/MAN_SDA15/'
## for data split
input_folder2 = output_folder
output_folder2 = output_folder2_base+'/MAN_SDA15/'
#Oceania_24_0_all_points.ONEILL_15
prepare_man_data(input_folder, output_folder, input_folder2, output_folder2, \
                     pattern1=pattern1)
