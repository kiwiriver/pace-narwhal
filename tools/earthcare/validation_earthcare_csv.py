import xarray as xr
import pandas as pd
import os
import re
import numpy as np
from datetime import datetime

import os
import numpy as np
import matplotlib.pyplot as plt
import glob
import xarray as xr
import sys

from tools.validation_earthcare_plot import *
from tools.validation_earthcare_matchup import parse_time
from tools.detection_download import format_tspan

def split_earthcare_csv(earthcare_save_folder, output_file_path, tspan=None, \
                        bbox=(-180, -80, 180, 80), filter_by_time_bbox = False, \
                       csv_filename='EarthCARE.csv'):
    """
    BBOX = (-180, -80, 180, 80)  # W, S, E, N order (Southern hemisphere, non-polar)
    output_file_path='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data_split/ATL_ALD_2A/'

    filter_by_time_bbox will determine, whether to filter the data according to tspan, and bbox, 
    aotherwise, using all files in that folder
    """

    if(tspan is not None):
        tspan_web = format_tspan(tspan)
        time_start, time_end = parse_time(tspan_web)
    else:
        #reset to false if tspan is not available
        filter_by_time_bbox=False
    
    path1=earthcare_save_folder
    path3=os.path.join(path1, 'EarthCARE/ATL_ALD_2A/')
    file3v=glob.glob(path3+'*h5')
    print("total file found:", len(file3v))

    found_filev=[]
    nv=[]
    datev=[]
    output_pathv=[]
    for file3 in file3v:
        print('---------------')
        print(file3)
        input_file = file3
        df = process_earthcare_data(input_file)
        #if filter by location and time
        if(filter_by_time_bbox):
            df = filter_data_by_location_time(df, time_start, time_end, bbox)
            
        if df is not None and len(df) > 0:
            n1=len(df)
            output_path = save_dataframe_to_csv(df, input_file, \
                            output_file_path=output_file_path, csv_filename=csv_filename)
            output_pathv.append(output_path)
            found_filev.append(input_file)
            nv.append(n1)
            datev.append(extract_date_from_filename(input_file))
    
    # plot
    #include all the csv in all available date
    #file4v=sorted(glob.glob(os.path.join(output_file_path,'*/*.csv')))
    #only plot the data processed above
    file4v=output_pathv
    print("total number of files:", len(file4v))
    outfile = os.path.join(output_file_path, f"plot/pace_earthcare_matchup_{tspan[0]}-{tspan[1]}.png")
    fig, ax = plot_multiple_files_cartopy(file4v, outfile=outfile)

    #plot every file separately
    #for i1 in range(len(file4v)):
    #    filevt=file4v[i1:i1+1]
    #    fig, ax = plot_multiple_files_cartopy(filevt)
    #    plt.show()
    
def process_earthcare_data(nc_path):
    """
    Process EarthCARE data and create DataFrame:
    - Read specific variables from an xarray dataset
    - Extract first 3 aerosol layers into separate columns
    - Convert aerosol layer heights from meters to kilometers
    - Only include data where aerosol_layer_number > 0
    - Add new fields (campaign, Date, Time)
    
    Parameters:
    -----------
    nc_path : str
        Path to the input file
    
    Returns:
    --------
    df : pandas.DataFrame
        The processed dataframe (None if no valid data)
    """
    # Read the dataset
    #df3 = xr.open_dataset(nc_path, group='ScienceData')
    datatree = xr.open_datatree(nc_path, decode_timedelta=False)
    df3 = xr.merge(datatree.to_dict().values())
    
    # Check for expected variables
    basic_vars = ['time', 'latitude', 'longitude', 'aerosol_layer_number']
    layer_vars = ['aerosol_layer_base', 'aerosol_layer_top', 'aerosol_layer_optical_thickness_355nm']
    
    # Variables that need unit conversion from meters to kilometers
    height_vars = ['aerosol_layer_base', 'aerosol_layer_top']
    
    all_vars = basic_vars + layer_vars
    missing_vars = [var for var in all_vars if var not in df3.variables]
    
    if missing_vars:
        print(f"Warning: Missing variables in dataset: {missing_vars}")
    
    # Start with basic variables
    basic_keys_available = [key for key in basic_vars if key in df3.variables]
    
    if basic_keys_available:
        basic_df = df3[basic_keys_available].to_dataframe().reset_index()
    else:
        raise ValueError("No basic variables (time, lat, lon) found in dataset!")
        
    # Filter to only include records where aerosol_layer_number > 0
    if 'aerosol_layer_number' in basic_df.columns:
        print(f"Original data points: {len(basic_df)}")
        basic_df = basic_df[basic_df['aerosol_layer_number'] > 0]
        print(f"Data points with layers > 0: {len(basic_df)}")
        
        if len(basic_df) == 0:
            print("Warning: No data points with aerosol layers > 0!")
            return None
    else:
        print("Warning: aerosol_layer_number not found, cannot filter")
    
    # Initialize result DataFrame with filtered basic variables
    result_df = basic_df
    
    # Handle layer variables with explicit extraction of first 3 layers
    for var_name in layer_vars:
        if var_name not in df3.variables:
            continue
            
        # Get variable and check its structure
        var = df3[var_name]
        
        # Find the layer dimension
        if len(var.dims) < 2:
            print(f"Warning: {var_name} does not have enough dimensions for layers")
            continue
        
        # Assuming layer is second dimension (e.g., [time, layer])
        time_dim = var.dims[0]  # Usually 'time' or similar
        layer_dim = var.dims[1]  # The layer dimension
        
        # Get number of layers
        n_layers = var.sizes[layer_dim]
        max_layers = min(3, n_layers)
        
        # Extract layers
        for i in range(max_layers):
            # Extract this layer and convert to a Series
            layer_values = var.isel({layer_dim: i}).to_dataframe()[var_name]
            
            # Reset index to match with our filtered dataframe
            layer_df = layer_values.reset_index()
            
            # Create column name with layer index
            col_name = f"{var_name}_n{i}"
            
            # Merge with result dataframe, keeping only the filtered rows
            merge_cols = [col for col in layer_df.columns if col in result_df.columns]
            result_df = pd.merge(result_df, layer_df[merge_cols + [var_name]], on=merge_cols, how='left')
            result_df = result_df.rename(columns={var_name: col_name})
            
            # Convert height variables from meters to kilometers
            if var_name in height_vars:
                print(f"Converting {col_name} from meters to kilometers")
                # Convert from meters to kilometers by dividing by 1000
                result_df[col_name] = result_df[col_name] / 1000.0
                
                # Optional: Print conversion statistics
                if not result_df[col_name].isna().all():
                    min_height = result_df[col_name].min()
                    max_height = result_df[col_name].max()
                    print(f"  {col_name}: Range {min_height:.3f} - {max_height:.3f} km")
            
    # Add campaign field and other mappings
    result_df['campaign'] = 'EarthCARE'
    result_df['AERONET_Site'] = 'EarthCARE'
    result_df['Latitude'] = result_df['latitude']
    result_df['Longitude'] = result_df['longitude']
    
    # Process time column
    def format_time(time_val):
        try:
            dt = pd.to_datetime(time_val)
            return dt.strftime('%d:%m:%Y'), dt.strftime('%H:%M:%S')
        except:
            return '', ''
    
    # Apply time formatting
    time_formatted = result_df['time'].apply(lambda x: pd.Series(format_time(x)))
    result_df['Date(dd:mm:yyyy)'] = time_formatted[0]
    result_df['Time(hh:mm:ss)'] = time_formatted[1]
    
    print(f"Processed DataFrame shape: {result_df.shape}")
    print(f"Column count: {len(result_df.columns)}")
    
    # Print layer columns created
    layer_cols = [col for col in result_df.columns if any(var in col for var in layer_vars)]
    print(f"Layer columns created: {layer_cols}")
    
    # Print height conversion summary
    height_cols = [col for col in result_df.columns if any(hvar in col for hvar in height_vars)]
    if height_cols:
        print(f"Height columns (converted to km): {height_cols}")
    
    return result_df

def filter_data_by_location_time(df, time_start, time_end, bbox):
    """
    Filter DataFrame by time range and geographic bounding box.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input DataFrame with 'time', 'latitude', 'longitude' columns
    time_start : datetime
        Start time for filtering
    time_end : datetime
        End time for filtering
    bbox : tuple
        Bounding box in format (W, S, E, N) - (min_lon, min_lat, max_lon, max_lat)
    
    Returns:
    --------
    df_filtered : pandas.DataFrame
        Filtered DataFrame
    """
    if df is None or df.empty:
        print("Warning: Input DataFrame is empty or None")
        return None
    
    print(f"Input DataFrame shape: {df.shape}")
    
    # Convert time column to datetime if it's not already
    df_filtered = df.copy()
    df_filtered['datetime'] = pd.to_datetime(df_filtered['time'])
    
    # Filter by time range
    time_mask = (df_filtered['datetime'] >= time_start) & (df_filtered['datetime'] <= time_end)
    df_filtered = df_filtered[time_mask]
    print(f"****After time filtering ({time_start} to {time_end}): {len(df_filtered)} points")
    
    if len(df_filtered) == 0:
        print("Warning: No data points within specified time range")
        return None
    
    # Filter by bounding box (W, S, E, N)
    min_lon, min_lat, max_lon, max_lat = bbox
    
    # Handle longitude wrapping if needed
    if min_lon <= max_lon:
        lon_mask = (df_filtered['longitude'] >= min_lon) & (df_filtered['longitude'] <= max_lon)
    else:
        # Handle case where bbox crosses 180/-180 boundary
        lon_mask = (df_filtered['longitude'] >= min_lon) | (df_filtered['longitude'] <= max_lon)
    
    lat_mask = (df_filtered['latitude'] >= min_lat) & (df_filtered['latitude'] <= max_lat)
    
    bbox_mask = lon_mask & lat_mask
    df_filtered = df_filtered[bbox_mask]
    
    print(f"After bounding box filtering {bbox}: {len(df_filtered)} points")
    
    if len(df_filtered) == 0:
        print("Warning: No data points within specified geographic bounds")
        return None
    
    # Drop the temporary datetime column
    df_filtered = df_filtered.drop('datetime', axis=1)
    
    return df_filtered

def save_dataframe_to_csv(df, input_file, output_file_path='./', csv_filename='EarthCARE.csv'):
    """
    Save DataFrame to CSV in a folder derived from the original filename.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame to save
    file_path : str
        Original file path to extract date for folder naming
    csv_filename : str, optional
        Name of the CSV file (default: 'ATL_ALD_2A.csv')
    
    Returns:
    --------
    output_path : str
        Full path where the CSV was saved
    """
    if df is None or df.empty:
        print("Warning: Cannot save empty DataFrame")
        return None
    
    # Extract folder name from filename
    folder_name = os.path.join(output_file_path, extract_date_from_filename(input_file))
    print(f"Extracted folder name: {folder_name}")
    
    # Create folder and save CSV
    os.makedirs(folder_name, exist_ok=True)
    output_path = os.path.join(folder_name, csv_filename)
    
    
    df.to_csv(output_path, index=False)
    
    print(f"Data saved to: {output_path}")
    print(f"Final dataset shape: {df.shape}")
    
    return output_path

def extract_date_from_filename(file_path):
    """Extract date from filename pattern like EXBA_ATL_ALD_2A_20240902T062114Z_"""
    filename = os.path.basename(file_path)
    # Look for pattern: 8 digits followed by T (YYYYMMDDTHHMMSSZ)
    match = re.search(r'(\d{8})T\d{6}Z', filename)
    if match:
        return match.group(1)  # Returns YYYYMMDD format
    else:
        # Fallback: try to extract any 8-digit sequence that looks like a date
        match = re.search(r'(20\d{6})', filename)
        if match:
            return match.group(1)
        else:
            return datetime.now().strftime('%Y%m%d')

