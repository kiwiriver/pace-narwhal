import os
import re
import numpy as np
import multiprocessing

def clean_value(value):
    """Convert value to string if it's a valid string/number, otherwise return empty string"""
    if (value is None or 
        (isinstance(value, float) and (np.isnan(value) or not np.isfinite(value))) or 
        not isinstance(value, (str, int, float))):
        return ""
    return str(value)
            
def is_none_value(value):
    """Check if value represents None/empty"""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == "" or value.lower() in ['none', 'null', 'undefined']
    return False

def extract_wavelength(var):
    match = re.search(r'(\d{3,4})', var)
    return int(match.group(1)) if match else None
        
def find_closest_wavelength_vars(var_list, targets):
    """
    Given a list of variable names with embedded wavelengths and a list of target wavelengths,
    return a list of variables that are closest to each target wavelength.
    """
    # Helper function to extract the wavelength from var name
    
    # Build a list of (var_name, wavelength) tuples
    wv_pairs = [(var, extract_wavelength(var)) for var in var_list if extract_wavelength(var) is not None]

    result = []
    for goal in targets:
        # Find the variable with the closest wavelength
        closest_var, _ = min(wv_pairs, key=lambda x: abs(x[1] - goal))
        result.append(closest_var)
    return result

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


#def get_rules_str(rules):
#    """convert to string as file name
#
#    include the full rules
#    
#    """
#    
#    rule_str = (f'c{rules["search_center_radius"]:.1f}_'
#                f'r{int(rules["search_grid_delta"])}_'
#                f'h{rules["delta_hour"]:.1f}_'
#                f'chi2{rules["chi2"][1]:.1f}_'
#                f'nvref{int(rules["nv_ref"][0])}_'
#                f'nvdolp{int(rules["nv_dolp"][0])}')
    
#    return rule_str

def get_filter_rules(all_rules, keys_to_keep = ["chi2", "nv_ref", "nv_dolp", "quality_flag"]):
    """
    select the rules to filter data directly
    
    """
    # includes a missing key
    print("***keys_to_keep in data filtering***", keys_to_keep)
    
    filter_rules = {key: all_rules[key] for key in keys_to_keep if key in all_rules}

    return filter_rules
        
def get_rules_str(rules):
    """Convert rules to string as file name
    
    Handles single numbers and ranges according to the specified order:
    - Single numbers: search_center_radius, search_grid_delta, delta_hour (and other single values)
    - Two-number ranges: chi2, nv_ref, nv_dolp, quality_flag (uses appropriate index)
    
    Args:
        rules (dict): Dictionary containing rule parameters
        
    Returns:
        str: Formatted rule string for filename

    # Test with your example
        all_rules = {
            "search_center_radius": 5, 
            "search_grid_delta": 5, 
            "delta_hour": 2, 
            "chi2": [0, 2], 
            "nv_ref": [120, 170], 
            "nv_dolp": [120, 170], 
            "quality_flag": [0, 5]
        }
        
        print(get_rules_str(all_rules))
        # Output: c5.0_r5_h2.0_chi22.0_nvref120_nvdolp120_qf5

    """
    
    # Define the order and format for each parameter
    single_params = ['search_center_radius', 'search_grid_delta', 'delta_hour']
    range_params = ['chi2', 'nv_ref', 'nv_dolp', 'quality_flag']
    
    # Define which index to use for range parameters and their prefixes
    range_config = {
        'chi2': {'index': 1, 'prefix': 'chi2', 'format': 'float'},
        'nv_ref': {'index': 0, 'prefix': 'nvref', 'format': 'int'},
        'nv_dolp': {'index': 0, 'prefix': 'nvdolp', 'format': 'int'},
        'quality_flag': {'index': 1, 'prefix': 'qf', 'format': 'int'}
    }
    
    rule_parts = []
    
    # Process single-value parameters in order
    for param in single_params:
        if param in rules:
            value = rules[param]
            if param == 'search_center_radius':
                rule_parts.append(f'c{value:.1f}')
            elif param == 'search_grid_delta':
                rule_parts.append(f'r{int(value)}')
            elif param == 'delta_hour':
                rule_parts.append(f'h{value:.1f}')
    
    # Process range parameters in order
    for param in range_params:
        if param in rules:
            value = rules[param]
            config = range_config[param]
            
            # Check if it's a single number or a list/tuple
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                selected_value = value[config['index']]
            else:
                selected_value = value  # Single number case
            
            # Format based on type
            if config['format'] == 'int':
                rule_parts.append(f'{config["prefix"]}{int(selected_value)}')
            else:  # float
                rule_parts.append(f'{config["prefix"]}{selected_value:.1f}')
    
    # Handle any other single-value parameters not in the predefined lists
    processed_params = set(single_params + range_params)
    for param, value in rules.items():
        if param not in processed_params:
            if isinstance(value, (list, tuple)):
                # If it's a list/tuple, use first element by default
                rule_parts.append(f'{param}{value[0]}')
            else:
                # Single value
                rule_parts.append(f'{param}{value}')
    
    return '_'.join(rule_parts)