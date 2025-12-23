import os
import glob
from pathlib import Path

def rename_seabass_files(root_dir):
    """
    Rename all files starting with 'SEABASS_Rrs2' to 'SEABASS_ALL_Rrs2' 
    in all subdirectories of root_dir
    """
    
    renamed_count = 0
    errors = []
    
    print(f"Searching for SEABASS_Rrs2*.csv files in: {root_dir}")
    
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            # Check if file starts with SEABASS_Rrs2 and ends with .csv
            if filename.startswith('SEABASS_Rrs2') and filename.endswith('.csv'):
                
                # Create new filename
                new_filename = filename.replace('SEABASS_Rrs2', 'SEABASS_ALL_Rrs2', 1)
                
                # Full paths
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_filename)
                
                try:
                    # Rename the file
                    os.rename(old_path, new_path)
                    print(f"✅ Renamed: {filename} -> {new_filename}")
                    print(f"   Path: {root}")
                    renamed_count += 1
                    
                except Exception as e:
                    error_msg = f"❌ Failed to rename {old_path}: {str(e)}"
                    print(error_msg)
                    errors.append(error_msg)
    
    print(f"\n📊 Summary:")
    print(f"   Files renamed: {renamed_count}")
    print(f"   Errors: {len(errors)}")
    
    if errors:
        print("\n❌ Errors encountered:")
        for error in errors:
            print(f"   {error}")
    
    return renamed_count, errors

# Usage
root_directory = "aeronet_oc"
renamed_count, errors = rename_seabass_files(root_directory)
