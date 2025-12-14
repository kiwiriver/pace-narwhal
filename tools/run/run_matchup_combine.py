import os
import sys
import argparse  # ADD THIS IMPORT
import json      # ADD THIS IMPORT
import matplotlib.pyplot as plt
from datetime import datetime

# Add the path of the tools
#mapol_path = os.path.expanduser('~/github/mapoltool')
#mapol_path = os.path.expanduser('/mnt/mfs/mgao1/analysis/github/mapoltool')
mapol_path = os.path.expanduser('/mnt/mfs/mgao1/analysis/github/pace-narwhal')
sys.path.append(mapol_path)

from tools.aeronet_matchup_plot import plot_four_csv_maps
from tools.aeronet_matchup_order import get_image_files,ordered_image_list
from tools.aeronet_matchup_plot import plot_four_csv_maps
from tools.narwhal_matchup_combine import aeronet_combine_summary
from tools.narwhal_tools import print_threads_info, get_rules_str

def main():
    print_threads_info()
    
    parser = argparse.ArgumentParser(description="Run PACE L2 daily processing script.")
    parser.add_argument("--share_dir_base", type=str, default="/mnt/mfs/FILESHARE/meng_gao/pace/validation/summary/", 
               help="Path to save in fileshare")
    parser.add_argument("--local_dir_base", type=str, default="/accounts/mgao1/mfs_pace/pace/validation/val5/test0/", 
               help="Path to read the matchup files")
    
    parser.add_argument("--product", type=str, help="product: harp2_fastmapol, ...")
    parser.add_argument("--tspan_start", type=str, default="2024-03-01", help="Start date of the time span (YYYY-MM-DD).")
    parser.add_argument("--tspan_end", type=str, default="2025-10-31", help="End date of the time span (YYYY-MM-DD).")

    parser.add_argument('--all_rules', type=str, \
     default='{"search_center_radius": 5, "search_grid_delta":5, "delta_hour":2, "chi2":[0,2], "nv_ref":[120,170], "nv_dolp":[120,170]: "quality_flag":[0,5]}',\
                        help='Filter rule as JSON string')
    parser.add_argument('--subset_rules', type=str, \
     default='{"nv_min":60, "min_aod":0.2, "max_aod":1, "max_chi2":2}', help='Filter rule as JSON string for subset')
    parser.add_argument('--val_source', type=str, default='AERONET')
    
    args = parser.parse_args()
    val_source = args.val_source
    product1 = args.product
    share_dir_base = args.share_dir_base
    local_dir_base = args.local_dir_base  # FIX: Use from args
    tspan_start = args.tspan_start 
    tspan_end = args.tspan_end
    tspan = (tspan_start, tspan_end)
    
    # Convert date range
    start_date = datetime.strptime(tspan[0], "%Y-%m-%d").strftime("%Y%m%d")
    end_date = datetime.strptime(tspan[1], "%Y-%m-%d").strftime("%Y%m%d")
    date_range = f'{start_date}-{end_date}'
    print(date_range)
    
    # FIX: Parse JSON strings
    all_rules = json.loads(args.all_rules)
    subset_rules = json.loads(args.subset_rules)
    
    # FIX: Correct variable names
    nv_min = subset_rules['nv_min']      # Was: subset_rues
    min_aod = subset_rules['min_aod']    # Was: subset_rues
    max_aod = subset_rules['max_aod']    # Was: subset_rues
    chi2_max = subset_rules['chi2_max']
    
    all_rules_str = get_rules_str(all_rules)
    print("rules:",all_rules_str)

    #must follow current validation data structure
    local_dir = os.path.join(local_dir_base, product1, f'pace_{val_source.lower()}_{all_rules_str}')
    print('data location:', local_dir)
    
    html_str = f"{all_rules_str}_subset_chi2max{chi2_max}_nvmin{nv_min}_aodmin{min_aod}_aodmax{max_aod}"
    print("html str", html_str)
    
    # HTML output path
    share_dir = os.path.join(share_dir_base, product1, 'html')
    os.makedirs(share_dir, exist_ok=True)
    share_file = f"val_{val_source.lower()}_{date_range}_{html_str}.html"
    share_html = os.path.join(share_dir, share_file)
    
    # CSV output path
    share_dir = os.path.join(share_dir_base, product1, 'csv')
    os.makedirs(share_dir, exist_ok=True)
    share_file = f"val_{val_source.lower()}_{date_range}_{html_str}.csv"
    share_csv = os.path.join(share_dir, share_file)

    #########################################################################################
    logo_path = os.path.join(mapol_path, "logo", 'narwhal_logo_v1.png')
    print("====logo location:", logo_path)
    if os.path.isfile(logo_path):
        print("====find the logo")
    else:
        print("====missing logo")
        logo_path=None
              
    aeronet_combine_summary(product1, local_dir, tspan,\
                            chi2_max, nv_min, min_aod, max_aod, \
                            share_html, share_csv, all_rules, val_source=val_source, logo_path=logo_path)
    
if __name__ == '__main__':
    main()
