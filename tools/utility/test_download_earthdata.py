import os
import time
import argparse
import requests
import subprocess
import earthaccess
import multiprocessing
from pathlib import Path
from requests.exceptions import RequestException

def download_with_retry(granules, local_path, max_retries=3, threads=8):
    """
    Add retry
    """
    for attempt in range(max_retries):
        try:
            files = earthaccess.download(granules, local_path, threads=threads)
            return files
        except (RequestException, Exception) as e:
            print(f"Download attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in 30 seconds...")
                time.sleep(30)
            else:
                print("All retry attempts failed")
                raise e

def download_l2_cloud(tspan, short_name="PACE_HARP2_L2_MAPOL_OCEAN_NRT",\
                      output_folder="./downloads", threads=8):
    """download ata using earthaccess"""
    
    results = earthaccess.search_data(
        short_name=short_name,
        temporal=tspan,
        )
    
    filelist_l2 = download_with_retry(results, output_folder, threads=threads)
    
    return filelist_l2

def log_key_value(key, value, indent=2, width=24):
    space = " " * indent
    print(f"{space}- {key:<{width}}: {value}")

def print_threads_info():
    """
    check threads info
    """
    print("check system information:")
    log_key_value("CPU Cores", multiprocessing.cpu_count())

    cores = int(os.environ.get('SLURM_CPUS_PER_TASK', 8))
    # Set threading for various libraries
    os.environ['OMP_NUM_THREADS'] = str(cores)
    os.environ['MKL_NUM_THREADS'] = str(cores)
    os.environ['OPENBLAS_NUM_THREADS'] = str(cores)

    log_key_value("MKL_NUM_THREADS", os.environ.get("MKL_NUM_THREADS", "Not set"))
    log_key_value("OPENBLAS_NUM_THREADS", os.environ.get("OPENBLAS_NUM_THREADS", "Not set"))
    log_key_value("OMP_NUM_THREADS", os.environ.get("OMP_NUM_THREADS", "Not set"))

def main():
    """
    test earthdata download in parallel
        
    """
    
    parser = argparse.ArgumentParser(description="Run PACE L2 daily processing script.")
    parser.add_argument("--save_path", type=str, default=".", \
                        help="Path to the input folder containing data files (default: current directory).")
    parser.add_argument("--product", type=str, help="product: harp2_fastmapol, ...")
    parser.add_argument("--tspan_start", type=str, help="Start date of the time span (YYYY-MM-DD).")
    parser.add_argument("--tspan_end", type=str, help="End date of the time span (YYYY-MM-DD).")
    parser.add_argument("--threads", type=int, default=8, help="number of threads used, default 8")
    
    args = parser.parse_args()
    save_path = args.save_path
    threads = args.threads
    product = args.product
    tspan_start = args.tspan_start 
    tspan_end = args.tspan_end
    tspan = (tspan_start, tspan_end)
    day1 = tspan[0]+'_'+tspan[1]

    #print_threads_info()
    
    if(product=='harp2_fastmapol'):
        outputfile_header='harp2_fastmapol_'
        product_info_nrt={"short_name": "PACE_HARP2_L2_MAPOL_OCEAN_NRT", "sensor_id": 48, "dtid":1546, \
                             "sensor":"PACE_HARP2","suite1":"L1C.V3.5km", "suite2":"L2.MAPOL_OCEAN.V3.0.NRT"}
        product_info_refined={"short_name": "PACE_HARP2_L2_MAPOL_OCEAN", "sensor_id": 48, "dtid":1547, \
                              "sensor":"PACE_HARP2", "suite1":"L1C.V3.5km", "suite2":"L2.MAPOL_OCEAN.V3.0"}
    elif(product=='spexone_fastmapol'):
        outputfile_header='spexone_fastmapol_'
        product_info_nrt={"short_name": "PACE_SPEXONE_L2_MAPOL_OCEAN_NRT", "sensor_id": 41, "dtid":1970, \
                             "sensor":"PACE_SPEXONE","suite1":"L1C.V3.5km", "suite2":"L2.MAPOL_OCEAN.V3.0.NRT"}
        product_info_refined={"short_name": "PACE_SPEXONE_L2_MAPOL_OCEAN", "sensor_id": 41, "dtid":1971, \
                              "sensor":"PACE_SPEXONE", "suite1":"L1C.V3.5km", "suite2":"L2.MAPOL_OCEAN.V3.0"}
    
    elif(product=='spexone_remotap'):
        outputfile_header='spexone_remotap_'
        product_info_nrt={"short_name": "PACE_SPEXONE_L2_AER_RTAPOCEAN_NRT", "sensor_id": 41, "dtid":1350, \
                             "sensor":"PACE_SPEXONE","suite1":"L1C.V3.5km", "suite2":"L2.RTAP_OC.V3.0.NRT"}
        product_info_refined={"short_name": "PACE_SPEXONE_L2_AER_RTAPOCEAN", "sensor_id": 41, "dtid":1420, \
                              "sensor":"PACE_SPEXONE", "suite1":"L1C.V3.5km", "suite2":"RTAP_OC.V3.0"}
        

    try:
        short_name=product_info_refined["short_name"]
        sensor_id=product_info_refined["sensor_id"]
        dtid=product_info_refined["dtid"]
        sensor =product_info_refined["sensor"]
        suite1 =product_info_refined["suite1"]
        suite2 = product_info_refined["suite2"]
        #filelist_name=sensor+'_'+suite2+'_'+day1+'_filelist.txt'
    except:
        short_name=product_info_nrt["short_name"]
        sensor_id=product_info_nrt["sensor_id"]
        dtid=product_info_nrt["dtid"]
        sensor =product_info_nrt["sensor"]
        suite1 =product_info_nrt["suite1"]
        suite2 = product_info_nrt["suite2"]
        #filelist_name=sensor+'_'+suite2+'_'+day1+'_filelist.txt'

    
    l2_path = os.path.join(save_path,'data_l2',sensor+'_'+suite2+'_'+day1)
    os.makedirs(l2_path, exist_ok=True)
    print("location to save file:", l2_path)

    t1=time.time()
    filelist_l2 = download_l2_cloud(tspan, short_name=short_name, output_folder=l2_path, threads=threads)
    t2=time.time()
    print(f"number of threads: {threads}, total time lapses:", t2-t1)
    
if __name__ == '__main__':
    main()
    