"""
Need import EAS MAAP package, and the pace_earthcare_matchups created by Sean Foley
Need reset system path to get correct path for data download and token

new packages:
    mamba install pystac-client -c conda-forge
    or poseidon seems not responsive when using mamba to install new package
    pip install pystac-client
    
    git clone https://github.com/MAAP-Project/maap-py
    pip install .
    
    git clone https://github.com/seanremy/pace-earthcare-matchups.git
    pip install .

    #mamba install geospatial #may not always need, requires a lot new stuff
    #create a new environment py3.12_earthcare, which need install a lot new package for the following package
    #mamba install jupytext -c conda-forge
    #mamba install pystac -c conda-forge

"""

import os
import sys
from maap.maap import MAAP
from pystac_client import Client
from datetime import datetime, timedelta

from tools.detection_download import format_tspan
from tools.narwhal_pace import get_pace_data_info

def run_earthcare_matchup(product, input_folder, tspan, bbox=(-180, 0, 180, 80), limit=50000, 
                         shortnames_earthcare1="ATL_ALD_2A",
                         token_path=None, verbose=True):
    """
    Run EarthCARE matchup analysis with PACE data
    
    Parameters:
    -----------
    product : str
        Product name to get PACE data info
    input_folder : str
        Where data is saved for both pace and earthcare
    tspan : tuple
        (tspan_start, tspan_end) in format (YYYY-MM-DD, YYYY-MM-DD)
    bbox : tuple
        Bounding box in format (W, S, E, N)
    limit : int
        Maximum number of records to retrieve
    shortnames_earthcare1 : str
        EarthCARE product shortname (default: "ATL_ALD_2A")
    PATH_TOKEN : str
        Path to credentials file
    verbose : bool
        Enable verbose output
    
    Returns:
    --------
    matchups : object
        Matchup results, or None if failed
    earthcare_save_folder: save folder
    """
    
    # Create folder structure - fix string formatting
    tspan_start, tspan_end = tspan
    earthcare_save_folder = os.path.join(input_folder, 'earthcare', f'{tspan_start}-{tspan_end}')
    print("***** earthcare data save here:", earthcare_save_folder)
    
    os.makedirs(earthcare_save_folder, exist_ok=True)
    os.environ['PACE_EARTHCARE_DATA_PATH'] = earthcare_save_folder
    os.environ['PATH_TOKEN'] = token_path

    #if not given already read from the package
    if(not token_path):
        try:
            from pace_earthcare_matchups.path_utils import PATH_TOKEN
            token_path = PATH_TOKEN
        except ImportError:
            print("cannot find the token")
            
    print("Token path:", token_path)

    if verbose:
        print(f"Created folder: {earthcare_save_folder}")
        print(f"Set PACE_EARTHCARE_DATA_PATH: {os.environ['PACE_EARTHCARE_DATA_PATH']}")

    # Add HMS (hours, minutes, seconds) to time span
    tspan_web = format_tspan(tspan)
    time_start, time_end = parse_time(tspan_web, verbose=verbose) 

    # Load the path after reset system path
    try:
        from pace_earthcare_matchups.path_utils import PATH_DATA, get_path
        print("Verify new path:", PATH_DATA)
        from pace_earthcare_matchups.matchup import get_matchups
        from pace_earthcare_matchups.plotting import plot_matchups
        
    except ImportError as e:
        print(f"Error importing pace_earthcare_matchups modules: {e}")
        print("Make sure pace_earthcare_matchups is properly installed and accessible")
        return None

    # Initialize MAAP and ESA client
    try:
        CMR_HOST = "cmr.earthdata.nasa.gov"
        
        # Read token file safely
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                _ESA_MAAP_TOKEN = f.read().strip()
        else:
            print(f"Token file not found at {token_path}")
            return None
            
        ESA_CATALOGUE = "https://catalog.maap.eo.esa.int/catalogue/"
        
        maap = MAAP()
        client_esa = Client.open(ESA_CATALOGUE)
        
        if verbose:
            print("Successfully initialized MAAP and ESA client")
            
    except Exception as e:
        print(f"Error initializing MAAP/ESA client: {e}")
        return None

    # Get PACE product information
    try:
        outputfile_header, product_info_nrt, product_info_refined = get_pace_data_info(product)
        if verbose:
            print(f"Retrieved product info for: {product}")
            print(f"Refined: {product_info_refined.get('short_name', 'N/A') if product_info_refined else 'None'}")
            print(f"NRT: {product_info_nrt.get('short_name', 'N/A') if product_info_nrt else 'None'}")
    except Exception as e:
        print(f"Error getting PACE data info for product '{product}': {e}")
        return None

    # Try to get matchups - first with refined, then with NRT
    matchups = None
    
    # Try refined product first
    if product_info_refined and product_info_refined.get("short_name"):
        try:
            shortname_pace1 = product_info_refined["short_name"]
            if verbose:
                print(f"Attempting matchups with refined product: {shortname_pace1}")
                
            matchups = get_matchups(
                maap=maap,
                client_esa=client_esa,
                long_term_token=_ESA_MAAP_TOKEN,
                shortname_pace=shortname_pace1,
                shortnames_earthcare=[shortnames_earthcare1],
                temporal=(time_start, time_end),  # Use parsed datetime objects
                bbox=bbox,
                limit=limit,
            )
            
            if verbose:
                print("Successfully retrieved matchups with refined product")
                
        except Exception as e:
            if verbose:
                print(f"Failed with refined product: {e}")
            matchups = None

    # If refined failed or wasn't available, try NRT
    if matchups is None and product_info_nrt and product_info_nrt.get("short_name"):
        try:
            shortname_pace1 = product_info_nrt["short_name"]
            if verbose:
                print(f"Attempting matchups with NRT product: {shortname_pace1}")
                
            matchups = get_matchups(
                maap=maap,
                client_esa=client_esa,
                long_term_token=_ESA_MAAP_TOKEN,
                shortname_pace=shortname_pace1,
                shortnames_earthcare=[shortnames_earthcare1],
                temporal=(time_start, time_end),  # Use parsed datetime objects
                bbox=bbox,
                limit=limit,
            )
            
            if verbose:
                print("Successfully retrieved matchups with NRT product")
                
        except Exception as e:
            if verbose:
                print(f"Failed with NRT product: {e}")
            matchups = None

    # Final check
    if matchups is not None:
        if verbose:
            print("Matchup operation completed successfully")
            print(f"Matchups type: {type(matchups)}")
        return matchups, earthcare_save_folder
    else:
        print("Failed to retrieve matchups with both refined and NRT products")
        return None, earthcare_save_folder

def parse_time(tspan_web, verbose=False):
    """
    Parse time span to datetime objects
    
    Parameters:
    -----------
    tspan_web : tuple
        ('YYYY-MM-DD HH:MM:SS', 'YYYY-MM-DD HH:MM:SS')
    verbose : bool
        Enable verbose output
    
    Returns:
    --------
    tuple : (time_start, time_end) or (None, None) if parsing fails
    """
    
    if not tspan_web or len(tspan_web) != 2:
        if verbose: print("Invalid tspan_web format")
        return None, None
    
    try:
        start_str, end_str = tspan_web
        time_start = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
        
        # Set end time to end of day if it's 00:00:00
        if end_str.endswith('00:00:00'):
            date_part = end_str.split(' ')[0]
            time_end = datetime.strptime(f"{date_part} 23:59:59", '%Y-%m-%d %H:%M:%S')
        else:
            time_end = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')
        
        if verbose:
            print(f"Parsed time span: {time_start} to {time_end}")
        
        return time_start, time_end
        
    except Exception as e:
        if verbose: print(f"Error parsing time span: {e}")
        return None, None