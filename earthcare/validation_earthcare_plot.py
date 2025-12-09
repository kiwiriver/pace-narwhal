import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from datetime import datetime
import matplotlib.cm as cm

def plot_multiple_files_cartopy(file_list, timestamp_col='Date(dd:mm:yyyy)', outfile=None):
    """
    Plot multiple CSV files on a global map with different colors and timestamps
    
    Parameters:
    -----------
    file_list : list
        List of file paths to CSV files
    timestamp_col : str
        Column name containing timestamp information
    """
    # Create the plot
    fig = plt.figure(figsize=(16, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Add map features
    ax.add_feature(cfeature.COASTLINE, alpha=0.5)
    ax.add_feature(cfeature.BORDERS, alpha=0.3)
    ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.3)
    ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.3)
    
    # Define colors and markers for different files
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    markers = ['o', 's', '^', 'v', 'D', '<', '>', 'p', '*', 'h']
    
    # Store data for legend
    legend_elements = []
    all_timestamps = []
    
    for i, file_path in enumerate(file_list):
        try:
            # Read the data
            df = pd.read_csv(file_path)
            
            # Check if required columns exist
            if 'latitude' not in df.columns or 'longitude' not in df.columns:
                print(f"Warning: Required columns not found in {file_path}")
                continue
                
            # Get lat/lon data
            coords_df = df[['latitude', 'longitude']].dropna()
            
            # Get timestamp info if available
            timestamp_info = "Unknown"
            if timestamp_col in df.columns:
                timestamps = df[timestamp_col].dropna().unique()
                if len(timestamps) > 0:
                    timestamp_info = timestamps[0]  # Use first timestamp
                    all_timestamps.extend(timestamps)
            
            if len(coords_df) == 0:
                print(f"Warning: No valid coordinates in {file_path}")
                continue
            
            # Use different color and marker for each file
            color = colors[i % len(colors)]
            marker = markers[i % len(markers)]
            
            # Plot the points
            scatter = ax.scatter(coords_df['longitude'], coords_df['latitude'], 
                               c=color, s=30, alpha=0.7, 
                               marker=marker,
                               transform=ccrs.PlateCarree(),
                               edgecolors='black', linewidth=0.3,
                               label=f'File {i+1}: {timestamp_info} (n={len(coords_df)})')
            
            legend_elements.append(scatter)
            
            print(f"Plotted {len(coords_df)} points from {file_path}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            continue
    
    # Set global extent
    ax.set_global()
    
    # Add gridlines
    gl = ax.gridlines(draw_labels=True, alpha=0.3)
    gl.top_labels = False
    gl.right_labels = False
    
    # Add legend
    if legend_elements:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    # Title with timestamp range
    if all_timestamps:
        unique_dates = sorted(list(set(all_timestamps)))
        if len(unique_dates) == 1:
            date_range = unique_dates[0]
        else:
            date_range = f"{unique_dates[0]} to {unique_dates[-1]}"
        title = f'Global Distribution - Multiple Files\nDate Range: {date_range}'
    else:
        title = 'Global Distribution - Multiple Files'
    
    plt.title(title, fontsize=14, pad=20)
    plt.tight_layout()
    
    if(outfile):
        plt.savefig(outfile, dpi=300)
        
    plt.show()
    
    return fig, ax