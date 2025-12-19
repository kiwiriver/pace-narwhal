
import re
import traceback
import numpy as np
import pandas as pd

from scipy.interpolate import UnivariateSpline
from tools.aeronet_matchup_sda import get_sda_aod
from tools.aeronet_oc import get_aeronet_oc_rrs

def extract_number(s):
    """
    Extract 3-4 consecutive digit wavelength from a string.
    """
    match = re.search(r'(\d{3,4})', s)
    if match:
        return int(match.group(1))
    else:
        return None

def get_aeronet_key(aeronet_df1, old_start1, old_end1):
    """
    get the keys, note that if ended with wavelength, just set old_end1=''
    """
    # Extract wavelength and column mapping
    target_cols = [c for c in aeronet_df1.columns if c.startswith(old_start1) and c.endswith(old_end1)]
    orig_wavelengths = [extract_number(c) for c in target_cols]
    #print('original cols', target_cols)
    #print('original wavelength', orig_wavelengths)
    
    return target_cols, orig_wavelengths
    
def get_aeronet_fit_spline(aeronet_df1, aeronet_df2, input_wavelengths, \
                           old_start1='AOD_', old_end1='nm', new_start1='aot_wv'):
    """
    Interpolate target variable(such as AOD) from aeronet_df1 at input_wavelengths using cubic spline,
    and assign results to aeronet_df2 as new columns named new_start1+wv.
    """

    target_cols, orig_wavelengths = get_aeronet_key(aeronet_df1, old_start1, old_end1)
                    
    for idx, row in aeronet_df1.iterrows():
        target_values = row[target_cols].values.astype(float)
        mask = (target_values != -999) & (~np.isnan(target_values))
        x_valid = np.array(orig_wavelengths)[mask]
        y_valid = target_values[mask]

        # Ensure x_valid is increasing and y_valid is sorted accordingly
        if len(x_valid) > 1:
            sort_idx = np.argsort(x_valid)
            x_valid_sorted = x_valid[sort_idx]
            y_valid_sorted = y_valid[sort_idx]
        else:
            x_valid_sorted = x_valid
            y_valid_sorted = y_valid
    
        #print(x_valid)
        if len(x_valid) > 3:  # Minimum for cubic spline
            spline = UnivariateSpline(x_valid_sorted, y_valid_sorted, k=3, s=0)
            interp = spline(input_wavelengths)
            
        elif len(x_valid) > 1:
            # Fallback to lower order spline, or linear interpolation
            try:
                spline = UnivariateSpline(x_valid_sorted, y_valid_sorted, k=min(2, len(x_valid)-1), s=0)
                interp = spline(input_wavelengths)

                print(input_wavelengths, interp, x_valid_sorted, y_valid_sorted)
            except Exception:
                interp = np.interp(input_wavelengths, x_valid_sorted, y_valid_sorted)
        else:
            interp = np.full(len(input_wavelengths), np.nan)
            
        for wv, val in zip(input_wavelengths, interp):
            aeronet_df2.at[idx, f'{new_start1}{wv}'] = val
        
    return aeronet_df2, orig_wavelengths

def subset_pace_df(pace_df_mean_all, pace_df_std_all, all_vars, extra_vars):
    """
    format pace dataframe, selecting subset of variables

    Ensure no duplicated entries, 
    need chi2, nv_ref, nv_dolp, quality_flag and aot_wv550 for all pace data
    
    """
    full_vars = [item for item in extra_vars if item not in all_vars] + all_vars
    #print("full_vars", full_vars)
    #print(list(pace_df_mean_all.keys()))
    pace_df_mean_all=pace_df_mean_all[full_vars].copy()
    pace_df_std_all=pace_df_std_all[full_vars].copy()

    
    #remove duplicated variable, keep first occurance, since extra_vars may contain same var in all_vars
    #pace_df_mean_all = pace_df_mean_all.loc[:, ~pace_df_mean_all.columns.duplicated()]
    #pace_df_std_all = pace_df_std_all.loc[:, ~pace_df_std_all.columns.duplicated()]
    
    return pace_df_mean_all, pace_df_std_all

def match_time_aeronet(pace_df_mean_all, pace_df_std_all, aeronet_df2, site_to_match, delta_hour=1):
    """
    Match with aeronet data within a window of delta_hour.
    Includes average matched aeronet time as 'datetime_aeronet'.
    Filters out entries with count=0 or all NaN values.
    Also filters input dataframes to match output structure.
    """
    time_window = pd.Timedelta(hours=delta_hour)
    df_pace = pace_df_mean_all[pace_df_mean_all['site'] == site_to_match].copy()
    data_vars = [c for c in aeronet_df2.columns if c not in ['site', 'datetime']]

    mean_rows = []
    std_rows = []

    for ts in df_pace['datetime']:
        mask = (
            (aeronet_df2['site'] == site_to_match) &
            (aeronet_df2['datetime'] >= ts - time_window) &
            (aeronet_df2['datetime'] <= ts + time_window)
        )

        matched_aeronet = aeronet_df2.loc[mask, data_vars + ['datetime']]
        matched_aeronet = matched_aeronet.replace(-999, np.nan)
        means = matched_aeronet[data_vars].mean(axis=0)
        stds = matched_aeronet[data_vars].std(axis=0)
        num_timestamps = matched_aeronet['datetime'].count()
        
        # Skip if no matches or all data values are NaN
        if num_timestamps == 0 or means.isna().all():
            continue
        
        # Compute average datetime if there are matches
        avg_aeronet_time = matched_aeronet['datetime'].mean()
        avg_aeronet_time = pd.to_datetime(avg_aeronet_time)
        
        mean_row = {
            'datetime': ts,
            'site': site_to_match,
            'count': num_timestamps,
            'datetime_aeronet': avg_aeronet_time
        }
        
        mean_row.update({var: means[var] for var in means.index})
        
        std_row = {
            'datetime': ts,
            'site': site_to_match,
            'count': num_timestamps,
            'datetime_aeronet': avg_aeronet_time
        }
        std_row.update({var: stds[var] for var in stds.index})
        
        mean_rows.append(mean_row)
        std_rows.append(std_row)

    aeronet_df3_mean = pd.DataFrame(mean_rows)
    aeronet_df3_std = pd.DataFrame(std_rows)
    
    # Filter input dataframes to match the structure of aeronet_df3_mean and aeronet_df3_std
    if not aeronet_df3_mean.empty:
        # Get the datetime values that exist in aeronet_df3_mean/aeronet_df3_std
        valid_datetimes = aeronet_df3_mean['datetime'].unique()
        
        # Filter pace_df_mean_all and pace_df_std_all to match
        pace_df_mean_all_filtered = pace_df_mean_all[
            (pace_df_mean_all['site'] == site_to_match) & 
            (pace_df_mean_all['datetime'].isin(valid_datetimes))
        ].copy()
        
        pace_df_std_all_filtered = pace_df_std_all[
            (pace_df_std_all['site'] == site_to_match) & 
            (pace_df_std_all['datetime'].isin(valid_datetimes))
        ].copy()
    else:
        # If no valid matches, return empty dataframes with same structure
        pace_df_mean_all_filtered = pace_df_mean_all[pace_df_mean_all['site'] == site_to_match].iloc[0:0].copy()
        pace_df_std_all_filtered = pace_df_std_all[pace_df_std_all['site'] == site_to_match].iloc[0:0].copy()

    return aeronet_df3_mean, aeronet_df3_std, pace_df_mean_all_filtered, pace_df_std_all_filtered