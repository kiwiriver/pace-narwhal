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

def plot_four_csv_maps(
    file1, file2,
    var,
    lon_col,
    lat_col,
    suptitle=None,
    outfile='four_maps.png',
    file1_label='Validation Target',
    file2_label='PACE',
    pct_range=[-100, 100],
    var_range=[0, 0.3],
    diff_range=[-0.3, 0.3],
    edgecolor="k",
    linewidth=0.5,
    cm1='viridis',
    cm2='seismic',
):
    """
    cm1='viridis',
    cm2='RdBu',
    """

    # Read data from CSV
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    minlen = min(len(df1), len(df2))
    lon = df2[lon_col].iloc[:minlen].values
    lat = df2[lat_col].iloc[:minlen].values
    v1 = df1[var].iloc[:minlen].values.astype(float)
    v2 = df2[var].iloc[:minlen].values.astype(float)
    diff = v2 - v1
    pct = np.full_like(diff, np.nan)
    mask_valid_pct = (v1 != 0)
    pct[mask_valid_pct] = (v2[mask_valid_pct] - v1[mask_valid_pct]) / v1[mask_valid_pct] * 100

    # Combined mask: Only plot locations where **both** are valid
    mask = ~np.isnan(v1) & ~np.isnan(v2)

    # For percent diff: also require valid pct value
    mask_pct = mask & ~np.isnan(pct)

    # Subplot grid
    fig, axs = plt.subplots(2, 2, figsize=(18, 10),
                           subplot_kw={'projection': ccrs.PlateCarree()})

    # FILE1
    ax = axs[0, 0]
    ax.set_global()
    ax.add_feature(cartopy.feature.OCEAN, edgecolor='w', linewidth=0.01)
    ax.add_feature(cartopy.feature.LAND, edgecolor='w', linewidth=0.01)
    gridliner = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
    gridliner.right_labels = False
    vmin1, vmax1 = var_range
    sc1 = ax.scatter(
        lon[mask], lat[mask], c=v1[mask],
        cmap=cm1, s=50, vmin=vmin1, vmax=vmax1,
        edgecolors=edgecolor, linewidths=linewidth, transform=ccrs.PlateCarree()
    )
    plt.colorbar(sc1, ax=ax, orientation='vertical', label=f'{var} ({file1_label})')
    ax.set_title(f'{var} from {file1_label}')

    # FILE2
    ax = axs[0, 1]
    ax.set_global()
    ax.add_feature(cartopy.feature.OCEAN, edgecolor='w', linewidth=0.01)
    ax.add_feature(cartopy.feature.LAND, edgecolor='w', linewidth=0.01)
    gridliner = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
    gridliner.right_labels = False
    vmin2, vmax2 = var_range
    sc2 = ax.scatter(
        lon[mask], lat[mask], c=v2[mask],
        cmap=cm1, s=50, vmin=vmin2, vmax=vmax2,
        edgecolors=edgecolor, linewidths=linewidth, transform=ccrs.PlateCarree()
    )
    plt.colorbar(sc2, ax=ax, orientation='vertical', label=f'{var} ({file2_label})')
    ax.set_title(f'{var} from {file2_label}')


    
    # DIFF
    ax = axs[1, 0]
    ax.set_global()
    ax.add_feature(cartopy.feature.OCEAN, edgecolor='w', linewidth=0.01)
    ax.add_feature(cartopy.feature.LAND, edgecolor='w', linewidth=0.01)
    gridliner = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
    gridliner.right_labels = False
    vmin_diff, vmax_diff = diff_range
    sc3 = ax.scatter(
        lon[mask], lat[mask], c=diff[mask],
        cmap=cm2, s=50, vmin=vmin_diff, vmax=vmax_diff,
        edgecolors=edgecolor, linewidths=linewidth, transform=ccrs.PlateCarree()
    )
    plt.colorbar(sc3, ax=ax, orientation='vertical', label=f'Difference ({var})')
    ax.set_title(f'{var} Difference ({file2_label}-{file1_label})')

    # PCT (require file1, file2, and pct all to be valid)
    ax = axs[1, 1]
    ax.set_global()
    ax.add_feature(cartopy.feature.OCEAN, edgecolor='w', linewidth=0.01)
    ax.add_feature(cartopy.feature.LAND, edgecolor='w', linewidth=0.01)
    gridliner = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
    gridliner.right_labels = False
    vmin_pct, vmax_pct = pct_range
    sc4 = ax.scatter(
        lon[mask_pct], lat[mask_pct], c=pct[mask_pct],
        cmap=cm2, s=50, vmin=vmin_pct, vmax=vmax_pct,
        edgecolors=edgecolor, linewidths=linewidth, transform=ccrs.PlateCarree()
    )
    plt.colorbar(sc4, ax=ax, orientation='vertical', label=f'Percent Diff ({var}) [%]')
    ax.set_title(f'{var} Percent Difference')

    if suptitle:
        plt.suptitle(suptitle, fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(outfile, dpi=300)
    print(f"Saved 2x2 map grid as: {outfile}")
    plt.show()

############################################  

def color_kde_scatter(ax, x, y, s=8, cmap='jet'):
    """
    plot kde
    """
    
    #print('x data:',x)
    #print('y data',y)
    
    if len(x) > 1:
        xy = np.vstack([x, y])
        z = gaussian_kde(xy)(xy)
        idx = z.argsort()
        x1, y1, z1 = x[idx], y[idx], z[idx]
        z1 = z1 / z1.max()
        sc = ax.scatter(x1, y1, c=z1, s=s, alpha=1, cmap=cmap, edgecolors=None, linewidth=0.005)
    else:
        sc = ax.scatter(x, y, s=s, alpha=1, color='gray', edgecolors=None, linewidth=0.005)
        
    return sc

def plot_corr_one_density_kde(
    x, y, label, title=None, fileout=None,
    xlabel="Validation Target", ylabel="PACE", buffer_frac=0.1,
    reference='x'
):
    x = np.asarray(x)
    y = np.asarray(y)

    # Remove NaNs and infs from both
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    n = len(x)

    if n == 0:
        min1, max1 = 0, 1
    else:
        allvals = np.concatenate([x, y])
        data_min = float(np.nanmin(allvals))
        data_max = float(np.nanmax(allvals))
        data_range = data_max - data_min if data_max > data_min else 1
        min1 = data_min - buffer_frac * data_range
        max1 = data_max + buffer_frac * data_range

    # For Bland-Altman
    if(reference=='x'):
        mean_vals = x
        ba_label=f"{xlabel}"
    elif(reference=='mean'):
        mean_vals = (x + y) / 2
        ba_label=f"({xlabel}+{ylabel})/2"
        
    diff_vals = y - x

    corr = np.corrcoef(x, y)[0, 1] if n > 1 else np.nan
    mean_diff = np.mean(diff_vals) if n > 0 else np.nan
    std_diff = np.std(diff_vals, ddof=1) if n > 1 else np.nan
    if n > 1:
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
    else:
        slope, intercept = np.nan, np.nan

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))  # Adjusted figsize for better display

    # Panel 1: x vs y colored by KDE density
    color_kde_scatter(axes[0, 0], x, y, s=20, cmap='jet')
    
    axes[0, 0].plot([min1, max1], [min1, max1], 'k--', label="1:1 line")
    axes[0, 0].set_xlim(min1, max1)
    axes[0, 0].set_ylim(min1, max1)
    axes[0, 0].set_xlabel(xlabel)
    axes[0, 0].set_ylabel(ylabel)
    if title is not None:
        axes[0, 0].set_title(title)
    axes[0, 0].legend(loc="best")

    txt1 = (
        f"n = {n}\n"
        f"corr = {corr:.3f}\n"
        f"y = {slope:.3f} x + {intercept:.3f}"
    )
    axes[0, 0].text(
        0.05, 0.95, txt1, transform=axes[0, 0].transAxes,
        fontsize=10, va='top', ha='left',
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
    )

    # Panel 2: Bland-Altman (mean vs diff) colored by KDE density
    color_kde_scatter(axes[0, 1], mean_vals, diff_vals, s=8, cmap='jet')
    # Add a small buffer to x limits on BA plot as well:
    if len(mean_vals) > 0:
        mean_min = float(np.nanmin(mean_vals))
        mean_max = float(np.nanmax(mean_vals))
        mean_range = mean_max - mean_min if mean_max > mean_min else 1
        ba_min = mean_min - buffer_frac * mean_range
        ba_max = mean_max + buffer_frac * mean_range
        axes[0, 1].set_xlim(ba_min, ba_max)
    if len(diff_vals) > 0:
        diff_min = float(np.nanmin(diff_vals))
        diff_max = float(np.nanmax(diff_vals))
        diff_range = diff_max - diff_min if diff_max > diff_min else 1
        ba_ymin = diff_min - buffer_frac * diff_range
        ba_ymax = diff_max + buffer_frac * diff_range
        axes[0, 1].set_ylim(ba_ymin, ba_ymax)
    axes[0, 1].axhline(0, color='k', linestyle='--', lw=1)
    axes[0, 1].set_xlabel(ba_label)
    axes[0, 1].set_ylabel(f"{ylabel} - {xlabel}")

    txt2 = (
        f"n = {n}\n"
        f"mean(y-x) = {mean_diff:.4f}\n"
        f"std(y-x) = {std_diff:.4f}"
    )
    axes[0, 1].text(
        0.05, 0.95, txt2, transform=axes[0, 1].transAxes,
        fontsize=10, va='top', ha='left',
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
    )

    # Panel 3: Distribution of x and y values
    if n > 0:
        bins = np.linspace(min1, max1, 30)
        axes[1, 0].hist(x, bins=bins, alpha=0.6, label=xlabel, color='blue')
        axes[1, 0].hist(y, bins=bins, alpha=0.6, label=ylabel, color='red')
        axes[1, 0].set_xlabel("Value")
        axes[1, 0].set_ylabel("Frequency")
        #axes[1, 0].set_title(f"Distribution of {xlabel} and {ylabel}")
        axes[1, 0].legend(loc="best")
    else:
        axes[1, 0].text(0.5, 0.5, "No data available", 
                       ha='center', va='center', transform=axes[1, 0].transAxes)
    
    # Panel 4: Distribution of differences (y-x)
    if n > 0:
        diff_range = max(abs(diff_min), abs(diff_max))
        diff_bins = np.linspace(-diff_range*1.1, diff_range*1.1, 30)
        axes[1, 1].hist(diff_vals, bins=diff_bins, alpha=0.7, color='green')
        axes[1, 1].axvline(0, color='k', linestyle='--', lw=1)
        axes[1, 1].axvline(mean_diff, color='r', linestyle='-', lw=2, label=f"Mean: {mean_diff:.3f}")
        axes[1, 1].axvline(mean_diff + std_diff, color='r', linestyle=':', lw=1, label=f"+1σ: {(mean_diff + std_diff):.3f}")
        axes[1, 1].axvline(mean_diff - std_diff, color='r', linestyle=':', lw=1, label=f"-1σ: {(mean_diff - std_diff):.3f}")
        axes[1, 1].set_xlabel(f"{ylabel} - {xlabel}")
        axes[1, 1].set_ylabel("Frequency")
        #axes[1, 1].set_title("Distribution of Differences")
        axes[1, 1].legend(loc="best")
    else:
        axes[1, 1].text(0.5, 0.5, "No data available", 
                       ha='center', va='center', transform=axes[1, 1].transAxes)
    
    plt.tight_layout()
    if fileout:
        plt.savefig(fileout, dpi=300)
    plt.show()
        


def plot_corr_diff_loc_index(all_target_mean_df, all_pace_mean_df, select_vars, title=None, fileout=None):
    plt.figure(figsize=(4,3))
    for var1 in select_vars:
        plt.plot(abs(all_pace_mean_df.pace_loc_index_lon-259),all_target_mean_df[var1]-all_pace_mean_df[var1],'.', label=var1)
    plt.title(title)
    
    plt.xlabel("Validation Target")
    plt.ylabel("PACE")
    plt.legend(loc=(1.01,0))
    plt.savefig(outfile, dpi=300)
    
def plot_corr(all_target_mean_df, all_pace_mean_df, select_vars, range1=(0,1), title=None, fileout=None):
    min1, max1 = range1
    plt.figure(figsize=(4,3))
    for var1 in select_vars:
        plt.plot(all_target_mean_df[var1],all_pace_mean_df[var1],'.', label=var1)
    plt.plot([min1, max1],[min1,  max1])
    plt.title(title)
    
    plt.xlabel("Validation Target")
    plt.ylabel("PACE")
    plt.legend(loc=(1.01,0))
    plt.savefig(outfile, dpi=300)