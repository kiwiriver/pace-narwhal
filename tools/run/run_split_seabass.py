import os
import sys
from datetime import datetime, timedelta
from tqdm import tqdm
#modify the library path on different machine
mapol_path = os.path.expanduser('/mnt/mfs/mgao1/analysis/github/pace-narwhal/')
sys.path.append(mapol_path)

import tools.SB_support as sb
from tools.narwhal_split_seabass import *
from tools.narwhal_split_aeronet import *

path1='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data/SEABASS/AOC_v4_l15_202512/'
filev=glob.glob(path1+'*.env')

path0='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data_split/'
overwrite=True

output_dir = f"{path0}/SEABASS/"
os.makedirs(output_dir, exist_ok=True)

for file1 in filev:
    print(file1)
    
    data1=sb.readSB(filename=file1, no_warn=True)
    pd1=pd.DataFrame(data1.data)
    
    
    site_name = "AERONET_Site"
    datetime_name = 'datetime'
    date_name = "Date(dd:mm:yyyy)"
    time_name = 'Time(hh:mm:ss)'
    lat_name = 'Site_Latitude(Degrees)'
    lon_name = 'Site_Longitude(Degrees)'
    columns_to_move = [site_name, datetime_name, date_name,time_name, lat_name, lon_name]
    
    pd1[datetime_name]=data1.fd_datetime()
    pd1[site_name] = get_site_name(file1)
    pd1[lat_name]=pd1['lat']
    pd1[lon_name]=pd1['lon']
    pd1 = create_time_and_date_columns(pd1, date_name=date_name, time_name=time_name)
    #pd1 = add_wv_to_wavelength_columns(pd1)
    pd1 = move_columns_to_front(pd1,columns_to_move=columns_to_move)

    tmpfile = 'tmp.csv'
    pd1.to_csv(tmpfile, index=False)
    input_file = tmpfile

    # Dynamically assign the key column names for site and date from the file header

    
    # Prepare input file and column names for chunk processing
    column_names = pd1.keys()
    skiprows = 0
    
    # Define chunk size for processing large files
    #chunk_size = 10**3  # Adjust chunk size for memory efficiency (e.g., 1000 rows per chunk)
    chunk_size = 10**4  # Adjust chunk size for memory efficiency (e.g., 1000 rows per chunk)
    
    # **Call Data Processing Function**
    split_aeronet_data(
        input_file=input_file,
        output_dir=output_dir,
        column_names=column_names,
        skiprows=skiprows,
        site_name=site_name,
        date_name=date_name,
        chunk_size=chunk_size,
        overwrite=overwrite
    )
    
    remove_duplicates_in_csv_files(
        output_dir=output_dir,
        key_columns=[site_name, date_name, time_name]
    )

