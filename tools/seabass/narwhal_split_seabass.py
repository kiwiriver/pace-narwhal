"""
format seabass data and split them into proper folder
Meng Gao, Dec 19, 2025
"""
import earthaccess
import requests
import os
import re

import sys
import glob
import time

import numpy as np
import xarray as xr
import pandas as pd
import json

import pickle

import tools.SB_support as sb

def move_columns_to_front(df, columns_to_move):
    """
    Move specified columns to the front of the dataframe
    
    Parameters:
    df: DataFrame to reorder
    columns_to_move: List of column names to move to front
    
    Returns:
    df: DataFrame with reordered columns
    """
    
    # Check which columns actually exist in the dataframe
    existing_front_columns = [col for col in columns_to_move if col in df.columns]
    missing_columns = [col for col in columns_to_move if col not in df.columns]
    
    # Get remaining columns (excluding the ones we're moving to front)
    remaining_columns = [col for col in df.columns if col not in existing_front_columns]
    
    # Create new column order
    new_column_order = existing_front_columns + remaining_columns
    
    # Reorder the dataframe
    df = df[new_column_order]
    
    print(f"Moved {len(existing_front_columns)} columns to front: {existing_front_columns}")
    if missing_columns:
        print(f"Warning: These columns were not found: {missing_columns}")
    
    print("New column order (first 10):", df.columns[:10].tolist())
    
    return df

def create_time_and_date_columns(df, datetime_col='datetime', \
                                 date_name = "Date(dd:mm:yyyy)", time_name= 'Time(hh:mm:ss)'):
    """
    Create Time(hh:mm:ss) and Date(dd:mm:yyyy) columns from datetime column
    
    Parameters:
    df: DataFrame with datetime column
    datetime_col: Name of the datetime column (default: 'datetime')
    
    Returns:
    df: DataFrame with new Time and Date columns added
    """
    import pandas as pd
    
    if datetime_col not in df.columns:
        print(f"Warning: '{datetime_col}' column not found in DataFrame")
        return df
    
    # Convert to datetime if it's not already
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    
    # Create Time(hh:mm:ss) column
    df[time_name] = df[datetime_col].dt.strftime('%H:%M:%S')
    
    # Create Date(dd:mm:yyyy) column  
    df[date_name] = df[datetime_col].dt.strftime('%d:%m:%Y')
    
    print(f"Created {time_name} and {date_name} columns")
    print("show first 5 elements:")
    for i in range(min(5, len(df))):  # Show first 5 examples
        original = df[datetime_col].iloc[i]
        time_formatted = df[time_name].iloc[i]
        date_formatted = df[date_name].iloc[i]
        print(f"  {original} -> Time: {time_formatted}, Date: {date_formatted}")
    
    return df



def get_site_name(file1):
    """get site name from the filename"""
    site1=file1.split('aoc_')[1].split('_v4')[0]
    return site1
    
def add_wv_to_wavelength_columns(df):
    """
    Add '_wv' after specified keys and before the wavelength number (including decimals)
    
    Keys to modify: lw, es, brdf, aoc_lw, lwn_fq, aot, rrs
    Example: 'lw412.5' becomes 'lw_wv412.5', 'aot551.8' becomes 'aot_wv551.8'
    """
    
    
    # Define the keys that should get '_wv' added
    target_keys = ['lw', 'es', 'brdf', 'aoc_lw', 'lwn_fq', 'aot', 'rrs']
    
    # Create rename dictionary
    rename_dict = {}
    
    for col in df.columns:
        for key in target_keys:
            # Pattern to match: key followed by digits and optional decimal (wavelength)
            pattern = f'^({key})(\d+\.?\d*)$'
            match = re.match(pattern, col)
            
            if match:
                prefix = match.group(1)  # The key (e.g., 'lw', 'aot')
                wavelength = match.group(2)  # The wavelength number (e.g., '412.5', '551.8')
                new_name = f"{prefix}_wv{wavelength}"
                rename_dict[col] = new_name
                break  # Found a match, no need to check other keys for this column
    
    # Apply the renaming
    df_renamed = df.rename(columns=rename_dict)
    
    return df_renamed