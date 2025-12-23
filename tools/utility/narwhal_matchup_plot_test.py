import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature
import numpy as np
from scipy.stats import linregress, gaussian_kde

def plot_csv_on_map(
    file1, file2,
    var,
    lon_col,
    lat_col,
    mode="diff",  # Options: "file1", "file2", "diff", "pct"
    title=None,
    outfile='map.png'
):
    """
    Plots specified mode for `var`:
        mode='file1' : just file1 var
        mode='file2' : just file2 var
        mode='diff'  : file2 - file1
        mode='pct'   : (file2 - file1) / file1 * 100

    Lon/lat are always from file2 for plotting.

    Parameters:
        - file1, file2: Paths to CSV files.
        - var: Name of variable/column to plot/compare.
        - lon_col, lat_col: Names of longitude and latitude columns (from file2).
        - mode: "file1", "file2", "diff", or "pct"
        - title: Plot title (optional).
        - outfile: Output image file name.
    """
    # Load CSV data
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # Basic validation
    if mode in ['diff', 'pct']:
        if var not in df1.columns or var not in df2.columns:
            print(f"Variable '{var}' not found in both CSV files.")
            return
    elif mode == 'file1':
        if var not in df1.columns:
            print(f"Variable '{var}' not found in file1.")
            return
    elif mode == 'file2':
        if var not in df2.columns:
            print(f"Variable '{var}' not found in file2.")
            return
    if lon_col not in df2.columns or lat_col not in df2.columns:
        print(f"Longitude or latitude columns '{lon_col}', '{lat_col}' not found in second CSV file.")
        return

    # Align by row (change to merge as needed)
    minlen = min(len(df1), len(df2))
    lon = df2[lon_col].iloc[:minlen].values
    lat = df2[lat_col].iloc[:minlen].values

    label = None
    if mode == "file1":
        dat = df1[var].iloc[:minlen].values.astype(float)
        label = f"{var} [file1]"
        if title is None:
            title = f"{var} (file1)"
    elif mode == "file2":
        dat = df2[var].iloc[:minlen].values.astype(float)
        label = f"{var} [file2]"
        if title is None:
            title = f"{var} (file2)"
    elif mode == "diff":
        v1 = df1[var].iloc[:minlen].values.astype(float)
        v2 = df2[var].iloc[:minlen].values.astype(float)
        dat = v2 - v1
        label = f"Difference ({var})"
        if title is None:
            title = f"{var} Difference (file2 - file1)"
    elif mode == "pct":
        v1 = df1[var].iloc[:minlen].values.astype(float)
        v2 = df2[var].iloc[:minlen].values.astype(float)
        percent_diff = np.full_like(v1, np.nan)
        mask = v1 != 0
        percent_diff[mask] = (v2[mask] - v1[mask]) / v1[mask] * 100
        dat = percent_diff
        label = f"Percent Difference ({var}) [%]"
        if title is None:
            title = f"{var} Percent Difference (file2 - file1)"

    # Set color limits
    vmax = np.nanmax(np.abs(dat))
    if mode in ['file1', 'file2']:
        vmin = np.nanmin(dat)
        vmax = np.nanmax(dat)
    else:
        vmin = -vmax

    # Plot
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.add_feature(cartopy.feature.OCEAN, edgecolor='w', linewidth=0.01)
    ax.add_feature(cartopy.feature.LAND, edgecolor='w', linewidth=0.01)
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

    sc = plt.scatter(
        lon, lat, c=dat, cmap='sesmic', s=50,
        transform=ccrs.PlateCarree(),
        vmin=vmin, vmax=vmax
    )
    plt.colorbar(sc, orientation='vertical', label=label)
    plt.title(title)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.savefig(outfile, dpi=300)
    print(f"Saved map as: {outfile}")
    plt.show()
    plt.close()