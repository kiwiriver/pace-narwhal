"""
aeronet: contain the relevant variable
pace: contain all l2 stuff, need aot550, and other diagnostic parameters at least

Note: since we search the aeronet sites based on AOD15 data, some sites maybe not available
for ALM/HYB, need try/exception to capture that:
"---exception countered: canot find this site:", site1

LWN is fine, which runs sepeartely.

"""
import os
import re

import numpy as np
import pandas as pd
import xarray as xr
import pickle
from tqdm import tqdm
import matplotlib.pyplot as plt
from datetime import datetime

from tools.aeronet_matchup_match import subset_pace_df, match_time_aeronet
from tools.aeronet_matchup_format import format_aeronet_df, format_pace_df, get_val_df

def subset_time_pace_aeronet(folder1, site1v, pace_df_mean_all, pace_df_std_all, wvv, all_vars,\
                       extra_vars=['chi2', 'count','nv_ref','nv_dolp', 'aeronet_lon', 'aeronet_lat', \
                                   'pace_lon','pace_lat',\
                                   'pace_loc_index_lon','pace_loc_index_lat', \
                                   'distance1_haversine','distance2_euclidean'],\
                        delta_hour=1, flag_subset_pace=True, \
                        old_start1='AOD_', old_end1='nm', new_start1='aot_wv',\
                       input_is_sda=False, val_source='AERONET', df0=None):
    """
    now search the aeronet data to match with pace, within delta_hour, for each variable
    when input_is_sda=True, use internal interpolation based on angstrom to get aod, aod_fine, aod_coarse
    val_source=MAN, combine data together
    val_source=AERONET, AERONET_OC load site by site

    Todo:
    fix: flag_format_pace, should clean up the pace data, rather using all
    but somehow failed to find matchups
    
    """
    all_aeronet_mean = []
    all_aeronet_std = []
    
    all_pace_mean = []
    all_pace_std = []
    count=0
    for site1 in site1v[:]:
        try:
        # Read aeronet/man data
            aeronet_df1, site_name = get_val_df(val_source, folder1, site1)
            
            #select relevant variables
            aeronet_df2, orig_wavelengths = format_aeronet_df(aeronet_df1, input_wavelengths=wvv,\
                                   old_start1=old_start1, old_end1=old_end1, new_start1=new_start1,\
                                                             input_is_sda=input_is_sda, \
                                                              site_name=site_name, \
                                                              df0=df0)
            
            print("**wavelength in aeronet or man:", orig_wavelengths)
            
            site_to_match = site1
    
            #with open('data.pkl', 'wb') as f:
            #    pickle.dump([pace_df_mean_all, pace_df_std_all, all_vars, extra_vars,  aeronet_df2, site_to_match, delta_hour], f)
            
            #print(pace_df_mean_all.keys())
            
            if(flag_subset_pace):
                pace_df_mean_all, pace_df_std_all = subset_pace_df(pace_df_mean_all, pace_df_std_all, \
                                                               all_vars, extra_vars)
            #print(pace_df_mean_all.keys())
            
            aeronet_df3_mean, aeronet_df3_std, pace_df_mean_all_filtered, pace_df_std_all_filtered\
                = match_time_aeronet(pace_df_mean_all, pace_df_std_all, aeronet_df2, site_to_match, delta_hour=delta_hour)
    
            #print(pace_df_mean_all_filtered.keys())
            
            # Append to lists
            all_aeronet_mean.append(aeronet_df3_mean)
            all_aeronet_std.append(aeronet_df3_std)
    
            all_pace_mean.append(pace_df_mean_all_filtered)
            all_pace_std.append(pace_df_std_all_filtered)
            count=count+1
            print(count,"===found====:", site1)
    
    
        #turn off except
        #except:
        #    print("---exception countered: canot find valid data from this site:", site1)
        except Exception as e:
            print(f"  Error processing site {site1}: {str(e)}")
            print("  Full traceback:")
            traceback.print_exc()

    try:
        # Concatenate into single DataFrames
        all_target_mean_df = pd.concat(all_aeronet_mean, ignore_index=True)
        all_target_std_df = pd.concat(all_aeronet_std, ignore_index=True)
        
        all_pace_mean_df = pd.concat(all_pace_mean, ignore_index=True)
        all_pace_std_df = pd.concat(all_pace_std, ignore_index=True)
        print("combine pd together")
    except:
        print("No AERONET and PACE matchup found")
        all_target_mean_df, all_target_std_df, all_pace_mean_df, all_pace_std_df=None, None, None, None

    return all_target_mean_df, all_target_std_df, all_pace_mean_df, all_pace_std_df


def prepare_date(aeronet_path1, suite1, date_list):
    folder1v = []  # Initialize the list to store folder paths
    
    for date in date_list:  # Loop through each date in date_list
        
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        
        formatted_date = date_obj.strftime('%Y%m%d')
        date1 = formatted_date
        print("folder for this day", date1)

        # Create the folder path
        folder1 = os.path.join(aeronet_path1, suite1, date1)
        
        # Check whether the folder exists and is not empty
        if os.path.exists(folder1):
            if os.listdir(folder1):  # Folder exists and is not empty
                print(f"Folder {folder1} is not empty - adding to list")
                folder1v.append(folder1)  # Only append if not empty
            else:  # Folder exists but is empty
                print(f"Folder {folder1} is empty - skipping")
        else:
            print(f"Folder {folder1} does not exist - skipping")

    return folder1v


def prepare_vars(wvv, current_vars=['datetime', 'site'], var_pattern="aot_wv"):
    """
    get aeronet folder for that day, 
    set all the variable names

    only check the first day
    
    """

    if wvv is not None and isinstance(wvv, (list, np.ndarray)):
        select_vars = [f'{var_pattern}{int(wv1)}' for wv1 in wvv]
    else:
        select_vars = [var_pattern]
    
    all_vars = current_vars+select_vars
    
    print(all_vars)
    
    return all_vars, select_vars
    


def subset_loc_pace_data(indexvv, filev, rules, search_grid_delta=2, save_subset_loc_path=None, decode_timedelta=False):
    """
    extract pace data using a size of pixel radius range of search_grid_delta
    return df_mean_all, df_std_all, which containthe mean and std of all the variables in the nc files

    decode_timedelta=False: handle a possible future behavior
    """

    df_mean_all = []
    df_std_all = []
    
    df_mean_all = []
    df_std_all = []
    
    for i1, timestamp in tqdm(enumerate(indexvv.keys())):
        indexv = indexvv[timestamp]
        nc_path = filev[i1]
        #print(nc_path)
        datatree = xr.open_datatree(nc_path, decode_timedelta=decode_timedelta)
        dataset = xr.merge(datatree.to_dict().values())
        
        dataset = format_pace_df(dataset, flag_aot550=True)
        
        for i1, entry in enumerate(indexv):

            pace_loc_index = entry['pace_loc_index']
            print("check entry:", i1)
            df_mean, df_std, wvv = get_mean_std_xr(dataset, pace_loc_index, search_grid_delta, \
                                                   rules, timestamp, i1, save_subset_loc_path=save_subset_loc_path)
            
            mean_row = df_mean.iloc[0].to_dict()
            std_row = df_std.iloc[0].to_dict()
            # Metadata: simple fields
            #'distance0_kdtree':dis0, 'distance1_haversine':dis1, 'distance2_euclidean':dis2
            for key in ['site_index', 'site', 'pace_date', 'distance0_kdtree', 'distance1_haversine', 'distance2_euclidean']:
                mean_row[key] = entry[key]
                std_row[key] = entry[key]
            mean_row['timestamp'] = timestamp
            std_row['timestamp'] = timestamp
            # Split location info into two columns each 
            # pace_loc_index (tuple of ints)
            mean_row['pace_loc_index_lon'] = int(entry['pace_loc_index'][0])
            mean_row['pace_loc_index_lat'] = int(entry['pace_loc_index'][1])
            std_row['pace_loc_index_lon'] = int(entry['pace_loc_index'][0])
            std_row['pace_loc_index_lat'] = int(entry['pace_loc_index'][1])
            # aeronet_loc (array-like, lon/lat convention)
            mean_row['aeronet_lon'] = float(entry['aeronet_loc'][0])
            mean_row['aeronet_lat'] = float(entry['aeronet_loc'][1])
            std_row['aeronet_lon'] = float(entry['aeronet_loc'][0])
            std_row['aeronet_lat'] = float(entry['aeronet_loc'][1])
            # pace_loc (list-like, lon/lat)
            mean_row['pace_lon'] = float(entry['pace_loc'][0])
            mean_row['pace_lat'] = float(entry['pace_loc'][1])
            std_row['pace_lon'] = float(entry['pace_loc'][0])
            std_row['pace_lat'] = float(entry['pace_loc'][1])
            # Append
            df_mean_all.append(mean_row)
            df_std_all.append(std_row)
    
    df_mean_all = pd.DataFrame(df_mean_all)
    df_std_all = pd.DataFrame(df_std_all)
    
    # Convert lists of dicts into DataFrames
    #df_mean_all = pd.DataFrame(df_mean_all)
    #df_std_all = pd.DataFrame(df_std_all)

    return df_mean_all, df_std_all, wvv

def filter_subset(subset, rules):
    """
    Filter ALL variables in the dataset based on the combined rules.
    Only keep data points where ALL rule conditions are satisfied.
    
    Parameters:
    -----------
    subset : xarray.Dataset
        Input dataset to filter
    rules : dict
        Dictionary with variable names as keys and either:
        - [min, max] ranges for range filtering
        - [value] single value for equality filtering
        Example: {'chi2':[0,2], 'nv_ref':[120,170], 'flag':[1]}
    
    Returns:
    --------
    xarray.Dataset
        Filtered dataset where all variables are masked based on combined rules
    """
    
    # First, check which rule variables exist in the dataset
    valid_rules = {}
    missing_vars = []
    
    for key, values in rules.items():
        if key in subset.data_vars:
            valid_rules[key] = values
        else:
            missing_vars.append(key)
            print(f"          ***Warning: Variable '{key}' not found in dataset, skipping rule")
    
    if not valid_rules:
        print("Warning: No valid rule variables found in dataset")
        return subset
    
    if missing_vars:
        print(f"          ***Skipped variables: {missing_vars}")
    
    # Get the first valid rule variable to establish the 2D mask shape
    first_rule_var = list(valid_rules.keys())[0]
    
    # Start with a 2D mask based on the first valid rule variable
    combined_mask = xr.ones_like(subset[first_rule_var], dtype=bool)
    valid_count = combined_mask.sum().values
    print(f"          Valid pixels before filtering: {valid_count}")

    # Apply each valid rule to build the combined 2D mask
    for key1, values in valid_rules.items():
        # Check if it's a single value or range
        if len(values) == 1:
            # Single value - equality check
            target_val = values[0]
            print(f"          Applying equality rule for {key1}: == {target_val}")
            condition = (subset[key1] == target_val)
        elif len(values) == 2:
            # Range - between min and max
            min_val, max_val = values
            print(f"         Applying range rule for {key1}: [{min_val}, {max_val}]")
            condition = (subset[key1] >= min_val) & (subset[key1] <= max_val)
        else:
            print(f"          ***Warning: Invalid rule format for '{key1}'. Expected 1 or 2 values, got {len(values)}")
            continue
            
        # Add this condition to the combined mask
        combined_mask = combined_mask & condition

    # Count True values in the mask
    valid_count = combined_mask.sum().values
    print(f"          Valid pixels after filtering: {valid_count}")

    # Apply the combined mask to ALL variables (both 2D and 3D)
    filtered_subset = subset.copy()
    for var_name in subset.data_vars:
        var_data = subset[var_name]
        
        # Check if variable is 2D or 3D and apply mask accordingly
        if var_data.ndim == 2:
            # For 2D variables, apply mask directly
            filtered_subset[var_name] = var_data.where(combined_mask, np.nan)
        elif var_data.ndim == 3:
            # For 3D variables, broadcast the 2D mask to all layers
            # Assume the last two dimensions are the spatial dimensions
            mask_3d = combined_mask.broadcast_like(var_data)
            filtered_subset[var_name] = var_data.where(mask_3d, np.nan)
        else:
            # For other dimensions, try to broadcast or keep as is
            try:
                mask_broadcast = combined_mask.broadcast_like(var_data)
                filtered_subset[var_name] = var_data.where(mask_broadcast, np.nan)
            except Exception as e:
                print(f"Warning: Could not apply mask to variable '{var_name}' with shape {var_data.shape}: {e}")
                filtered_subset[var_name] = var_data  # Keep original if masking fails
    
    return filtered_subset
                  
def get_mean_std_xr(dataset, pace_loc_index, delta, rules, timestamp, i1, save_subset_loc_path=None):
    """
    Given an xarray dataset and a location index,
    - Subsets around that location by +-delta pixels,
    - Computes nanmean and nanstd for all variables (as per your rules),
    - Returns two DataFrames: one for mean, one for std,
      and adds valid value count only for chi2 (as column 'count').

      timestamp, i1 is used to define the name for subset output
    """

    # Calculate slice boundaries, ensuring bounds
    line_start = max(pace_loc_index[0] - delta, 0)
    line_end = min(pace_loc_index[0] + delta + 1, dataset.dims['number_of_lines'])
    pix_start = max(pace_loc_index[1] - delta, 0)
    pix_end = min(pace_loc_index[1] + delta + 1, dataset.dims['pixels_per_line'])

    # Subset the dataset
    subset = dataset.isel(
        number_of_lines=slice(line_start, line_end),
        pixels_per_line=slice(pix_start, pix_end)
    )

    if(save_subset_loc_path):
        filename = os.path.join(save_subset_loc_path, f"{timestamp}_{i1}.nc")
        subset.to_netcdf(filename)
                    
    # Read wavelength and convert to integers immediately
    wvv = dataset['wavelength'].values
    wl_values = [int(round(wl)) for wl in wvv]

    mean_dict = {}
    std_dict = {}
    count = None

    print('            ---------------------------------------')
    subset = filter_subset(subset, rules)
    print('            ---------------------------------------')
    
    for var in subset.data_vars:
        try:
            da = subset[var]
            dims = da.dims
            if len(dims) > 3:
                continue  # Skip variables with more than 3 dimensions
            if 'wavelength' in dims and len(dims) == 3:
                for i, wl in enumerate(wl_values):
                    arr = da.isel(wavelength=i).values
                    var_name = f'{var}_wv{wl}'  # Use integer wavelength in name
                    mean_dict[var_name] = np.nanmean(arr)
                    std_dict[var_name] = np.nanstd(arr)
                    # Only add count for chi2
                    if var == 'chi2':
                        var_name = f'count_wv{wl}'
                        count = np.count_nonzero(~np.isnan(arr))
                        mean_dict[var_name] = count
                        std_dict[var_name] = count
            else:
                arr = da.values
                mean_dict[var] = np.nanmean(arr)
                std_dict[var] = np.nanstd(arr)
                if var == 'chi2':
                    count = np.count_nonzero(~np.isnan(arr))
                    mean_dict['count'] = count
                    std_dict['count'] = count
        except:
            print('======failed to load======', var)
    
    df_mean = pd.DataFrame([mean_dict])
    df_std = pd.DataFrame([std_dict])
    return df_mean, df_std, wvv
    