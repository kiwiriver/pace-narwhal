"""
get the filename for csv download
"""

import os
import re
import glob
from collections import defaultdict
from tools.narwhal_matchup_html_tool import *

def get_suite_description(suite_name):
    """Get a human-readable description for a suite."""
    # Predefined descriptions
    descriptions = {
        'AOD15': 'Direct Solar',
        'SDA15': 'Spectral Deconvolution',
        'ALM15': 'Almucantar Mode',
        'HYB15': 'Hybrid Mode',
        'LWN15': 'Ocean Color',
        'SEABASS_ALL': 'SEABASS Ocean Color',
        'SEABASS_OCI': 'SEABASS matchups on OCI bands',
        'MAN_AOD15_series': 'MAN AOD',
        'MAN_SDA15_series': 'MAN SDA',
        'HSRL2_R1': 'HSRL2 (R1)',
        'HSRL2_R0': 'HSRL2 (R0)',
        'HSRL2_RA': 'HSRL2 (RA)',
        'ATL_ALD_2A': 'Atmospheric Lidar (ATLID) aerosol layer descriptors Level 2A (L2A) product'
    }
    
    # Return predefined description if available
    if suite_name in descriptions:
        return descriptions[suite_name]
    
    # Auto-generate description for unknown suites
    if suite_name.startswith('HSRL2_'):
        return f"HSRL2 ({suite_name.split('_', 1)[1]})"
    elif suite_name.startswith('MAN_'):
        return f"MAN {suite_name.split('_', 1)[1].replace('_', ' ').title()}"
    else:
        return suite_name.replace('_', ' ').title()

def get_suite_css_class(suite_name):
    """Get CSS class for styling suite containers."""
    base_class = "suite-container"
    
    if suite_name.startswith('MAN'):
        return base_class + " man-suite"
    elif suite_name.startswith('LWN'):
        return base_class + " lwn-suite"
    elif suite_name.startswith('AOD'):
        return base_class + " aod-suite"
    elif suite_name.startswith('SDA'):
        return base_class + " sda-suite"
    elif suite_name.startswith('ALM'):
        return base_class + " alm-suite"
    elif suite_name.startswith('HYB'):
        return base_class + " hyb-suite"
    elif suite_name.startswith('HSRL2'):
        return base_class + " hsrl2-suite"
    elif suite_name.startswith('ATLID'):
        return base_class + " atlid-suite"
    elif suite_name.startswith('SEABASS'):
        return base_class + " seabass-suite"
    else:
        return base_class

def get_variable_display_names():
    """Return mapping of variable codes to display names"""
    return {
        # Aerosol variables
        'aot': 'Aerosol Optical Thickness',
        'aot_fine': 'Fine Mode AOT',
        'aot_coarse': 'Coarse Mode AOT', 
        'angstrom': 'Angstrom Exponent',
        'angstrom_440_670': 'Angstrom Exponent (440-670nm)',
        'ssa': 'Single Scattering Albedo',
        'mi': 'Refractive Index (Imaginary)',
        'mr': 'Refractive Index (Real)',
        'reff_fine': 'Effective Radius (Fine)',
        'reff_coarse': 'Effective Radius (Coarse)',
        'veff_fine': 'Effective Variance (Fine)',
        'veff_coarse': 'Effective Variance (Coarse)',
        'vd_fine': 'Volume Density (Fine)',
        'vd_coarse': 'Volume Density (Coarse)',
        'sph': 'Sphericity Parameter',
        'alh': 'Aerosol Layer Height',
        
        # HSRL2-specific variables
        'extinction': 'Extinction Coefficient',
        'backscatter': 'Backscatter Coefficient',
        'lidar_ratio': 'Lidar Ratio',
        'depolarization': 'Depolarization Ratio',
        'profile': 'Vertical Profile',
        'aot550': 'AOD at 550nm',
        'aod532': 'AOD at 532nm',
        'ext532': 'Extinction at 532nm',
        'bsc532': 'Backscatter at 532nm',
        'lr532': 'Lidar Ratio at 532nm',
        'depo532': 'Depolarization at 532nm',
        
        # Ocean/Water variables - Updated for new format
        'chla': 'Chlorophyll-a Concentration',
        'rrs': 'Remote Sensing Reflectance (Mean)',
        'Rrs2_mean': 'Remote Sensing Reflectance (Mean)',
        'rrs2_mean': 'Remote Sensing Reflectance (Mean)',
        'wind_speed': 'Wind Speed',
        
        # Additional variables
        'sst': 'Sea Surface Temperature',
        'kd490': 'Diffuse Attenuation Coefficient',
        'pic': 'Particulate Inorganic Carbon',
        'poc': 'Particulate Organic Carbon',
        'cdm': 'Colored Dissolved Matter',
        'bbp': 'Backscattering Coefficient',
        
        # MAN-specific variables
        'series': 'Time Series',
        'statistics': 'Statistical Analysis'
    }
    
def generate_csv_urls(folder_path, suite, variable):
    """
    Generate CSV download URLs by converting local path to web URL.
    First finds the actual CSV files using glob on the local path,
    then converts the paths to web URLs.
    """
    # Determine the CSV folder path (replace 'plot' with 'csv')
    csv_folder_path = folder_path.replace('/plot', '/csv').rstrip('/')
    
    # Base filename pattern - more flexible to handle cases with or without 'wv'
    #base_filename_pattern = f"{suite}_{variable}/{suite}_{variable}*_all"
    #aot_wv or aot can be confusing use * instead
    base_filename_pattern = f"{suite}_{variable}*/{suite}_{variable}*_all"
    
    urls = {}
    # File types to look for
    suffixes = [
        'target_mean',
        'target_std', 
        'pace_mean',
        'pace_std'
    ]
    
    # Search for matching files
    for suffix in suffixes:
        # Create glob pattern
        glob_pattern = os.path.join(csv_folder_path, f"{base_filename_pattern}_{suffix}*.csv")
        print(glob_pattern)
        matching_files = glob.glob(glob_pattern)
        #print(matching_files)
        
        if matching_files:
            # Get the first matching file
            local_file_path = matching_files[0]

            # Convert to web URL
            web_csv_file = local_file_path.replace('/mnt/mfs/FILESHARE', 'https://oceancolor.gsfc.nasa.gov/fileshare')
            urls[suffix] = web_csv_file
        else:
            print("file not available")
            urls[suffix] = None
    return urls

def generate_plot_content(var_id, data, files, plot_type, folder_path, resolution_factor, quality, display_style=''):
    """Generate HTML for plot content (correlation, histogram, or global map)."""
    html_parts = [f'<div class="plot-content {plot_type}-content" id="{var_id}_{plot_type}" style="{display_style}">']
    
    # For map plots, don't use wavelength tabs - show all images directly
    if plot_type == 'map' or not data['has_wavelengths']:
        # No wavelength dependency - show all files directly
        for file_info in files:
            fname = file_info['filename']
            fpath = os.path.join(folder_path, fname)
            b64 = encode_image_to_base64(fpath, factor=resolution_factor, quality=quality)
            if b64:
                html_parts.append(f'<h4>{fname}</h4>')
                html_parts.append(f'<img src="data:image/png;base64,{b64}" alt="{fname}">')
    else:
        # Use wavelength tabs for corr and hist plots
        wv_files = defaultdict(list)
        for file_info in files:
            wv = file_info['wavelength'] or 'no_wv'
            wv_files[wv].append(file_info)
        
        # Custom sorting for wavelengths
        def sort_wavelength(wv):
            if wv == 'no_wv':
                return (0, 0)
            elif '_' in str(wv):  # For angstrom patterns like 440_670
                return (1, int(wv.split('_')[0]))
            else:
                return (1, int(wv))
        
        # Generate wavelength tabs
        html_parts.append('<div class="wavelength-tabs">')
        for wv in sorted(wv_files.keys(), key=sort_wavelength):
            if wv == 'no_wv':
                wv_display = 'All Wavelengths'
            elif '_' in str(wv):
                wv_display = f"λ{wv}nm"
            else:
                wv_display = f"λ{wv}nm"
            
            html_parts.append(f'<span class="wavelength-tab" onclick="showWavelength(\'{var_id}\', \'{wv}\', \'{plot_type}\')">{wv_display}</span>')
        html_parts.append('</div>')
        
        # Generate content for each wavelength
        for wv in sorted(wv_files.keys(), key=sort_wavelength):
            wv_container_id = f"{var_id}_wv_{wv}_{plot_type}_content"
            html_parts.append(f'<div id="{wv_container_id}" style="display: none;">')
            
            # Add images
            for file_info in wv_files[wv]:
                fname = file_info['filename']
                fpath = os.path.join(folder_path, fname)
                b64 = encode_image_to_base64(fpath, factor=resolution_factor, quality=quality)
                if b64:
                    html_parts.append(f'<h4>{fname}</h4>')
                    html_parts.append(f'<img src="data:image/png;base64,{b64}" alt="{fname}">')
            
            html_parts.append('</div>')
    
    html_parts.append('</div>')  # End plot-content
    return '\n'.join(html_parts)
    
def generate_html_for_variable(suite, variable, data, folder_path, variable_display_names, resolution_factor, quality):
    """Generate HTML for a single variable within a suite."""
    var_id = f"{suite}_{variable}".replace(' ', '_').replace('/', '_')
    
    html_parts = [
        f'<div class="image-container" id="{var_id}">',
        f'<h3>{variable_display_names.get(variable, variable.replace("_", " ").title())}</h3>'
    ]
    
    # Generate CSV URLs for this variable
    csv_urls = generate_csv_urls(folder_path, suite, variable)
    
    # Separate different plot types
    corr_files = [f for f in data['files'] if f['plot_type'] == 'corr']
    hist_files = [f for f in data['files'] if f['plot_type'] == 'hist']
    map_files = [f for f in data['files'] if f['plot_type'] == 'map']  # Global map files
    
    # Add criteria buttons - include Global Map if available
    buttons_to_show = []
    if corr_files:
        buttons_to_show.append(('corr', '📊 Correlation'))
    if hist_files:
        buttons_to_show.append(('hist', '📈 Distribution'))
    if map_files:
        buttons_to_show.append(('map', '🗺️ Global Map'))  # Add global map button
    buttons_to_show.append(('download', '💾 Download Data'))
    
    if buttons_to_show:
        html_parts.append('<div class="criteria-buttons">')
        for i, (btn_type, btn_label) in enumerate(buttons_to_show):
            active_class = ' active' if i == 0 and btn_type != 'download' else ''
            html_parts.append(f'<button class="criteria-btn {btn_type}{active_class}" onclick="{"showCriteria" if btn_type != "download" else "toggleDownloadLinks"}(\'{var_id}\', \'{btn_type}\')">{btn_label}</button>')
        html_parts.append('</div>')
    
    # Add download links section
    html_parts.append(f'<div class="download-links" id="{var_id}_downloads">')
    html_parts.append('<strong>📥 Download CSV Data Files:</strong><br>')
    html_parts.append(f'<a href="{csv_urls["target_mean"]}" class="download-link" target="_blank">AERONET Mean</a>')
    html_parts.append(f'<a href="{csv_urls["target_std"]}" class="download-link" target="_blank">AERONET Std</a>')
    html_parts.append(f'<a href="{csv_urls["pace_mean"]}" class="download-link" target="_blank">PACE Mean</a>')
    html_parts.append(f'<a href="{csv_urls["pace_std"]}" class="download-link" target="_blank">PACE Std</a>')
    html_parts.append('</div>')
    
    # Generate content for correlation plots if they exist
    if corr_files:
        html_parts.append(generate_plot_content(var_id, data, corr_files, 'corr', folder_path, resolution_factor, quality))
    
    # Generate content for histogram plots if they exist
    if hist_files:
        display_style = 'display: none;' if corr_files else ''
        html_parts.append(generate_plot_content(var_id, data, hist_files, 'hist', folder_path, resolution_factor, quality, display_style))
    
    # Generate content for global map plots if they exist
    if map_files:
        display_style = 'display: none;' if corr_files or hist_files else ''
        html_parts.append(generate_plot_content(var_id, data, map_files, 'map', folder_path, resolution_factor, quality, display_style))
    
    html_parts.append('</div>')  # End image-container
    return '\n'.join(html_parts)

def generate_html_for_suite(suite, suite_variables, folder_path, variable_display_names, resolution_factor, quality):
    """Generate HTML for a single suite and all its variables."""
    suite_class = get_suite_css_class(suite)
    suite_description = get_suite_description(suite)
    
    html_parts = [
        f'<div class="{suite_class}">',
        f'<div class="suite-title">{suite}</div>',
        f'<div class="suite-description">{suite_description}</div>'
    ]
    
    # Variable buttons for this suite - sorted according to specified order
    sorted_variables = sort_variables(list(suite_variables.keys()))
    html_parts.append('<div class="variable-buttons">')
    for variable in sorted_variables:
        display_name = variable_display_names.get(variable, variable.replace('_', ' ').title())
        var_id = f"{suite}_{variable}".replace(' ', '_').replace('/', '_')
        html_parts.append(f'<button class="variable-btn" onclick="toggleVariable(\'{var_id}\')">{display_name}</button>')
    html_parts.append('</div>')
    
    # Content for each variable
    for variable in sorted_variables:
        html_parts.append(generate_html_for_variable(suite, variable, suite_variables[variable], 
                                                   folder_path, variable_display_names, 
                                                   resolution_factor, quality))
    
    html_parts.append('</div>')  # End suite-container
    return '\n'.join(html_parts)

def process_suites_and_generate_html(parsed_files, suites, folder_path, resolution_factor, quality):
    """Process all suites and generate HTML content for each."""
    # Create mapping from keys to display names for variables
    variable_display_names = get_variable_display_names()
    
    # Define suite order for display
    suite_order = ['AOD15', 'SDA15', 'ALM15', 'HYB15', 'LWN15', 'SEABASS_ALL','SEABASS_OCI',\
                   'MAN_AOD15_series', 'MAN_SDA15_series',
                  'HSRL2_R1', 'HSRL2_R0', 'HSRL2_RA','ATL_ALD_2A']
    
    # Group by suite
    suites_data = defaultdict(lambda: defaultdict(list))
    for key, data in parsed_files.items():
        suite = data['suite'] 
        variable = data['variable']
        suites_data[suite][variable] = data
    
    # Process suites in defined order, then any additional ones
    processed_suites = set()
    all_suites_to_process = []
    
    # Add suites from predefined order that exist in the data
    for suite in suite_order:
        if suite in suites_data:
            all_suites_to_process.append(suite)
            processed_suites.add(suite)
    
    # Add any other suites found in the data
    for suite in sorted(suites_data.keys()):
        if suite not in processed_suites:
            all_suites_to_process.append(suite)
    
    # Build HTML for all suites
    html_parts = []
    
    for suite in all_suites_to_process:
        html_parts.append(generate_html_for_suite(suite, suites_data[suite], folder_path, 
                                                variable_display_names, resolution_factor, quality))
    
    return '\n'.join(html_parts)