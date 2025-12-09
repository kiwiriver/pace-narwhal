"""
major functions to do matchups

todo:
refine the range of tspan based on the data read from validation, so narrow down datadownload
    from tools.aeronet_matchup_man import get_man_all
    
    tspan=('2024-09-06', '2024-09-06')
    loc_search_path='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data_split/HSRL2_R1/'
    aeronet_list_df1 = get_man_all(loc_search_path, tspan, flag_man=True, flag_list=False)

"""

import os
import re
import pickle
import glob
import shutil
import sys

import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from tqdm import tqdm 
from datetime import datetime
import matplotlib.pyplot as plt

from tools.aeronet_matchup_extract import subset_time_pace_aeronet, subset_loc_pace_data, \
                                            prepare_date, prepare_vars
from tools.narwhal_matchup_plot import plot_corr_one_density_kde, plot_four_csv_maps
from tools.narwhal_tools import find_closest_wavelength_vars
from tools.aeronet_matchup_man import get_man_all

from tools.aeronet_matchup_download import get_aeronet_file, process_local_nc_files
from tools.narwhal_pace import download_pace_data
from tools.aeronet_matchup_search import aeronet_search, plot_search
from tools.aeronet_matchup_format import clean_pace_data

from tools.aeronet_matchup_html_suite import create_html_with_embedded_images
from tools.aeronet_matchup_order import get_image_files,ordered_image_list
from tools.aeronet_tools import get_rules_str, get_filter_rules, clean_value

from tools.aeronet_oc import get_f0_tsis

def aeronet_matchup_summary(matchup_save_folder, matchup_save_folder2, html_save_folder,\
                            val_url, val_path1, loc_suite1, tspan, \
                            product1, appkey, api_key, \
                            save_path1, l2_data_folder, \
                            all_rules, \
                            save_subset_loc_path, share_dir_base,\
                            val_source='AERONET', flag_rm=True, flag_earthdata_cloud=False, \
                            df0=None, logo_path=None):
    """
    define the main function to run matchup

    List of all variables:
        matchup_save_folder
        matchup_save_folder2
        
        val_url
        val_path1
        loc_suite1: search this path to get all lococation, usually under one of the data suites
            set the same as val_path1
        tspan
        product1
        appkey
        api_key
        save_path1
        
    
        l2_data_folder
    
        search_center_radius
    
        filter_rules
        search_grid_delta
        save_subset_loc_path
    
        share_dir_base

        val_source
        flag_rm
        flag_earthdata_cloud


    Path example:
      /val5/test0/harp2_fastmapol/pace_pace_pax_c5.0_r10_h2.0_chi22.0_nvref30_nvdolp30_qf5
      data_l1c  data_l2  html  matchup  plot  summary
           data_l1c
           data_l2
           matchup: /daily path: /plot, /csv
           html: html files
    """

    search_center_radius = all_rules['search_center_radius']
    search_grid_delta = all_rules['search_grid_delta']
    delta_hour = all_rules['delta_hour']
    
    all_rules_str = get_rules_str(all_rules)
    print("all_rules_str:", all_rules_str)
    
    filter_rules = get_filter_rules(all_rules)

    if(val_source.upper() in ['AERONET', 'AERONET_OC']):
        print("search path for AERONETR locations:", matchup_save_folder)
        if(val_url):
            #if url is provided, load this url
            url_file = os.path.join(matchup_save_folder, val_url.split('/')[-1])
            aeronet_list_df1 = get_aeronet_file(url_file, val_url)
        else:
            #if not provided, search the path
            #loc_suite1 = 'AOD15'
            loc_search_path = os.path.join(val_path1, loc_suite1)
            print("search path for AERONET or AERONET OC locations:", loc_search_path)
            aeronet_list_df1 = get_man_all(loc_search_path, tspan, flag_man=False, flag_list=True)
        print(f"finish for {val_source} data")
        
    elif(val_source.upper() in ['MAN','PACE_PAX', 'EARTHCARE']):
        #default search the man aod path
        #loc_suite1 = 'MAN_AOD15_series'
        loc_search_path = os.path.join(val_path1, loc_suite1)
        print("search path for MAN/PACE_PAX/EARTHCARE locations:", loc_search_path)
        aeronet_list_df1 = get_man_all(loc_search_path, tspan, flag_list=True)
        print(f"finish for {val_source} data")
    else:
        print(f"{val_source} do not exist")
        exit
    
    aeronet_len = len(aeronet_list_df1)
    print("===total number of sites in aeronet/man data:", aeronet_len)

    filename = f"val_locations_{loc_suite1}_n{aeronet_len}.csv"
    path1 = os.path.join(matchup_save_folder2, filename)
    print("===save location file to:", path1)
    aeronet_list_df1.to_csv(path1,index=False)

    if aeronet_len <= 0:
        sys.exit("No data found in aeronet/man data, EXIT")
        
    #######################################################################################################
    if(l2_data_folder == None):
        l2_path1, l1c_path, plot_path, html_path = download_pace_data(tspan, product1, appkey, api_key, \
                                                                      path1=save_path1, \
                                                                      flag_earthdata_cloud=flag_earthdata_cloud)
    else:
        print(f"Using local L2 data folder: {l2_data_folder}")
        # Validate that the specified folder exists
        if not os.path.exists(l2_data_folder):
            raise ValueError(f"Specified L2 data folder does not exist: {l2_data_folder}")
        
        # Check if folder contains any .nc files
        nc_files = glob.glob(os.path.join(l2_data_folder, '*.nc'))
        if not nc_files:
            print(f"Warning: No .nc files found in {l2_data_folder}")
        
        # Process local files and copy those in time range
        l2_path1, l1c_path, plot_path, html_path = process_local_nc_files(tspan, l2_data_folder, product1, \
                                                                           path1=save_path1)
        
        print(f"Local data processing complete. Files copied to: {l2_path1}")
    
    print("l2_path1:", l2_path1)

    #######################################################################################################

    #### list all l2 data and match with aeronet locations
    #everything in the l2_path1, could include multiple days
    filev=glob.glob(os.path.join(l2_path1,'*.nc'))
    print("total files:", len(filev))
    #search_center_radius = 5 #km #center distance
    indexvv, boundingboxv = aeronet_search(aeronet_list_df1, filev, search_center_radius=search_center_radius)
    
    #### plot the matched aeronet location in l2 locations
    #### check matched points
    
    out_dir1 = os.path.join(matchup_save_folder2, 'csv')
    out_dir2 = os.path.join(matchup_save_folder2, 'plot')
    
    print("output dir", out_dir1)
    print("output dir", out_dir2)
    os.makedirs(out_dir1, exist_ok=True)
    os.makedirs(out_dir2, exist_ok=True)

    outfile=os.path.join(out_dir2, product1+'_'+tspan[0]+'-'+tspan[1]+f'_{val_source.lower()}_matchup.png')
    print(outfile)
    
    plot_search(indexvv, boundingboxv, outfile)
    
    ##### create df based on the matched data, and compute mean and std within a grid range
    #search_grid_delta=2
    ## turn off temp
    try:
        pace_df_mean_all, pace_df_std_all, wvv = subset_loc_pace_data(indexvv, filev, filter_rules, \
                                                            search_grid_delta=search_grid_delta,\
                                                            save_subset_loc_path=save_subset_loc_path)
    #turn off except
    except:
        sys.exit("Cannot find pace matchups based on locations")

    print("number of all pixel found:", len(pace_df_mean_all))
    pace_df_mean_all, pace_df_std_all = clean_pace_data(pace_df_mean_all, pace_df_std_all)
    print("number of non-nan pixel found:", len(pace_df_mean_all))
    
    wvv = [int(wv1) for wv1 in wvv] #use integer
    print("PACE wavelength:", wvv)
    #wvv=[440, 550, 670, 870]
    target=550 #find closet wavelength
    wv550 = min(list(wvv), key=lambda x: abs(x - target))
    print("make plots for wavelenth close to 550", wv550)


    #### get the list of date:
    date_list = sorted(set(pace_df_mean_all['datetime'].dt.strftime('%Y-%m-%d').tolist()))

    print("*************************************************************")
    if(len(date_list)<1):
        print("****NO PACE Data Available during this time period, Skip****")
        pass
    else:
        print("**** number and list of days of data in PACE found:", len(date_list), date_list)
    print("*************************************************************")
    
    #### match with aeronet time
    print("*************************************************************")
    site1v = sorted(pace_df_mean_all['site'].unique())
    print("**** number and list of AERONET sites collocated with PACE lat/lon:", len(site1v), site1v)
    print("*************************************************************")

    ##############################################################################################################
    #aeronet_path1='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data_split/'
    #suite1='AOD15' #ALM15  AOD15  LWN15  MAN_AOD15  MAN_SDA15  SDA15
    #----------------------------------------------------------------------------------------------------

    current_module_path = Path(__file__).parent.absolute()
    print("Current module directory:", current_module_path)

    df_var = pd.read_csv(os.path.join(current_module_path, 'val_var_list.csv'),skipinitialspace=True)
    # Filter by val_source
    df_var1 = df_var.loc[df_var.val_source == val_source]

    # Process each row using itertuples (faster than iterrows)
    for row in df_var1.itertuples(index=False):
        print('-------------------------------------------------')
    
        # Unpack the row directly
        val_source_row, suite1, old_start1, old_end1, new_start1, wvv_option = row
        input_is_sda = isinstance(suite1, str) and ('SDA' in suite1.upper())
        
        # Handle wavelength dependency
        if wvv_option == 'wvv':
            wvv_input = wvv  # assuming 'wvv' is defined elsewhere in your code
        else:
            wvv_input = None
    
        # Your processing logic here
        print(f"Processing: {suite1}, {old_start1}, {old_end1}, {new_start1}, {wvv_input}")

        #for each variable separately
        #try:
        get_matchup_results(out_dir1, out_dir2, tspan, \
                            date_list, val_path1, site1v, product1, suite1, \
                            pace_df_mean_all, pace_df_std_all,\
                            old_start1, old_end1, new_start1, wvv_input, delta_hour, \
                            input_is_sda=input_is_sda, wv550=wv550, \
                            val_source=val_source, df0=df0)

        #turn off except
        #except:
        #    print("no valid results from get_matchup_results ")

        
    #################################################################################
    ## make more plot for example cases
    cases = [
        {
            'suite1': 'AOD15',
            'file1': os.path.join(out_dir1, 'AOD15_aot_wv_all_target_mean_df.csv'),
            'file2': os.path.join(out_dir1, 'AOD15_aot_wv_all_pace_mean_df.csv'),
            'var': f'aot_wv{wv550}',
            'lon_col': 'aeronet_lon',
            'lat_col': 'aeronet_lat',
            'var_range': [0, 0.3],
            'diff_range': [-0.3, 0.3],
            'pct_range': [-100, 100],
        },
        {
            'suite1': 'ALM15',
            'file1': os.path.join(out_dir1, 'ALM15_ssa_wv_all_target_mean_df.csv'),
            'file2': os.path.join(out_dir1, 'ALM15_ssa_wv_all_pace_mean_df.csv'),
            'var': f'ssa_wv{wv550}',
            'lon_col': 'aeronet_lon',
            'lat_col': 'aeronet_lat',
            'var_range': [0.7, 1.0],
            'diff_range': [-0.3, 0.3],
            'pct_range': [-100, 100],
        },
        {
            'suite1': 'HYB15',
            'file1': os.path.join(out_dir1, 'HYB15_ssa_wv_all_target_mean_df.csv'),
            'file2': os.path.join(out_dir1, 'HYB15_ssa_wv_all_pace_mean_df.csv'),
            'var': f'ssa_wv{wv550}',
            'lon_col': 'aeronet_lon',
            'lat_col': 'aeronet_lat',
            'var_range': [0.7, 1.0],
            'diff_range': [-0.3, 0.3],
            'pct_range': [-100, 100],
        }
    ] 
    
    for case in cases:
        try:
            outfile = os.path.join(
                out_dir2,
                f"{product1}_{tspan[0]}-{tspan[1]}_{case['suite1']}_{case['var']}_validation_diff.png"
            )
            title = f"Global Map: {case['var']} (AERONET vs PACE)"
            file1, file2 = case['file1'], case['file2']
            if os.path.isfile(file1) and os.path.isfile(file2):
                plot_four_csv_maps(
                    file1,
                    file2,
                    case['var'],
                    case['lon_col'],
                    case['lat_col'],
                    suptitle=title,
                    outfile=outfile,
                    var_range=case['var_range'],
                    diff_range=case['diff_range'],
                    pct_range=case['pct_range']
                )
        except:
            print("skip plot for ", case['var'])


    ###########################
    # Example usage:

    print("==arrange image order for html==")
    file_path=out_dir2
    image_files = get_image_files(file_path)
    #ordered_files = final_ordered_image_list(image_files)
    prior = ["validation_matchup", "validation_diff"]
    ordered_files = ordered_image_list(image_files, priority_substrings=prior)

    #only create html when there is more than one images
    if(len(ordered_files)>0):
        # Now use ordered_files in your HTML generator!
        html_str = f"{all_rules_str}_all"
        html_file = f"val_{tspan[0]}-{tspan[1]}_{html_str}_validation_matchup.html"
        print("html_file:", html_file)
        local_html=os.path.join(html_save_folder, html_file)
        
        title=f"{product1.upper()} Validation with {val_source.upper()}" 
        title2=f"{tspan[0]}-{tspan[1]}: {all_rules_str}"
        
        create_html_with_embedded_images(file_path, ordered_files, output_html=local_html,\
                                         title=title, title2=title2,\
                                         resolution_factor=2, quality=85, logo_path=logo_path)
    
        #### copy to share folder
        #share_dir_base = "/mnt/mfs/FILESHARE/meng_gao/pace/validation"
        share_dir = f"{share_dir_base}/daily/{product1}/pace_{val_source.lower()}_{all_rules_str}"
        os.makedirs(share_dir, exist_ok=True)
        share_html = os.path.join(share_dir, html_file)

        shutil.copy(local_html, share_html)
        print(f"Copied to: {share_html}")
    
    ###########################
    try:
        print("l2_path1:", l2_path1)

        if(flag_rm):
            pathv = [l2_path1]
            for path1 in pathv:
                try:
                    shutil.rmtree(path1)  # Recursively remove the folder and its contents
                    print(f"✅ Folder removed: {path1}")
                except:
                    print("do not exist", path1)
    except:
        print("l2_path1 not available")
        
###################################################################################


def process_all_folders(folder1v, site1v, pace_df_mean_all, pace_df_std_all, wvv_input, all_vars, 
                       extra_vars=None, delta_hour=None, old_start1=None, old_end1=None, 
                       new_start1=None, input_is_sda=False, val_source='AERONET', df0=None):
    """
    Process all folders and combine the resulting DataFrames.
    
    Parameters:
    -----------
    folder1v : list
        List of folder paths to process
    site1v : various
        Site parameter for match_pace_aeronet function
    pace_df_mean_all : DataFrame
        Mean data DataFrame
    pace_df_std_all : DataFrame
        Standard deviation data DataFrame
    wvv_input : various
        Wavelength input parameter
    all_vars : various
        Variables parameter
    extra_vars : various, optional
        Extra variables parameter
    delta_hour : float, optional
        Time delta in hours
    old_start1, old_end1, new_start1 : various, optional
        Time range parameters
    input_is_sda : bool, optional
        SDA input flag (default: False)
    
    Returns:
    --------
    tuple : (combined_target_mean_df, combined_target_std_df, 
             combined_pace_mean_df, combined_pace_std_df)
        Combined DataFrames from all processed folders
    """
    
    # Initialize empty lists to store DataFrames from each folder
    aeronet_df_mean_alls = []
    aeronet_df_std_alls = []
    pace_df_mean_alls = []
    pace_df_std_alls = []
    
    print(f"Processing {len(folder1v)} folders...")
    
    for folder1 in tqdm(folder1v):
        #print(f"Processing folder {i+1}/{len(folder1v)}: {folder1}")
        
        #with open("pace2.pkl", "wb") as f:
        #    pickle.dump([folder1, site1v, pace_df_mean_all, pace_df_std_all, wvv_input, all_vars, \
        #                       extra_vars, delta_hour,\
        #                      old_start1, old_end1, new_start1,\
        #                      input_is_sda, val_source], f)

        #print(f"old_start1={old_start1}, old_end1={old_end1}, new_start1={new_start1}")
        old_start1, old_end1, new_start1 = map(clean_value, [old_start1, old_end1, new_start1])
        #print(f"old_start1={old_start1}, old_end1={old_end1}, new_start1={new_start1}")
        
        try:
            aeronet_df_mean_all, aeronet_df_std_all, pace_df_mean_all, pace_df_std_all = \
                subset_time_pace_aeronet(folder1, site1v, \
                                         pace_df_mean_all, pace_df_std_all, wvv_input, all_vars, \
                                   extra_vars=extra_vars, delta_hour=delta_hour,\
                                  old_start1=old_start1, old_end1=old_end1, new_start1=new_start1,\
                                  input_is_sda=input_is_sda, val_source=val_source, df0=df0)
            
            # Append each DataFrame to the respective list (only if not empty/None)
            if aeronet_df_mean_all is not None and not aeronet_df_mean_all.empty:
                aeronet_df_mean_alls.append(aeronet_df_mean_all)
                print(f"  Added AERONET mean data: {aeronet_df_mean_all.shape}")
            
            if aeronet_df_std_all is not None and not aeronet_df_std_all.empty:
                aeronet_df_std_alls.append(aeronet_df_std_all)
                print(f"  Added AERONET std data: {aeronet_df_std_all.shape}")
            
            if pace_df_mean_all is not None and not pace_df_mean_all.empty:
                pace_df_mean_alls.append(pace_df_mean_all)
                print(f"  Added PACE mean data: {pace_df_mean_all.shape}")
            
            if pace_df_std_all is not None and not pace_df_std_all.empty:
                pace_df_std_alls.append(pace_df_std_all)
                print(f"  Added PACE std data: {pace_df_std_all.shape}")

        #turn off except        
        except Exception as e:
            print(f"  Error processing folder {folder1}: {str(e)}")
            continue
    
    # Combine all DataFrames
    print("\nCombining DataFrames...")
    
    combined_target_mean_df = pd.concat(aeronet_df_mean_alls, ignore_index=True) \
        if aeronet_df_mean_alls else pd.DataFrame()
    combined_target_std_df = pd.concat(aeronet_df_std_alls, ignore_index=True) \
        if aeronet_df_std_alls else pd.DataFrame()
    combined_pace_mean_df = pd.concat(pace_df_mean_alls, ignore_index=True) \
        if pace_df_mean_alls else pd.DataFrame()
    combined_pace_std_df = pd.concat(pace_df_std_alls, ignore_index=True) \
        if pace_df_std_alls else pd.DataFrame()
    
    # Print summary
    print(f"\nFinal combined DataFrames shapes:")
    print(f"  AERONET mean: {combined_target_mean_df.shape}")
    print(f"  AERONET std: {combined_target_std_df.shape}")
    print(f"  PACE mean: {combined_pace_mean_df.shape}")
    print(f"  PACE std: {combined_pace_std_df.shape}")
    
    return combined_target_mean_df, combined_target_std_df, combined_pace_mean_df, combined_pace_std_df

def get_matchup_results(out_dir1, out_dir2, tspan, date_list, \
                        aeronet_path1, site1v, product1, suite1, \
                        pace_df_mean_all, pace_df_std_all,\
                        old_start1, old_end1, new_start1, wvv_input, delta_hour,\
                        input_is_sda=False, wv550=550, val_source='AERONET', df0=None):
    """
    get the final matchpu results, and make plots
    wvv_input=None for variable do not have a wv dimension

    if date_list include several days, multiple days of aeronet data will be loaded.
    
    """

    all_vars, select_vars = prepare_vars(wvv_input, var_pattern=new_start1)
    extra_vars=['timestamp', 'pace_date', 'aot_wv'+str(wv550), 'chi2', 'count', 'nv_ref','nv_dolp', 'quality_flag',\
                'aeronet_lon', 'aeronet_lat', 'pace_lon','pace_lat',\
                'pace_loc_index_lon','pace_loc_index_lat',\
                'distance1_haversine','distance2_euclidean']

    #datetime	pace_date	timestamp	site_index	site
    
    print("all_vars", all_vars)
    print("select_vars", select_vars)
    print("extra_vars", extra_vars)

    folder1v=prepare_date(aeronet_path1, suite1, date_list)
        
    aeronet_df_mean_all, aeronet_df_std_all, pace_df_mean_all, pace_df_std_all = \
        process_all_folders(folder1v, site1v, pace_df_mean_all, pace_df_std_all, wvv_input, all_vars, 
                               extra_vars=extra_vars, delta_hour=delta_hour,\
                              old_start1=old_start1, old_end1=old_end1, new_start1=new_start1,\
                              input_is_sda=input_is_sda, val_source=val_source, df0=df0)
    #save data
    #AOD15_aot_wv_all_target_mean_df.csv
    dfs_to_save = [
        (aeronet_df_mean_all, suite1+'_'+new_start1+'_all_target_mean_df.csv'),
        (aeronet_df_std_all, suite1+'_'+new_start1+'_all_target_std_df.csv'),
        (pace_df_mean_all, suite1+'_'+new_start1+'_all_pace_mean_df.csv'),
        (pace_df_std_all, suite1+'_'+new_start1+'_all_pace_std_df.csv'),
        ]
        
    for df, filename in dfs_to_save:
        df.to_csv(os.path.join(out_dir1, filename), index=False,float_format='%.6f')
            

    #make density plots
    try:
        if 'spexone' in product1.lower() and wvv_input is not None and len(wvv_input) > 0:
            var_list = select_vars
            targets = [440, 550, 670, 870]
            screened_vars = find_closest_wavelength_vars(var_list, targets)
            print(screened_vars)
        else:
            screened_vars = select_vars
        
        for var1 in screened_vars:
            x = aeronet_df_mean_all[var1].values
            y = pace_df_mean_all[var1].values
            
            title1=suite1+'_'+var1+'_'+tspan[0]+'-'+tspan[1]
            
            fileout1=os.path.join(out_dir2, suite1+'_'+var1+'_corr.png')
            
            plot_corr_one_density_kde(
                x, y, label=var1, title=title1, fileout=fileout1,
                xlabel="Validation Target", ylabel="PACE"
            )
    except:
        print("nothing to plot")
        
    return aeronet_df_mean_all, aeronet_df_std_all, pace_df_mean_all, pace_df_std_all