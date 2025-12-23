
import re
import traceback
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
from tools.aeronet_matchup_sda import get_sda_aod
from tools.aeronet_oc import get_aeronet_oc_rrs

import numpy as np

import re

def extract_number(s):
    """
    Extract wavelength number and return as float for consistency
    """
    match = re.search(r'(\d+\.?\d*)', s)
    if match:
        return float(match.group(1))  # Always return float
    else:
        return None

def get_aeronet_key(aeronet_df1, old_start1, old_end1):
    """
    Get the keys, handles both integer and decimal wavelengths
    """
    # Updated regex to handle decimals: \d+\.?\d*
    pattern = f'^{re.escape(old_start1)}\\d+\\.?\\d*{re.escape(old_end1)}$'
    target_cols = [c for c in aeronet_df1.columns 
                   if c.startswith(old_start1) and c.endswith(old_end1) and
                   re.match(pattern, c)]
    
    orig_wavelengths = [extract_number(c) for c in target_cols]
    
    # Check whether they are numbers
    if are_all_numeric(orig_wavelengths):
        print("✅ All values are numeric")
    else:
        print("❌ Some values are not numeric")
        print("Non-numeric values:", [w for w in orig_wavelengths if not isinstance(w, (int, float))])
    
    return target_cols, orig_wavelengths

def are_all_numeric(values):
    """Check if all values are numeric (now expects floats)"""
    return all(isinstance(x, (int, float)) and not np.isnan(x) for x in values if x is not None)


def find_closest_wavelength_keys(df, wavelengths, prefix, suffix=''):
    """
    Find the closest matching column keys in dataframe for given wavelengths.
    Handles cases where column names contain decimal numbers.
    """
    # Get all columns that match the pattern
    pattern = rf'{re.escape(prefix)}(\d+\.?\d*){re.escape(suffix)}'
    matching_cols = []
    col_wavelengths = []
    
    for col in df.columns:
        match = re.match(pattern, col)
        if match:
            try:
                wv = float(match.group(1))
                matching_cols.append(col)
                col_wavelengths.append(wv)
            except ValueError:
                continue
    
    # Find closest matches for each target wavelength
    col_wavelengths = np.array(col_wavelengths)
    closest_keys = []
    actual_wavelengths = []
    
    for target_wv in wavelengths:
        if len(col_wavelengths) > 0:
            # Find the closest wavelength
            distances = np.abs(col_wavelengths - target_wv)
            closest_idx = np.argmin(distances)
            closest_keys.append(matching_cols[closest_idx])
            actual_wavelengths.append(col_wavelengths[closest_idx])
        else:
            closest_keys.append(None)
            actual_wavelengths.append(np.nan)
    
    return closest_keys, actual_wavelengths

def check_aeronet_fit(aeronet_df1, orig_wavelengths, \
                     aeronet_df2, input_wavelengths, max_order=None,\
                     old_start1='AOD_', old_end1='nm', new_start1='aot_wv',\
                     nline=3, outfile=None, flag_verbose=False):
    """
    df1: original data
    max_order: order used to do interpolation as in df2
    nline: line to plot
    """
    
    # Find closest matching keys for original data
    key1v, actual_wv1 = find_closest_wavelength_keys(aeronet_df1, orig_wavelengths, 
                                                     old_start1, old_end1)
    
    # Filter out None keys and get corresponding data
    valid_keys1 = [k for k in key1v if k is not None]
    valid_wv1 = [w for k, w in zip(key1v, actual_wv1) if k is not None]
    
    if len(valid_keys1) == 0:
        print("No matching columns found in original data")
        return
        
    data1 = aeronet_df1[valid_keys1].values
    wvv1 = np.array(valid_wv1)
    
    # Find closest matching keys for interpolated data
    key2v, actual_wv2 = find_closest_wavelength_keys(aeronet_df2, input_wavelengths, 
                                                     new_start1, '')
    
    # Filter out None keys and get corresponding data
    valid_keys2 = [k for k in key2v if k is not None]
    valid_wv2 = [w for k, w in zip(key2v, actual_wv2) if k is not None]
    
    if len(valid_keys2) == 0:
        print("No matching columns found in interpolated data")
        return
        
    data2 = aeronet_df2[valid_keys2].values
    wvv2 = np.array(valid_wv2)
    
    # Ensure we don't plot more lines than available data
    nline = min(nline, len(data1), len(data2))

    plt.figure(figsize=(8,6))
    
    # Get default color cycle
    colors = plt.cm.tab10(np.linspace(0, 1, nline))
    
    # Plot each line with matching colors
    for i in range(nline):
        color = colors[i]
        plt.plot(wvv1, data1[i], '.-', color=color, 
                label=f'original_{i}' if nline > 1 else 'original', alpha=0.8)
        plt.plot(wvv2, data2[i], 'o', color=color, markerfacecolor='none', 
                markersize=6, label=f'fitted_{i}' if nline > 1 else 'fitted', alpha=0.8)
    
    plt.legend(loc=(1.05,0))
    plt.xlabel("wavelength")
    plt.ylabel(new_start1)
    title_str = f"check fitting"
    if max_order is not None:
        title_str += f", max_order: {max_order}"
    plt.title(title_str)
    plt.tight_layout()
    
    if outfile:
        plt.savefig(outfile, dpi=300)

    plt.close()
    
    if(flag_verbose):
        # Print information about matched wavelengths
        print("Original wavelengths - Requested vs Found:")
        for req, found, key in zip(orig_wavelengths, actual_wv1, key1v):
            if key is not None:
                print(f"  {req:.1f} -> {found:.1f} ({key})")
            else:
                print(f"  {req:.1f} -> Not found")
        
        print("\nInterpolated wavelengths - Requested vs Found:")
        for req, found, key in zip(input_wavelengths, actual_wv2, key2v):
            if key is not None:
                print(f"  {req:.1f} -> {found:.1f} ({key})")
            else:
                print(f"  {req:.1f} -> Not found")

    
def get_aeronet_fit_polynomial(aeronet_df1, aeronet_df2, input_wavelengths, 
                              max_order=1, old_start1='AOD_', old_end1='nm', 
                              new_start1='aot_wv'):
    """
    Interpolate target variable using the two nearby wavelengths for each target wavelength.
    Returns NaN for wavelengths outside the input range.
    
    Parameters:
    -----------
    max_order : int
        Maximum polynomial order to use (default=1 for linear interpolation), higher order for consistency but 1d is always used
    """
    
    target_cols, orig_wavelengths = get_aeronet_key(aeronet_df1, old_start1, old_end1)
    
    for idx, row in aeronet_df1.iterrows():
        target_values = row[target_cols].values.astype(float)
        mask = (target_values != -999) & (~np.isnan(target_values))
        x_valid = np.array(orig_wavelengths)[mask]
        y_valid = target_values[mask]
        
        if len(x_valid) > 1:
            # Sort data
            sort_idx = np.argsort(x_valid)
            x_valid_sorted = x_valid[sort_idx]
            y_valid_sorted = y_valid[sort_idx]
            
            interp = []
            
            for wv in input_wavelengths:
                # Find the two nearby wavelengths
                if wv < x_valid_sorted[0] or wv > x_valid_sorted[-1]:
                    # Outside range
                    interp.append(np.nan)
                else:
                    # Find bracketing wavelengths
                    idx_right = np.searchsorted(x_valid_sorted, wv)
                    
                    if idx_right == 0:
                        # wv equals the first wavelength
                        interp.append(y_valid_sorted[0])
                    elif idx_right >= len(x_valid_sorted):
                        # wv equals the last wavelength
                        interp.append(y_valid_sorted[-1])
                    elif x_valid_sorted[idx_right] == wv:
                        # Exact match
                        interp.append(y_valid_sorted[idx_right])
                    else:
                        # Interpolate between two nearby points
                        idx_left = idx_right - 1
                        x1, x2 = x_valid_sorted[idx_left], x_valid_sorted[idx_right]
                        y1, y2 = y_valid_sorted[idx_left], y_valid_sorted[idx_right]
                        
                        # Determine polynomial order (max_order or 1, whichever is smaller)
                        poly_order = min(max_order, 1)  # For 2 points, max order is 1
                        
                        if poly_order == 1:
                            # Linear interpolation
                            interpolated_val = y1 + (y2 - y1) * (wv - x1) / (x2 - x1)
                        else:
                            # This case won't occur with 2 points, but keeping for consistency
                            coeffs = np.polyfit([x1, x2], [y1, y2], poly_order)
                            poly = np.poly1d(coeffs)
                            interpolated_val = poly(wv)
                        
                        interp.append(interpolated_val)
            
            interp = np.array(interp)
            
        else:
            # Not enough points for interpolation
            interp = np.full(len(input_wavelengths), np.nan)
        
        # Store results
        for wv, val in zip(input_wavelengths, interp):
            aeronet_df2.at[idx, f'{new_start1}{wv}'] = val
    
    return aeronet_df2, orig_wavelengths

def get_aeronet_fit_spline(aeronet_df1, aeronet_df2, input_wavelengths, \
                           old_start1='AOD_', old_end1='nm', new_start1='aot_wv'):
    """
    Interpolate target variable(such as AOD) from aeronet_df1 at input_wavelengths using cubic spline,
    and assign results to aeronet_df2 as new columns named new_start1+wv.
    Returns NaN for wavelengths outside the input range.
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
            
            # Define valid wavelength range
            x_min, x_max = x_valid_sorted[0], x_valid_sorted[-1]
        else:
            x_valid_sorted = x_valid
            y_valid_sorted = y_valid
            x_min = x_max = x_valid_sorted[0] if len(x_valid_sorted) > 0 else np.nan
    
        if len(x_valid) > 3:  # Minimum for cubic spline
            spline = UnivariateSpline(x_valid_sorted, y_valid_sorted, k=3, s=0)
            
            # Apply spline only to wavelengths within range, NaN otherwise
            interp = []
            for wv in input_wavelengths:
                if x_min <= wv <= x_max:
                    interp.append(spline(wv))
                else:
                    interp.append(np.nan)
            interp = np.array(interp)
            
        elif len(x_valid) > 1:
            # Fallback to lower order spline, or linear interpolation
            try:
                spline = UnivariateSpline(x_valid_sorted, y_valid_sorted, k=min(2, len(x_valid)-1), s=0)
                
                # Apply spline only to wavelengths within range, NaN otherwise
                interp = []
                for wv in input_wavelengths:
                    if x_min <= wv <= x_max:
                        interp.append(spline(wv))
                    else:
                        interp.append(np.nan)
                interp = np.array(interp)
                
                print(input_wavelengths, interp, x_valid_sorted, y_valid_sorted)
            except Exception:
                # Use linear interpolation with range checking
                interp = []
                for wv in input_wavelengths:
                    if x_min <= wv <= x_max:
                        interp.append(np.interp(wv, x_valid_sorted, y_valid_sorted))
                    else:
                        interp.append(np.nan)
                interp = np.array(interp)
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