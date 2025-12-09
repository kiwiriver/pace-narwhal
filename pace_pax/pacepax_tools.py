import sys
import os
import glob
import pickle

import numpy as np
import pandas as pd
import xarray as xr

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from scipy.spatial import cKDTree
from datetime import timedelta

def get_alh(df):
    print("***get alh from backscattering****")
    aot_key = '532_extinction_from_backscatter'
    
    # Check if the key exists in the dataset
    if aot_key not in df:
        print(f"Warning: '{aot_key}' not found in dataset")
        available_keys = [k for k in df.keys() if 'extinction' in k or 'backscatter' in k]
        print(f"Available extinction/backscatter keys: {available_keys}")
        # You might want to return df unchanged or use a different key
        return df
    
    heights, aots, weighted_heights = \
        calculate_aerosol_layer_properties_integrated_vectorized(df, \
           aot_key=aot_key, z_key='z', min_aod=0.1)
    
    df['alh'] = heights/1000
    
    print("***max height:", np.nanmax(heights)/1000)
    return df  # Make sure to return the modified dataset
    
def get_kdtree(lat_variable, lon_variable):
    """construct kdtree"""
    
    # Flatten the 2D matrices into 1D arrays
    flat_lats = lat_variable.flatten()
    flat_lons = lon_variable.flatten()
    
    # Combine latitudes and longitudes into a 2D array of coordinates
    coordinates = np.column_stack((flat_lats, flat_lons))
    
    # Build a KD-tree using these combined coordinates
    kdtree = cKDTree(coordinates)
    return kdtree
    
def plot_hsrl(df4, fileout, ylim=(-0.1,0.5), labelv=[], title='',
              start_time=None, end_time=None,
              label1='HSRL Variable', label2='PACE Variable', **kwargs):
    """
    General plotting function for any variables
    """
    plt.figure(figsize=(10,3))
    ax=plt.subplot(111)
    plt.scatter(df4.time2, df4.var2, label=label1,
                facecolors='none', edgecolors='r', **kwargs)
    plt.scatter(df4.time2, df4.var1, label=label2,
                facecolors='none', edgecolors='b', **kwargs)

    plt.ylim(ylim)
    plt.legend(loc=(0.01,0.7), framealpha=0.5)
    plt.ylabel('Variable Value')
    plt.xticks(rotation=45)

    # Set up secondary x-axis for time difference
    secax = ax.secondary_xaxis('top')
    secax.set_xlabel(title+' '+'Time Difference (minutes)')
    
    # Set the tick values and labels of the secondary x-axis
    secax.set_xticks(df4['time2'][::50])
    secax.set_xticklabels(df4['offset'][::50].astype(int))
    
    try:
        plt.xlim(start_time, end_time)
    except:
        pass

    plt.savefig(fileout, dpi=400, bbox_inches='tight', pad_inches=0.1)

def get_hsrl_general(time1, df1, df2, pace_var='aot', hsrl_var='532_AOT_from_bsc',
                    search_radius=2, maxk=1, chi2max=2, nv_ref_min=30, nv_dolp_min=30,\
                    sensor='HARP2', wavelength_index=1, algorithm='FastMAPOL'):
    """
    General function to compare any variables between PACE and HSRL data
    
    Parameters:
    - pace_var: variable name in PACE data (e.g., 'aot', 'aot550')
    - hsrl_var: variable name in HSRL data (e.g., '532_AOT_from_bsc')
    - wavelength_index: index for wavelength dimension if PACE variable is 2D
    """
    
    # Filter PACE data based on chi2 if it exists
    if 'chi2' in df1.variables:
        df1[pace_var] = df1[pace_var].where((df1['chi2'].broadcast_like(df1[pace_var]) <= chi2max) & \
                                           (df1['nv_ref'].broadcast_like(df1[pace_var]) >= nv_ref_min) & \
                                           (df1['nv_dolp'].broadcast_like(df1[pace_var]) >= nv_dolp_min))
    
    # Setup spatial matching
    radius = search_radius/110  # convert km to degrees
    lat1, lon1 = df1.latitude.values, df1.longitude.values
    print(lat1.shape, lon1.shape)
    kdtree = get_kdtree(lat1, lon1)
    
    target_point = np.array([df2.lat, df2.lon])
    target = target_point[:,:].T
    
    dis1, icol1 = kdtree.query(target, k=maxk, distance_upper_bound=radius)
    
    filter1 = dis1 < radius
    
    # Get grid indices
    if sensor == 'HARP2':
        nx = 519
    elif sensor == 'SPEXONE':
        nx = 29
    else:
        # For unknown sensors, try to determine nx from data shape
        nx = df1[pace_var].shape[-1] if len(df1[pace_var].shape) > 1 else 1
        
    i1v, i2v = np.int32(icol1[filter1]/nx), icol1[filter1] % nx
    print('number of collocated points', len(i1v))

    # Extract PACE data
    time1 = pd.to_datetime(time1).strftime('%Y-%m-%d %H:%M:%S')
    time1 = np.repeat(time1, len(i1v))
    
    # Handle both 1D and 2D variables for PACE data
    pace_data = df1[pace_var]
    if len(pace_data.shape) == 3:  # 2D spatial + wavelength dimension
        var1 = np.array([pace_data[i1v[i3], i2v[i3], wavelength_index].values for i3 in range(len(i1v))])
    elif len(pace_data.shape) == 2:  # 2D spatial only
        var1 = np.array([pace_data[i1v[i3], i2v[i3]].values for i3 in range(len(i1v))])
    else:  # 1D or other
        var1 = np.array([pace_data[i1v[i3]].values for i3 in range(len(i1v))])
    
    # Extract coordinate data
    lat1 = np.array([df1.latitude[i1v[i3], i2v[i3]].values for i3 in range(len(i1v))])
    lon1 = np.array([df1.longitude[i1v[i3], i2v[i3]].values for i3 in range(len(i1v))])
    
    # Extract additional variables if they exist
    additional_vars = {}
    for var_name in ['chi2', 'chla', 'nv_ref', 'nv_dolp', 'cloud_fraction', 'nview']:
        if var_name in df1.variables:
            if len(df1[var_name].shape) == 2:
                additional_vars[var_name] = np.array([df1[var_name][i1v[i3], i2v[i3]].values for i3 in range(len(i1v))])
            else:
                additional_vars[var_name] = np.array([df1[var_name][i1v[i3]].values for i3 in range(len(i1v))])
    
    print(f"PACE {pace_var} shape:", var1.shape, "lat/lon shape:", lat1.shape, lon1.shape, "time shape:", time1.shape)
    
    # Extract HSRL data
    dis2 = dis1[filter1]
    lat2 = df2.lat[filter1]
    lon2 = df2.lon[filter1]
    
    # Handle both 1D and 2D variables for HSRL data
    hsrl_data = df2[hsrl_var][filter1]
    if len(hsrl_data.shape) == 2:  # 2D (spatial + wavelength/other dimension)
        if wavelength_index < hsrl_data.shape[1]:
            var2 = hsrl_data.values[:, wavelength_index]
        else:
            var2 = hsrl_data.values[:, 0]  # Use first index if wavelength_index is out of bounds
    else:  # 1D
        var2 = hsrl_data.values
    
    time2 = df2['time'][filter1].values
    print(f"HSRL {hsrl_var} shape:", var2.shape, "lat/lon shape:", lat2.shape, lon2.shape, "time shape:", time2.shape)

    # Combine data into DataFrame
    base_data = [dis2, time1, lon1, lat1, var1, time2, lon2, lat2, var2]
    base_columns = ['dis2', 'time1', 'lon1', 'lat1', 'var1', 'time2', 'lon2', 'lat2', 'var2']
    
    # Add additional variables to the data
    for var_name, var_data in additional_vars.items():
        base_data.append(var_data)
        base_columns.append(var_name)
    
    df3 = pd.DataFrame(np.array(base_data).T, columns=base_columns)
    
    # Convert time columns
    df3['time2'] = pd.to_datetime(df3['time2'])
    df3['time1'] = pd.to_datetime(df3['time1'])
    
    # Calculate time offset
    df3['offset'] = (df3['time2'] - df3['time1']).dt.total_seconds() / 60  # minutes
    
    return df3

def compare_hsrl_general(path1, path2, sensor, algorithm, str1, 
                        pace_var='aot', hsrl_var='532_AOT_from_bsc',
                        start_time=None, end_time=None,
                        chi2max=1.5, nv_ref_min=30, nv_dolp_min=30, \
                        search_radius=2, wavelength_index=1,
                        ylim=(-0.05, 0.5), sysout='./plot/aod_pace_pax/'):
    """
    General comparison function for any variables between PACE and HSRL
    """
    
    file2v = sorted(glob.glob(path2 + '*' + str1 + '*h5'))
    print(file2v)
    df5v = []
    
    for file2 in file2v:
        print(file2)
        time2 = file2.split('ER2_')[1].split('_R')[0]
        datatree = xr.open_datatree(file2)
        df2 = xr.merge(datatree.to_dict().values())
        #placeholder
        #try:
        print("***get alh from backscattering")
        aot_key='532_extinction_from_backscatter'
        heights, aots, weighted_heights=calculate_aerosol_layer_properties_integrated_vectorized(df2, \
                                                            aot_key=aot_key, z_key='z', min_aod=0.1)
        df2['alh'] = heights/1000
        print("***max height:", np.nanmax(heights)/1000)
        #except:
        #    df2['alh'] = xr.full_like(df2['wind_speed'], np.nan)
        
        print('PACE PAX time', time2)
        
        file1v = sorted(glob.glob(path1 + '*' + str(time2) + '*.nc'))
        print('number of nc files', len(file1v))
        df4v = []
        
        for file1 in file1v:
            time1 = file1.split('PACE_' + sensor + '.')[1].split('.')[0]
            print('***L2', time1)

            datatree = xr.open_datatree(file1)
            df1 = xr.merge(datatree.to_dict().values())
            
            # Check valid data before and after filtering
            if pace_var in df1.variables:
                total_valid_before = df1[pace_var].notnull().sum().values
                print(f'Valid {pace_var} before filtering:', total_valid_before)
            
            df4 = get_hsrl_general(time1, df1, df2, 
                                 pace_var=pace_var, hsrl_var=hsrl_var,
                                 search_radius=search_radius, maxk=1,
                                 wavelength_index=wavelength_index, 
                                 sensor=sensor, algorithm=algorithm,
                                 chi2max=chi2max, nv_ref_min=nv_ref_min, nv_dolp_min=nv_dolp_min)
            
            df4v.append(df4)
        
        if len(df4v) > 0:
            print("Concatenating data")
            df5 = pd.concat(df4v)
            os.makedirs(sysout, exist_ok=True)
            fileout = sysout + f'pace_pax_{sensor}_{pace_var}_vs_{hsrl_var}_{time2}.png'
            plot_hsrl(df5, fileout, start_time=start_time, end_time=end_time,
                     title=time2, ylim=ylim, s=10, linewidth=0.9, alpha=0.5, 
                     label1=f'HSRL {hsrl_var}', label2=f'{sensor} {pace_var}')
            df5v.append(df5)
    
    if len(df5v) > 0:
        df6 = pd.concat(df5v)
        return df6
    else:
        return pd.DataFrame()  # Return empty DataFrame if no data

def calculate_aerosol_layer_properties_integrated_vectorized(dataset, \
            aot_key='532_extinction_from_backscatter', z_key='z', min_aod=0.01):
    """
    Vectorized calculation with proper vertical integration considering height spacing (dz)
    
    Parameters:
    -----------
    dataset : xarray.Dataset or dict
        Dataset containing the aerosol and height data
    aot_key : str
        Key for the AOT variable with vertical dimension
    z_key : str
        Key for the height coordinate
    min_aod : float
        Minimum total AOD threshold for calculating average height (default: 0.01)
        
    Returns:
    --------
    dict containing:
        - average_height: AOT-weighted average height [m]
        - total_aod: Column-integrated AOD (∫ AOT dz)
        - aot_weighted_height_integral: ∫ z × AOT dz
        - column_height: Total height range [m]
    """
    
    # Get the data
    z = dataset[z_key].values
    aot_col = dataset[aot_key].values
    
    print(f"Height shape: {z.shape}")
    print(f"AOT column shape: {aot_col.shape}")
    
    # Calculate column height range
    column_height = np.max(z) - np.min(z)
    print(f"Total column height: {column_height:.2f} m")
    print(f"Height spacing (median): {np.median(np.diff(z)):.2f} m")
    
    # Create valid mask (non-NaN and non-negative AOT values)
    valid_mask = ~np.isnan(aot_col) & (aot_col >= 0)
    
    if len(aot_col.shape) == 2:
        # 2D case: (horizontal_points, vertical_levels)
        # Mask invalid data (set to 0 for integration)
        aot_masked = np.where(valid_mask, aot_col, 0)
        
        # Expand height array to match AOT dimensions
        z_expanded = np.broadcast_to(z, aot_col.shape)
        
        # Numerical integration using trapezoidal rule
        # Total AOD = ∫ AOT(z) dz
        total_aods = np.trapezoid(aot_masked, z, axis=-1)
        
        # AOT-weighted height integral = ∫ z × AOT(z) dz  
        aot_weighted_height_integrals = np.trapezoid(aot_masked * z_expanded, z, axis=-1)
        
        # Average height = ∫ z × AOT(z) dz / ∫ AOT(z) dz
        # Only calculate where total AOD is above minimum threshold
        average_heights = np.where(total_aods >= min_aod, 
                                 aot_weighted_height_integrals / total_aods, 
                                 np.nan)
        
    elif len(aot_col.shape) == 3:
        # 3D case: (y_points, x_points, vertical_levels)
        z_expanded = np.broadcast_to(z, aot_col.shape)
        aot_masked = np.where(valid_mask, aot_col, 0)
        
        # Numerical integration using trapezoidal rule along last axis (vertical)
        # Total AOD = ∫ AOT(z) dz
        total_aods = np.trapezoid(aot_masked, z, axis=-1)
        
        # AOT-weighted height integral = ∫ z × AOT(z) dz
        aot_weighted_height_integrals = np.trapezoid(aot_masked * z_expanded, z, axis=-1)
        
        # Average height = ∫ z × AOT(z) dz / ∫ AOT(z) dz
        # Only calculate where total AOD is above minimum threshold
        average_heights = np.where(total_aods >= min_aod, 
                                 aot_weighted_height_integrals / total_aods, 
                                 np.nan)
        
    elif len(aot_col.shape) == 1:
        # 1D case: (vertical_levels,)
        aot_masked = np.where(valid_mask, aot_col, 0)
        
        # Integration for 1D profile
        total_aods = np.trapezoid(aot_masked, z)
        aot_weighted_height_integrals = np.trapezoid(aot_masked * z, z)
        
        # Only calculate average height if total AOD is above minimum threshold
        if total_aods >= min_aod:
            average_heights = aot_weighted_height_integrals / total_aods
        else:
            average_heights = np.nan
    
    else:
        raise ValueError(f"Unsupported AOT array dimensions: {aot_col.shape}")

    return average_heights, total_aods, aot_weighted_height_integrals