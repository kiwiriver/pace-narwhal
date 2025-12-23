import base64
from PIL import Image

import os
import re
from collections import defaultdict

def resize_and_compress_image(image_path, factor, output_format="JPEG", quality=85):
    """
    Resize and compress the image to reduce file size.
    """
    try:
        with Image.open(image_path) as img:
            new_width = max(1, img.width // factor)
            new_height = max(1, img.height // factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save the resized image as compressed data
            from io import BytesIO
            buffer = BytesIO()
            img.convert("RGB").save(buffer, format=output_format, quality=quality)
            return buffer.getvalue()
    except Exception as e:
        print(f"❌ Error resizing/compressing image '{image_path}': {e}")
        return None

def encode_image_to_base64(image_path, factor=1, output_format="JPEG", quality=85):
    """
    Encode an image to a Base64 string, optionally resizing/compressing it first.
    """
    try:
        if factor > 1:
            compressed_data = resize_and_compress_image(image_path, factor, output_format, quality)
            if compressed_data:
                return base64.b64encode(compressed_data).decode("utf-8")
        else:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ Error encoding image '{image_path}': {e}")
        return None


        f.write("</head>\n<body>\n")
        f.write(f"<h1>{title}</h1>\n<p>{title2 or ''}</p>\n")

def parse_filename(filename):
    """
    Parse filename to extract suite name, variable name, and wavelength info.
    Handles specific suite names: AOD15, SDA15, ALM15, HYB15, LWN15, SEABASS_ALL, SEABASS_OCI, 
                                  MAN_AOD15_series, MAN_SDA15_series
    Returns: (suite_name, variable_name, wavelength, plot_type)
    """
    # Remove file extension
    base_name = filename.replace('.png', '')
    
    # Handle MAN suite names specially (MAN_AOD15_series, MAN_SDA15_series)
    if base_name.startswith('MAN_'):
        # Look for exact patterns: MAN_AOD15_series, MAN_SDA15_series
        man_match = re.match(r'^(MAN_(?:AOD|SDA)15_series)_', base_name)
        if man_match:
            suite_name = man_match.group(1)
            remaining = base_name[len(suite_name)+1:]
        else:
            # If no match, treat as unknown MAN suite
            suite_name = 'MAN_UNKNOWN'
            remaining = base_name[4:]  # Remove 'MAN_'
    else:
        # Handle standard suite names: AOD15, SDA15, ALM15, HYB15, LWN15, SEABASS
        suite_match = re.match(r'^((?:AOD|SDA|ALM|HYB|LWN)15|HSRL2_R[01A]|ATL_ALD_2A|SEABASS_ALL|SEABASS_OCI)_', base_name)
        #suite_match = re.match(r'^((?:AOD|SDA|ALM|HYB|LWN)15)_', base_name)
        if suite_match:
            suite_name = suite_match.group(1)
            remaining = base_name[len(suite_name)+1:]
        else:
            # If no standard suite match found
            suite_name = 'UNKNOWN'
            remaining = base_name
    
    # Extract plot type (corr or hist)
    plot_type = 'corr' if remaining.endswith('_corr') else ('hist' if remaining.endswith('_hist') else 'other')
    
    # Remove plot type from remaining
    if plot_type != 'other':
        remaining = remaining[:-5]  # Remove '_corr' or '_hist'
    
    # Extract wavelength information
    wavelength = None
    wv_match = re.search(r'_wv(\d+)', remaining)
    if wv_match:
        wavelength = wv_match.group(1)
        # Remove wavelength from variable name
        remaining = re.sub(r'_wv\d+', '', remaining)
    elif re.search(r'_(\d+)_(\d+)', remaining):  # For angstrom_440_670 pattern
        wv_match = re.search(r'_(\d+)_(\d+)', remaining)
        wavelength = f"{wv_match.group(1)}_{wv_match.group(2)}"
        remaining = re.sub(r'_\d+_\d+', '', remaining)
    elif remaining.endswith('_wv'):  # For cases like "aot_wv" - treat as no specific wavelength
        remaining = remaining[:-3]  # Remove '_wv'
        wavelength = None  # No overview, just no specific wavelength
    
    variable_name = remaining
    
    return suite_name, variable_name, wavelength, plot_type

def get_variable_order():
    """
    Define the display order for variables
    """
    return [
        'aot', 'aot_fine', 'aot_coarse', 'ssa', 'mr', 'mi', 'vd_fine', 'vd_coarse', 'sph',
        # Additional variables
        'angstrom', 'angstrom_440_670', 'reff_fine', 'reff_coarse', 'veff_fine', 'veff_coarse',
        # Ocean/Water variables (LWN15)
        'chla', 'rrs', 'Rrs2_mean', 'rrs2_mean', 'wind_speed', 'sst', 'kd490', 'pic', 'poc', 'cdm', 'bbp',
        # MAN variables
        'series', 'statistics'
    ]

def sort_variables(variables):
    """
    Sort variables according to specified order
    """
    order = get_variable_order()
    order_dict = {var: i for i, var in enumerate(order)}
    
    def sort_key(var):
        return (order_dict.get(var, 999), var)
    
    return sorted(variables, key=sort_key)



