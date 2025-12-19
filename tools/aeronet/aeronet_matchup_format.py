import re
import os
import numpy as np
import pandas as pd

from scipy.interpolate import UnivariateSpline
from tools.aeronet_matchup_sda import get_sda_aod
from tools.aeronet_oc import get_aeronet_oc_rrs
from tools.aeronet_matchup_match import get_aeronet_fit_spline            
from tools.aeronet_matchup_man import get_man_site

def clean_pace_data(df_mean_all, df_std_all):
    """
    clean pace data:
    -dropna
    -add timestamp
    -reorder columns
    
    """
    df_mean_all = df_mean_all.dropna(subset=['chi2'])
    df_std_all = df_std_all.dropna(subset=['chi2'])
    
    # Convert 'timestamp' to datetime object
    df_mean_all['datetime'] = pd.to_datetime(df_mean_all['timestamp'], format='%Y%m%dT%H%M%S')
    df_std_all['datetime'] = pd.to_datetime(df_std_all['timestamp'], format='%Y%m%dT%H%M%S')
    
    #'distance0_kdtree':dis0, 'distance1_haversine':dis1, 'distance2_euclidean':dis2
    desired_first_cols = [
        'datetime',
        'pace_date',
        'timestamp',      # will be datetime object
        'site_index',
        'site',           # Aeronet site name
        'aeronet_lon',
        'aeronet_lat',
        'pace_lon',
        'pace_lat',
        'pace_loc_index_lon',
        'pace_loc_index_lat',
        'distance0_kdtree',
        'distance1_haversine',
        'distance2_euclidean',
        'chi2',
        'count',
        'chi2_first_guess',	
        'timing',
        'nv_ref',	
        'nv_dolp',
        'nfev',	
        'njev',	
        'quality_flag',	
        'ozone',	
        'surface_pressure',	
        'sensor_view_angle',	
    ]
    
    # Make sure all desired first columns are present
    # Ignore extras in desired_first_cols not in DataFrame; use only those present
    first_cols_mean = [c for c in desired_first_cols if c in df_mean_all.columns]
    remaining_cols_mean = [c for c in df_mean_all.columns if c not in first_cols_mean]
    df_mean_all = df_mean_all[first_cols_mean + remaining_cols_mean]
    
    first_cols_std = [c for c in desired_first_cols if c in df_std_all.columns]
    remaining_cols_std = [c for c in df_std_all.columns if c not in first_cols_std]
    df_std_all = df_std_all[first_cols_std + remaining_cols_std]

    return df_mean_all, df_std_all
    
def format_pace_df(dataset, nv_max=170, flag_aot550=True):
    """
    format pace df
    """
    #rename wavelength dimension and variables
    dataset = switch_wavelength_names(dataset)
    
    #check invalid datatype, no need anymore after 
    #decode_timedelta=decode_timedelta
    #dataset = fix_xr_timing(dataset)

    #for remotap data, nv is not in default output, add default number of max 170
    if 'nv_ref' not in dataset.data_vars:
        dataset['nv_ref'] = xr.full_like(dataset['chi2'], nv_max)
        
    if 'nv_dolp' not in dataset.data_vars:
        dataset['nv_dolp'] = xr.full_like(dataset['chi2'], nv_max)

    if(flag_aot550):
        # Get the wavelength closest to 550
        target_wv = 550
        wvv = list(dataset['wavelength'].values)
        
        # Find wavelength closest to target_wv
        wv550 = min(wvv, key=lambda x: abs(x - target_wv))
        iwv550 = wvv.index(wv550)
        
        #print(f"Using wavelength {wv550} (at index {iwv550}) as closest to {target_wv}")
        
        # Get aot550 for the matchup with hsrl data at a single wavelength
        dataset['aot'+str(target_wv)] = dataset['aot'][:, :, iwv550]
        
    #print('pace keys', list(dataset.keys()))
          
    return dataset

def switch_wavelength_names(dataset):
    """
    this may happen for old data, or spexone remotap data, 
    wavelength3d is used for optical properties, while wavelenth is the one for inversions. 
    we need to switch them
    """
    # Check presence
    has_wavelength = 'wavelength' in dataset.dims or 'wavelength' in dataset.data_vars
    has_wavelength3d = 'wavelength3d' in dataset.dims or 'wavelength3d' in dataset.data_vars
    has_wavelength_3d = 'wavelength_3d' in dataset.dims or 'wavelength_3d' in dataset.data_vars

    # Only perform if both exist
    if has_wavelength and (has_wavelength3d or has_wavelength_3d):
        # Rename 'wavelength' to 'wavelength_inv'
        if 'wavelength' in dataset.dims:
            dataset = dataset.rename({'wavelength': 'wavelength_inv'})
        if 'wavelength' in dataset.data_vars:
            dataset = dataset.rename({'wavelength': 'wavelength_inv'})

        # Rename 'wavelength3d' or 'wavelength_3d' to 'wavelength'
        for old in ['wavelength3d', 'wavelength_3d']:
            if old in dataset.dims:
                dataset = dataset.rename({old: 'wavelength'})
            if old in dataset.data_vars:
                dataset = dataset.rename({old: 'wavelength'})
    return dataset

def fix_xr_timing(dataset, var='timing'):
    """
    No need anymore.
    
    Fix issues where numeric timing data is incorrectly interpreted as datetime64.
    Converts it back to float.

    should fixed after using:
    datatree = xr.open_datatree(nc_path, decode_timedelta=False)
    
    Otherwise, the results on timings seem not right

    """
    
    if var in dataset.variables:
        # Check if it's incorrectly stored as datetime64
        if np.issubdtype(dataset[var].dtype, np.datetime64):
            try:
                # Convert datetime64 back to numeric (assuming it represents seconds, hours, etc.)
                # Get the numeric values from datetime64
                numeric_values = dataset[var].values.astype('datetime64[ns]').astype(np.float64) / 1e9
                dataset[var] = (dataset[var].dims, numeric_values)
                #print(f"Converted {var} from datetime64 to float")
            except:
                try:
                    # Alternative: extract just the numeric part if stored as string-like datetime
                    dataset[var] = dataset[var].astype(float)
                except:
                    print(f"Warning: Could not convert {var} to float")
        
        # Ensure it's float type
        elif not np.issubdtype(dataset[var].dtype, np.floating):
            try:
                dataset[var] = dataset[var].astype(float)
                #print(f"Converted {var} to float type")
            except:
                print(f"Warning: Could not convert {var} to float")
    
    return dataset
    
###############################################################################
def get_val_df(val_source, folder1, site1):
    """
    get validation data based on val_source type
    """
    if(val_source.upper() in ['MAN','PACE_PAX', 'EARTHCARE']):
        #only for one day, and also match the specific site1 location (one point)
        aeronet_df1 = get_man_site(folder1, site1)
        site_name='Site_Name'
        #add p0 ... to aeronet_site and create site_name
        #note different variable name as site name
    elif(val_source.upper() in ['AERONET', 'AERONET_OC']):
        #AERONET, AERONET OC
        aeronet_df1 = pd.read_csv(os.path.join(folder1, site1 + '.csv'))
        site_name='AERONET_Site'
    else:
        print(f"canot load df, {val_source} do not exist")
        exit
        
    aeronet_df1 = aeronet_df1.replace(-999, np.nan)
    #why comment out?
    #aeronet_df1 = aeronet_df1.dropna(axis=1, how='all')
    aeronet_df1 = aeronet_df1.dropna(axis=1, how='all')
    
    return aeronet_df1, site_name

def format_aeronet_df(aeronet_df1, input_wavelengths = [440, 550, 670, 870], \
                     old_start1='AOD_', old_end1='nm', new_start1='aot_wv',\
                     input_is_sda=False, site_name='AERONET_Site', df0=None):
    """
    format aeronet df, interpolate wavelength, ***select the relevant variables
    aeronet_df1: aeronet

    Note: add a few quanitities for analysis:
        -compute Veff from sigma_g
        -compute sphericity fraction in decimal, rather than percentage
        -fit SDA wavelength

    Todo:
        add aod550 to aeronet data, but the variable is not always available directly
    
    """

    #note that sometimes for MAN data there is an extra (int) in its variable name, remove it
    aeronet_df1.columns = aeronet_df1.columns.str.replace(r'\(int\)', '', regex=True)
    
    aeronet_df2=pd.DataFrame()
    aeronet_df2['site'] = aeronet_df1[site_name]

    aeronet_df2['datetime'] = create_datetime_column(aeronet_df1)
    
    ###############################################################################
    if df0 is not None:
        try:
            wvv2, rrs2 = get_aeronet_oc_rrs(df0, aeronet_df1, key1='Lwn_f/Q[', key2='Exact_Wavelengths(um)_')
            for i2, wv2 in enumerate(wvv2):
                aeronet_df1[f'Rrs_f/Q[{np.int32(wv2)}nm]'] = rrs2[:,i2]
    
            wvv2, rrs2 = get_aeronet_oc_rrs(df0, aeronet_df1, key1='Lwn_IOP[', key2='Exact_Wavelengths(um)_')
            for i2, wv2 in enumerate(wvv2):
                aeronet_df1[f'Rrs_IOP[{np.int32(wv2)}nm]'] = rrs2[:,i2]
    
            wvv2, rrs2 = get_aeronet_oc_rrs(df0, aeronet_df1, key1='Lwn[', key2='Exact_Wavelengths(um)_')
            for i2, wv2 in enumerate(wvv2):
                aeronet_df1[f'Rrs[{np.int32(wv2)}nm]'] = rrs2[:,i2]
                
        except:
            print("convert rrs failed, not aeronet oc case")
            pass

    ###############################################################################
    try:
        aeronet_df1['Sphericity_Factor']=aeronet_df1['Sphericity_Factor(%)']/100
    except:
        pass

    ###############################################################################
    try:
        #compute effective variance
        #veff = exp(ln^2 sigma_g)-1 
        aeronet_df1['VEff-F']=np.exp(np.log(aeronet_df1['Std-F'])**2)-1
        aeronet_df1['VEff-C']=np.exp(np.log(aeronet_df1['Std-C'])**2)-1
        aeronet_df1['VEff-T']=np.exp(np.log(aeronet_df1['Std-T'])**2)-1
    except:
        pass
        
    if input_is_sda:
        # SDA expects a pair of dataframes and a 'time1' argument.
        # We'll use the main aeronet_df1 twice, and get the time vector as needed.
        time1 = aeronet_df2['datetime'].values if 'datetime' in aeronet_df2 else None
        # combine_aeronet_aod returns a new DataFrame with interpolated columns.
        interp_df = get_sda_aod(aeronet_df1, wvv=input_wavelengths)
        
        aeronet_df2=aeronet_df2.reset_index(drop=True)
        interp_df=interp_df.reset_index(drop=True)
        
        # Attach to aeronet_df2
        for col in interp_df.columns:
            #if col not in aeronet_df2.columns:
            #    aeronet_df2[col] = interp_df[col]
            aeronet_df2[col]=interp_df[col].values

        #print("after sda interpolation", aeronet_df2)
        
        orig_wvv = input_wavelengths
        
    else: 
        #map to the pace wavelength
        if input_wavelengths is not None and isinstance(input_wavelengths, (list, np.ndarray)):

            #interpolate data into new set of wavelength: input_wavelengths
            #original wavelength will be save
            aeronet_df2, orig_wvv= get_aeronet_fit_spline(aeronet_df1, aeronet_df2, \
                                                          input_wavelengths, \
                                  old_start1=old_start1, old_end1=old_end1, new_start1=new_start1)
            
        else:
            target_cols = [c for c in aeronet_df1.columns \
                           if c.startswith(old_start1) and c.endswith(old_end1)]
            #print("aeronet_df1.columns", list(aeronet_df1.columns))
            print("new_start1", new_start1)
            print("target_cols", target_cols)
            aeronet_df2[new_start1]=aeronet_df1[target_cols]
            orig_wvv=None
    
    return aeronet_df2, orig_wvv

def create_datetime_column(df):
    """
    Create datetime column from date and time columns with flexible naming for AOD, SDA, LWN
    """
    # Define possible column name patterns
    date_patterns = [
        #AOD
        'Date(dd:mm:yyyy)',
        #SDA,
        'Date_(dd:mm:yyyy)',
        #LWN
        'Date(dd-mm-yyyy)', 
    ]
    
    time_patterns = [
        #AOD, LWN
        'Time(hh:mm:ss)',
        #SDA
        'Time_(hh:mm:ss)',
    ]
    
    # Find matching columns
    date_col = None
    time_col = None

    #print(df.columns)
    
    for pattern in date_patterns:
        #print(pattern)
        if pattern in df.columns:
            date_col = pattern
            break
    
    for pattern in time_patterns:
        #print(pattern)
        if pattern in df.columns:
            time_col = pattern
            break
    
    if date_col is None or time_col is None:
        raise ValueError(f"Could not find date/time columns. Available columns: {list(df.columns)}")
    
    print(f"Using date column: {date_col}")
    print(f"Using time column: {time_col}")
    
    # Create datetime column
    df['datetime'] = pd.to_datetime(df[date_col] + ' ' + df[time_col], 
                                   format='%d:%m:%Y %H:%M:%S')
    
    return df['datetime']