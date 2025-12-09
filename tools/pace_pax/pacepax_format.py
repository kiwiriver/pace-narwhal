import os
import re
import shutil
import glob
from pathlib import Path

import xarray as xr
import pandas as pd
import numpy as np
from tools.pacepax_tools import calculate_aerosol_layer_properties_integrated_vectorized

def format_hsrl2_data_for_val(df, \
      aeronet_lon_var='Longitude', \
      aeronet_lat_var='Latitude', \
      aeronet_site_var='AERONET_Site',\
      aeronet_date_var='Date(dd:mm:yyyy)', \
      aeronet_time_var='Time(hh:mm:ss)'):

    """
    'lat', 'lon', 'time', campaign="PACE_PAX"
    aeronet: format
      aeronet_site_var='AERONET_Site'
      aeronet_lon_var='Longitude(decimal_degrees)', \
      aeronet_lat_var='Latitude(decimal_degrees)', \

    man:
        aeronet_site_var='AERONET_Site'
        'Site_Name' will be created by adding p0
        aeronet_lon_var='Longitude', \
        aeronet_lat_var='Latitude', \  
    """
    df[aeronet_site_var] = df['campaign']
    df[aeronet_lon_var] = df['lon']
    df[aeronet_lat_var] = df['lat']

    # Convert to datetime
    df['timestamp'] = pd.to_datetime(df['time'],format='%Y-%m-%d %H:%M:%S.%f')
    # Create your desired columns
    df[aeronet_date_var] = df['timestamp'].dt.strftime('%d:%m:%Y')
    df[aeronet_time_var] = df['timestamp'].dt.strftime('%H:%M:%S')
    #print(df[aeronet_date_var])
    #print(df[aeronet_time_var])

    return df