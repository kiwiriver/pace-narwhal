"""
when set mask on data, set aod between 0-max
for other optical and microphysical based on aod in [min, max]

"""
import glob
import os
import sys
from pathlib import Path
import shutil
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from tools.narwhal_matchup_plot import plot_four_csv_maps, plot_corr_one_density_kde, get_global_map
from tools.narwhal_matchup_html_suite import create_html_with_embedded_images_and_buttons, format_html_info_matchup
from tools.narwhal_matchup_order import get_image_files,ordered_image_list
from tools.narwhal_csv import reformat_csv

def narwhal_combine_summary(product1, path_dict, tspan, chi2_max1, nv_min1, min_aod1, max_aod1, \
                            all_rules=None, val_source='AERONET', logo_path=None):
    """
    put all things together

    These are subset rules after the matchups for refined analysis:
        chi2_max1, nv_min1, min_aod1, max_aod1

    matchup_daily_folder: where daily matchup is
    summary_folder_csv/plot: where summary result is
    


    To do: 
        think about how to deal with variable with large spatial variablity

    local path:
                    /accounts/mgao1/mfs_pace/pace/validation/val5/test0/
                    harp2_fastmapol/pace_pace_pax_c5.0_r10_h2.0_chi22.0_nvref30_nvdolp30_qf5/
                    summary/date_20240701-20250731/csv_nv30_minaod0.1_maxaod1/
                    HSRL2_R1_alh

                    /accounts/mgao1/mfs_pace/pace/validation/val5/test0/
                    harp2_fastmapol/pace_earthcare_c5.0_r10_h2.0_chi22.0_nvref30_nvdolp30_qf5/
                    summary/date_20240701-20250731/csv_nv30_minaod0.1_maxaod1/
                    /ATL_ALD_2A_alh

    share path: 
                   old: /mnt/mfs/FILESHARE/meng_gao/pace/validation/summary/spexone_fastmapol/val_earthcare/date_20240701-20250731
                   
                   new: /mnt/mfs/FILESHARE/meng_gao/pace/validation/share/
                       harp2_fastmapol/pace_earthcare_c5.0_r10_h2.0_chi22.0_nvref30_nvdolp30_qf5/
                       summary/date_20240701-20250731/csv_nv30_minaod0.1_maxaod1/
                      /ATL_ALD_2A_alh

                      daily vs summary
                      add date range for different period
    """

    #### load the folders to read and save data ####

    matchup_daily_folder, summary_folder_csv, summary_folder_plot, summary_folder_html,\
                                share_folder_csv, share_folder_plot, share_folder_html = path_dict

    #### load csv info file ######
    current_path = os.getcwd()
    print("Current working directory:", current_path)
    current_module_path = Path(__file__).parent.absolute()
    print("Current module directory:", current_module_path)
    csv_path=os.path.join(current_module_path,'../data/val_var_list.csv')
    csv_lookup = set_csv_lookup(csv_path=csv_path)

    #### set four spectral bands for correlation plots
    if(product1=='harp2_fastmapol'):
        wvv4b=[440, 550, 670, 870]
    elif(product1=='spexone_fastmapol'):
        wvv4b=[437, 548, 668, 748]
    elif(product1=='spexone_remotap'):
        wvv4b=[440, 550, 670, 870]

    #used for plot and find aot550 for data filtering
    aot550_key = 'aot_wv'+str(int(wvv4b[1]))
    ssa550_key = 'ssa_wv'+str(int(wvv4b[1]))
    print('aot550_key, ssa550_key:', aot550_key, ssa550_key)

    ############################
    pair_dic={'AOD15':['aot_wv','angstrom_440_670'],\
              'SDA15':['aot_fine_wv', 'aot_coarse_wv'],\
              'ALM15':['ssa_wv', 'mr_wv', 'mi_wv', 'vd_fine', 'vd_coarse', 
                       'reff_fine', 'reff_coarse', 'veff_fine', 'veff_coarse', 'sph', 'sph_coarse'],\
              'HYB15':['ssa_wv', 'mr_wv', 'mi_wv', 'vd_fine', 'vd_coarse', 
                       'reff_fine', 'reff_coarse', 'veff_fine', 'veff_coarse', 'sph', 'sph_coarse'],\
              'MAN_AOD15_series':['aot_wv','angstrom_440_870'],\
              'MAN_SDA15_series':['aot_fine_wv','aot_coarse_wv'],\
              'LWN15':['aot_wv','Rrs2_mean_wv','wind_speed','chla'],\
              'SEABASS_ALL':['Rrs2_mean_wv'],\
              'SEABASS_OCI':['Rrs2_mean_wv'],\
              'HSRL2_R1':['aot550', 'wind_speed', 'alh'],\
              'ATL_ALD_2A':['alh'],\
             }

    #pair_dic={}
    
    #pair_dic={'HSRL2_R1':['aot550', 'wind_speed', 'alh']}

    pair_dic={'LWN15':['aot_wv','Rrs2_mean_wv','wind_speed','chla'],\
              'SEABASS_ALL':['Rrs2_mean_wv'],\
              'SEABASS_OCI':['Rrs2_mean_wv'],\
             }
    
    pair_dic={
              'SEABASS_OCI':['Rrs2_mean_wv'],\
             }
    
    #pair_dic={'ATL_ALD_2A':['alh']}
    
    #pair_dic={'ALM15':['sph', 'sph_coarse'],\
    #          'HYB15':['sph', 'sph_coarse']}

    
    #################################################################################################
    # Loop through every suite+var pair
    suite_count = 0
    for suite1, var_list in pair_dic.items():        
        suite_count += 1
        print(f"\n--- Processing Suite {suite_count}/{len(pair_dic)}: {suite1} ---")
        
        var_count = 0
        for var1 in var_list:
            #for every variable
            var_count += 1
            
            print(f"  Processing variable {var_count}/{len(var_list)}: {var1}")
        
            pair1 = set_var_criteria(suite1, var1, csv_lookup, wvv4b, chi2_max1, nv_min1, min_aod1, max_aod1)
            
            #wvv_corr_plot = wvv4b
            suite1, var1, wvv_corr_plot, chi2_max2, nv_min2, min_aod2, max_aod2 = pair1
            
            print("pair1", pair1)

            csv_file_dict={"pace_mean": f"{suite1}_{var1}_all_pace_mean_df.csv",
               "pace_std":  f"{suite1}_{var1}_all_pace_std_df.csv",
               "target_mean": f"{suite1}_{var1}_all_target_mean_df.csv",
               "target_std":  f"{suite1}_{var1}_all_target_std_df.csv"
              }
            
            ###work on pace data first and get the mask######################################
            file1 = csv_file_dict["pace_mean"]
            csv_files = get_filtered_csv_file(matchup_daily_folder, file1, tspan)
            
            if(csv_files is None):
                continue
            df1 = get_all_csv(csv_files)
            mask1 = get_mask(df1, chi2_max2, nv_min2, min_aod2, max_aod2, aot550_key=aot550_key)

            #try:
            print("----start csv creation----------------------------------------------------------")
            
            csv_file_share = {}
            
            for key1 in csv_file_dict.keys():
                # Find matching files
                filet = csv_file_dict[key1]

                ##
                csv_files = get_filtered_csv_file(matchup_daily_folder, filet, tspan)
                
                if not csv_files:  # Check if any files found
                    print(f"***No files found for pattern: {filet} in {matchup_daily_folder}/*/csv")
                    continue

                dft = get_all_csv(csv_files)
                num_dft1 = len(dft)
                print("    ====size of val/pace before subset filtering (nv, aod, chi2):", num_dft1)
                dft = dft[mask1]
                num_dft2 = len(dft)
                print("    ====size of val/pace after subset filtering (nv, aod, chi2):", num_dft2)
                num_str=f'count_b{num_dft1}_a{num_dft2}'
                
                # Calculate statistics
                numeric_cols = dft.select_dtypes(include=['number']).columns
                dft_mean = dft.groupby('site')[numeric_cols].mean().reset_index()
                #dft_std = df1.groupby('site')[numeric_cols].std().reset_index()
            
                # save csv to internal path
                # add another subfolder for both summary and share path
                summary_folder_csv_var = summary_folder_csv
                #summary_folder_csv_var = os.path.join(summary_folder_csv, f"{suite1}_{var1}")
                #os.makedirs(summary_folder_csv_var, exist_ok=True)
                share_folder_csv_var = share_folder_csv
                #share_folder_csv_var = os.path.join(share_folder_csv, f"{suite1}_{var1}")
                #os.makedirs(share_folder_csv_var, exist_ok=True)
                
                #print("    ====path to save csv avg in local:", summary_folder_csv_var)
                
                #add total number of entries in filename
                file_save_mean = filet.replace('.csv', f'_avg_{num_str}.csv')
                path_save_mean = os.path.join(summary_folder_csv_var, file_save_mean)
                dft_mean.to_csv(path_save_mean, index=False)
                
                #full list
                file_save_full = filet.replace('.csv', f'_full_{num_str}.csv')
                path_save_full = os.path.join(summary_folder_csv_var, file_save_full)
                dft.to_csv(path_save_full, index=False)
                
                #copy file to fileshsare folder
                #makesure the same file structure for both share and summary data
                shutil.copy(path_save_full, share_folder_csv_var)
                csv_file_share[key1] = os.path.join(share_folder_csv_var, file_save_full)
                
                
            print("-----format csv file ---------------------------------------------------------")
            
            
            ##reformat the data structure
            file1=csv_file_share['target_mean'] #validation target source
            file2=csv_file_share['pace_mean']   #pace product
            print(file1, file2)
            reformat_csv(file1, file2, aot550_key)
            
            file1=csv_file_share['target_std'] #validation target source
            file2=csv_file_share['pace_std']   #pace product
            reformat_csv(file1, file2, aot550_key)

            print("-----print data ---------------------------------------------------------")
            file1=csv_file_share['target_mean'] #validation target source
            file2=csv_file_share['pace_mean']   #pace product
            df1 = pd.read_csv(file1, index_col=0)
            df2 = pd.read_csv(file2, index_col=0)

            print(file1)
            print(file2)

            print("-----corr and hist plot ---------------------------------------------------------")
            #combine correlation at selected wavelength
            plot_combine_corr(df1, df2, wvv_corr_plot,\
                    summary_folder_plot,val_source, product1, suite1, var1,\
                              target_prefix='target_var_', pace_prefix='pace_var_')
            
            #plot histogram
            plot_combine_hist(df2, \
                    summary_folder_plot,val_source, product1, suite1, var1, \
                              pace_prefix='pace_')

            print("-----global diff plot ---------------------------------------------------------")
            #plot global map for all variable
            get_global_map(file1, file2, suite1, var1, wvv4b,\
                   summary_folder_plot, product1, 
                   target_prefix='target_var_', pace_prefix='pace_var_')

            #test except
            #except:
            #    print("*****************************************")
            #    print("********can not found", f"{suite1}_{var1}")
    
    ####################################
    #copy the plot to share folder too
    #use copytree to copy folder
    shutil.copytree(summary_folder_plot, share_folder_plot, dirs_exist_ok=True)
    
    #create html

    
    print("==arrange image order for html==")
    #folder_path = summary_folder_plot
    folder_path = share_folder_plot #for share folder
    image_files = get_image_files(folder_path)
    #ordered_files = final_ordered_image_list(image_files)
    prior = ["validation_matchup", "validation_diff"]
    ordered_files = ordered_image_list(image_files, priority_substrings=prior)
    
    # Now use ordered_files in your HTML generator!
    source_html=os.path.join(summary_folder_html, \
                             f"narwhal_pace_{val_source.lower()}_{product1}_{tspan[0]}-{tspan[1]}.html")

    title=f"{product1.upper()} Validation with {val_source.upper()}" 
    
    if all_rules:
        title2 = format_html_info_matchup(
            val_source=val_source,
            all_rules=all_rules,
            tspan=tspan,
            wvv1=wvv4b,
            nv_min1=nv_min1,
            min_aod1=min_aod1,
            max_aod1=max_aod1
        )
    else:
        title2 = None

    create_html_with_embedded_images_and_buttons(folder_path, ordered_files, output_html=source_html, 
                                        resolution_factor=2, quality=85,\
                                    title=title, title2=title2, logo_path=logo_path)
    
    #### copy to share folder
    shutil.copy(source_html, share_folder_html)
    print(f"Copied to:", share_folder_html)
 
def get_filtered_csv_file(matchup_daily_folder, filet, tspan):
    """get all csv and the napply tspan filtering"""
    filev = glob.glob(os.path.join(matchup_daily_folder, '*/csv', filet))
    filev = sorted(filter_files_by_date_range(filev, tspan))
    print("  ")
    print(f"*** Found {len(filev)} files for {filet}")

    if not filev:  # Check if any files found
        print(f"*** No files found for pattern: {filet} in {matchup_daily_folder}/*/csv")
        filev=None
        
    return filev
                        
def set_csv_lookup(csv_path='./val_var_list.csv'):
    """
    read from csv, determine wv dependency
    """
    df_var = pd.read_csv(csv_path, skipinitialspace=True)
    
    # Create a lookup dictionary from CSV for quick access
    csv_lookup = {}
    for index, row in df_var.iterrows():
        key = (row['suite1'], row['new_start1'])
        csv_lookup[key] = row['wvv_option']
    return csv_lookup

def set_var_criteria(suite1, var1, csv_lookup, wvv1, chi2_max1, nv_min1, min_aod1, max_aod1):
    """
    construct the option for combine variables
    also set min and max aod for each variables
    """

    key = (suite1, var1)
    if key in csv_lookup:
        wvv_option = csv_lookup[key]
        #include all bands
        if wvv_option == 'wvv':
            wvv = wvv1  # or assign actual wvv1 variable
        else:
            wvv = []
    else:
        print(f"Warning: {suite1}+{var1} not found in CSV file")
        wvv = []  # default
    
    #aot and rrs, use min_aod = 0, all others set a minimum value    
    if var1 in ['aot550', 'aot_wv', 'aot_fine_wv', 'aot_coarse_wv', \
                'chla', 'wind_speed', 'Rrs2_mean_wv', 'Rrs1_mean_wv']:
        min_aod2 = 0
    else:
        min_aod2 = min_aod1

    # Create the pair (equivalent to original pair1 unpacking)
    pair1 = [suite1, var1, wvv, chi2_max1, nv_min1, min_aod2, max_aod1]
    
    print(f"Processing: suite={suite1}, variable={var1}, wvv={wvv}, "
          f"chi2_max={chi2_max1}, nv_min={nv_min1}, min_aod={min_aod2}, max_aod={max_aod1}")
        
    return pair1

def get_mask(df2, chi2_max, nv_min, min_aod, max_aod, aot550_key='aot_wv550'):
    """
    df1: validation data/target data
    df2: retrieval data/pace data
    
    apply data mask on nv_min and aot550
    """
    
    #nv_ref and nv_dolp may not exist in remotap data, set a default value in preprocessing
    mask1 = (df2.chi2<=chi2_max) & (df2.nv_ref>=nv_min) & (df2.nv_dolp>=nv_min)

    aot550 = df2[aot550_key]
    mask2 = (aot550 <= max_aod) & (aot550 >= min_aod)
        
    mask = mask1 & mask2    
    
    return mask

def get_all_csv(csv_files):
    """
    read all csv files which are not empty
    """
    df1v=[]
    for file in csv_files:
        try:
            df1=pd.read_csv(file) 
            df1v.append(df1)
            #print(len(df1))
        except:
            pass
    
    df1=pd.concat(df1v, ignore_index=True)
    return df1

def plot_combine_hist(df2, \
                     summary_folder_plot,val_source, product1, suite1, var1,\
                     pace_prefix='pace_var_'):
    """
    get histogram of the retrieval results 
    """
    fileout0 = os.path.join(summary_folder_plot, f"{suite1}_{var1}_hist.png")

    plt.figure(figsize=(6,4))
    try:
        key1v=['chi2', 'nv_ref', 'nv_dolp', 'quality_flag']
        key1v = [pace_prefix+key1 for key1 in key1v]
        df2[key1v].hist(bins=50)
    except:
        key1v=['chi2', 'quality_flag']
        key1v = [pace_prefix+key1 for key1 in key1v]
        df2[key1v].hist(bins=50)
        
    plt.savefig(fileout0, dpi=300, bbox_inches='tight')


def plot_combine_corr(df1, df2,  wvv_corr_plot, \
                         summary_folder_plot,val_source, product1, suite1, var1,\
                         target_prefix='target_var_', pace_prefix='pace_var_'):
    """

    df1: target at val_source (aeronet, aeronet oc etc
    df2: pace product: product1
    
    file1='AOD15_aot_wv_all_pace_mean_df.csv'
    use the wavelength as input in wvv_corr_plot, and determine the var for plot, e.g.
        screened_vars = ['aot_wv440', 'aot_wv550', 'aot_wv670', 'aot_wv870']

        
    """

    if(len(wvv_corr_plot)>0):
        target_screened_vars = [target_prefix+str(var1)+str(wv) for wv in wvv_corr_plot]
        pace_screened_vars = [pace_prefix+str(var1)+str(wv) for wv in wvv_corr_plot]
        
        title1v=[f"{suite1}_{var1}{wv}" for wv in wvv_corr_plot]
        fileout1v=[os.path.join(summary_folder_plot, f"{suite1}_{var1}{wv}_corr.png") for wv in wvv_corr_plot]
    else:
        target_screened_vars = [target_prefix+var1]
        pace_screened_vars = [pace_prefix+var1]
        
        title1v=[f"{suite1}_{var1}"]
        fileout1v=[os.path.join(summary_folder_plot, f"{suite1}_{var1}_corr.png")]
        
    print(pace_screened_vars)
    print(target_screened_vars)
    xlabel=val_source.upper()  # x: target
    ylabel=product1.upper() #y: pace
                                                                  
    plot_corr(df1, df2, target_screened_vars, pace_screened_vars, \
              xlabel=xlabel, ylabel=ylabel, title1v=title1v, fileout1v=fileout1v)
    
def plot_corr(all_target_mean_df, all_pace_mean_df, target_screened_vars, pace_screened_vars, \
              xlabel="Target", ylabel="PACE", title1v = None, fileout1v=None):
    
    """
    for aod, consider use log10 scale in scatter plot
    there are also large outliers
    
    """

    #print("         >plot correlation on screened_vars:", screened_vars)
    
    for var1, var2, title1, fileout1 in zip(target_screened_vars, pace_screened_vars, title1v, fileout1v):
        #print("           *plot corr:", var1, title1, fileout1)
        print("           *plot corr:", var1, var2)
        
        x = all_target_mean_df[var1].values
        y = all_pace_mean_df[var2].values
        
        #print("number of pixels for x and y:", x.shape, y.shape)

        #if('aot' in var1):
        #    x1=np.log10(x).copy()
        #    y1=np.log10(x).copy()
                    
        x1 = x.copy()
        y1 = y.copy()
        
        plot_corr_one_density_kde(
            x, y, label=var1, title=title1, fileout=fileout1,
            xlabel=xlabel, ylabel=ylabel)



def filter_files_by_date_range(file_list, tspan):
    """
    Filter files by date range from the glob results
    """
    start_date = datetime.strptime(tspan[0], "%Y-%m-%d")
    end_date = datetime.strptime(tspan[1], "%Y-%m-%d")
    
    filtered_files = []
    
    for file_path in file_list:
        # Extract date from the directory structure
        # Assuming path structure: .../2024-03-02-2024-03-02/csv/...
        try:
            # Get the parent directory of 'csv'
            csv_parent = os.path.dirname(os.path.dirname(file_path))
            date_dir = os.path.basename(csv_parent)
            
            # Extract first date from patterns like "2024-03-02-2024-03-02"
            if '-' in date_dir:
                date_parts = date_dir.split('-')
                if len(date_parts) >= 3:
                    file_date_str = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                    
                    # Check if within range
                    if start_date <= file_date <= end_date:
                        filtered_files.append(file_path)
        
        except (ValueError, IndexError):
            continue
    
    return filtered_files
