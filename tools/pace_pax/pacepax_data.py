import os
import re
import shutil
import glob
from pathlib import Path

import xarray as xr
import pandas as pd
import numpy as np

from tools.pacepax_format import format_hsrl2_data_for_val
from tools.pacepax_tools import get_alh

def h5_to_csv_xarray(h5_file_path, variables, output_dir="csv_output", 
                     campaign="PACE_PAX", version="R1", aircraft="ER2"):
    """
    Convert HSRL2 HDF5 file to CSV format using xarray
    First dimension is always time, second dimension (size=1) is ignored
    
    Args:
        h5_file_path (str): Path to the HDF5 file
        output_dir (str): Directory to save CSV files
        campaign (str): Campaign name (default: "PACE_PAX", case preserved)
        version (str): Data version (default: "R1")
        aircraft (str): Aircraft name (default: "ER2")
        variables (list): List of variable names to extract
    """
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        print(f"Processing: {os.path.basename(h5_file_path)}")
        
        # Open the HDF5 file using xarray datatree
        print("  📂 Opening HDF5 file with xarray...")
        datatree = xr.open_datatree(h5_file_path)

        # Merge all groups into a single dataset
        print("  🔄 Merging groups...")
        dataset = xr.merge(datatree.to_dict().values())
        print("***********************************")
        dataset=get_alh(dataset)
        print("***********************************")
        
        print(f"  📊 Available variables: {len(list(dataset.data_vars.keys()))}")
        print(f"  📏 Dataset dimensions: {dict(dataset.dims)}")
        
        # Extract the target variables
        data_dict = {}
        found_vars = []
        
        for var in variables:
            if var in dataset:
                
                data = dataset[var]
                values = data.values

                #if(var=='532_AOT_from_bsc'):
                #    data1=values
                #    print("convert to 1d:", data1.shape, np.nanmin(data1), np.nanmax(data1))
                
                # Always take first dimension (time), ignore second dimension if size=1
                if values.ndim == 2:
                    # Should be [time_size, 1] - take first dimension
                    data_array = values[:, 0]
                    print(f"  ✓ {var}: {values.shape} -> {len(data_array)} values (2D->1D)")
                elif values.ndim == 1:
                    # Already 1D
                    data_array = values
                    print(f"  ✓ {var}: {len(data_array)} values (1D)")
                else:
                    # Other dimensions - flatten
                    data_array = values.flatten()
                    print(f"  ⚠️  {var}: {values.shape} flattened to {len(data_array)} values")
                
                # Check data quality
                valid_count = np.sum(~np.isnan(data_array)) if len(data_array) > 0 else 0
                print(f"    Valid: {valid_count}/{len(data_array)}")
                
                data_dict[var] = data_array
                found_vars.append(var)

                #if(var=='532_AOT_from_bsc'):
                #    data1=data_array
                #    print("convert to 1d:", data1.shape, np.nanmin(data1), np.nanmax(data1))
                                    
            else:
                print(f"  ❌ {var}: not found")

        
        if not data_dict:
            print("  ❌ No target variables found")
            print(f"  📋 Available variables: {list(dataset.data_vars.keys())[:10]}")
            datatree.close()
            return None, None
        
        # Determine the expected length
        lengths = [len(arr) for arr in data_dict.values()]
        if len(set(lengths)) > 1:
            print(f"  ⚠️  Variables have different lengths: {dict(zip(data_dict.keys(), lengths))}")
            # Use time dimension if available, otherwise use most common length
            if 'time' in data_dict:
                expected_length = len(data_dict['time'])
                print(f"    Using time dimension length: {expected_length}")
            else:
                expected_length = max(set(lengths), key=lengths.count)
                print(f"    Using most common length: {expected_length}")
            
            # Adjust array lengths
            for var in list(data_dict.keys()):
                if len(data_dict[var]) > expected_length:
                    data_dict[var] = data_dict[var][:expected_length]
                    print(f"    ✂️  Truncated {var}")
                elif len(data_dict[var]) < expected_length:
                    # Pad with NaN
                    padding_size = expected_length - len(data_dict[var])
                    data_dict[var] = np.concatenate([
                        data_dict[var], 
                        np.full(padding_size, np.nan)
                    ])
                    print(f"    📏 Padded {var}")
        else:
            expected_length = lengths[0]
        
        # Add metadata columns (preserve case for campaign)
        data_dict['campaign'] = [campaign] * expected_length  # Keep original case
        data_dict['version'] = [version] * expected_length  
        data_dict['aircraft'] = [aircraft] * expected_length
        
        print(f"  ✓ Added metadata: {campaign}, {version}, {aircraft}")
        
        # Create DataFrame
        df = pd.DataFrame(data_dict)
        
        # Reorder columns - metadata first
        priority_columns = ['campaign', 'version', 'aircraft']
        other_columns = [col for col in df.columns if col not in priority_columns]
        df = df[priority_columns + other_columns]

        
        try:
            df = format_hsrl2_data_for_val(df)
        except:
            print("no update on variable names for validation")
                
        # Generate output filename
        base_name = Path(h5_file_path).stem
        csv_filename = f"{base_name}.csv"
        csv_path = os.path.join(output_dir, csv_filename)
        
        # Save to CSV
        df.to_csv(csv_path, index=False)
        
        #print("check again:", np.nanmax(df['532_AOT_from_bsc'].values))
        #print("check again:", np.nanmax(df['wind_speed'].values))
        #df.to_pickle('test.pk')

        
        print(f"  💾 Saved: {csv_path}")
        print(f"  📊 Shape: {df.shape}")
        print(f"  🏷️  Variables found: {found_vars}")
        
        # Close the datatree
        datatree.close()
        
        return csv_path, df.shape
        
    except Exception as e:
        print(f"❌ Error processing {h5_file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def batch_convert_h5_to_csv_xarray(h5_directory, pattern="*hsrl*.h5", output_dir="csv_output", 
                                  campaign="PACE_PAX", version="R1", aircraft="ER2",
                                  variables=[
                                      'lat', 'lon', 'time', 
                                      '355_AOT_from_bsc', '532_AOT_from_bsc',
                                      '355_AOT_hi', '532_AOT_hi',
                                      'cloud_top_height', 'wind_direction', 'wind_speed', 'alh'
                                  ]):
    """
    Batch convert multiple files using xarray
    
    Args:
        h5_directory (str): Directory containing HDF5 files
        pattern (str): File pattern to match
        output_dir (str): Directory to save CSV files
        campaign (str): Campaign name (case preserved)
        version (str): Data version
        aircraft (str): Aircraft name
        variables (list): List of variable names to extract
    """
    
    h5_files = glob.glob(os.path.join(h5_directory, pattern))
    
    if not h5_files:
        print(f"No files found matching pattern '{pattern}' in {h5_directory}")
        return
    
    print(f"Found {len(h5_files)} HDF5 files to convert")
    print(f"Metadata: {campaign}, {version}, {aircraft}")
    print(f"Variables: {variables}")
    print("=" * 60)
    
    successful_conversions = 0
    failed_conversions = 0
    
    for i, h5_file in enumerate(h5_files, 1):
        print(f"\n[{i}/{len(h5_files)}]")
        csv_path, shape = h5_to_csv_xarray(h5_file, variables, output_dir, campaign, version, aircraft)
        
        if csv_path:
            successful_conversions += 1
        else:
            failed_conversions += 1
    
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    print(f"✓ Successful: {successful_conversions}")
    print(f"❌ Failed: {failed_conversions}")
    print(f"🏷️  Metadata: {campaign}, {version}, {aircraft}")
    print(f"📁 CSV files saved to: {os.path.abspath(output_dir)}")

def organize_csv_by_date(input_folder, output_folder, new_filename_prefix="PACE_PAX"):
    """
    Organize CSV files into date-based folders and rename them
    
    Args:
        input_folder (str): Path to folder containing CSV files
        output_folder (str): Path to output folder where date folders will be created
        new_filename_prefix (str): New prefix for the files (default: "PACE_PAX")
    """
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Pattern to extract date from filename (YYYYMMDD)
    date_pattern = r'(\d{8})'
    
    # Get all CSV files from input folder
    csv_files = []
    if os.path.isdir(input_folder):
        csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
        csv_files = [os.path.join(input_folder, f) for f in csv_files]
    else:
        print(f"Input folder '{input_folder}' does not exist")
        return
    
    if not csv_files:
        print(f"No CSV files found in '{input_folder}'")
        return
    
    print(f"Found {len(csv_files)} CSV files to organize")
    print("=" * 50)
    
    processed = 0
    errors = 0
    
    for csv_file in csv_files:
        try:
            filename = os.path.basename(csv_file)
            
            # Extract date from filename
            match = re.search(date_pattern, filename)
            if match:
                date_str = match.group(1)
                
                # Create date folder
                date_folder = os.path.join(output_folder, date_str)
                os.makedirs(date_folder, exist_ok=True)
                
                # Create new filename
                new_filename = f"{new_filename_prefix}.csv"
                destination = os.path.join(date_folder, new_filename)
                
                # Copy file to new location with new name
                shutil.copy2(csv_file, destination)
                
                print(f"✓ {filename}")
                print(f"  -> {date_str}/{new_filename}")
                processed += 1
                
            else:
                print(f"❌ No date found in filename: {filename}")
                errors += 1
                
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            errors += 1
    
    print("\n" + "=" * 50)
    print("ORGANIZATION SUMMARY")
    print("=" * 50)
    print(f"✓ Successfully processed: {processed}")
    print(f"❌ Errors: {errors}")
    print(f"📁 Output folder: {os.path.abspath(output_folder)}")
    
    # Show created folders
    if processed > 0:
        print(f"\n📅 Created date folders:")
        for folder in sorted(os.listdir(output_folder)):
            folder_path = os.path.join(output_folder, folder)
            if os.path.isdir(folder_path):
                files_in_folder = len([f for f in os.listdir(folder_path) if f.endswith('.csv')])
                print(f"  {folder}/ ({files_in_folder} files)")