import os
import re
from collections import defaultdict

# Usage:
main_var_order = ["validation_diff", 'AOD15', 'SDA15', 'ALM15', 'HYB15', 'MAN_AOD15', 'MAN_SDA15', 'LMN15']
sec_var_order = ['aot_wv', 'aot_fine_wv', 'aot_coarse_wv', 'ssa_wv', 'angstrom']

def get_image_files(folder_path):
    img_exts = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
    return [f for f in os.listdir(folder_path) if f.lower().endswith(img_exts)]
    
def parse_filename(filename):
    """
    Returns (main_var, sec_var, wavelength list)
    e.g. ("AOD15", "aot_fine_wv", [550])
    """
    name = filename.rsplit('.', 1)[0]
    parts = name.split('_')
    # Main var
    main_var = None
    for mv in main_var_order:
        if parts[0].startswith(mv):
            main_var = mv
            break
    # Secondary var: pick the **first** that matches the substring sequence in the filename
    sec_var = None
    idx = -1
    for sv in sec_var_order:
        sv_idx = name.find(sv)
        if sv_idx != -1:
            # Among all matches, pick the earliest, or the first in sec_var_order in case of tie
            if idx == -1 or sv_idx < idx:
                sec_var = sv
                idx = sv_idx
            break  # stop at first found in order
    # Wavelength: "wvNUMBER" if available, or (for angstrom) angstrom_NUMBER_NUMBER
    wavelengths = []
    if sec_var is not None and sec_var != "angstrom":
        m = re.search(rf"{sec_var}(\d+)", name)
        if m:
            wavelengths = [int(m.group(1))]
        else:
            wv_matches = re.findall(r'wv(\d+)', filename)
            if wv_matches:
                wavelengths = [int(wv_matches[0])]
    elif sec_var == "angstrom":
        ang_matches = re.findall(r'angstrom_(\d+_\d+|\d+)', filename)
        if ang_matches:
            wavelengths = [int(v) for v in ang_matches[0].split('_') if v.isdigit()]
    else:
        # fallback: just grab first wv###
        wv_matches = re.findall(r'wv(\d+)', filename)
        if wv_matches:
            wavelengths = [int(wv_matches[0])]
    return main_var, sec_var, wavelengths

def group_and_order(filenames):
    """Grouped: for each main_var, for each sec_var, for each wavelength (asc), all matching files."""
    buckets = defaultdict(list)
    all_wavelengths = set()
    for f in filenames:
        main_var, sec_var, wavelengths = parse_filename(f)
        wl = wavelengths[0] if wavelengths else None
        buckets[(main_var, sec_var, wl)].append(f)
        if wl is not None:
            all_wavelengths.add(wl)
    wv_sorted = sorted(all_wavelengths)
    print("wv_sorted", wv_sorted)
    
    ordered = []
    for mv in main_var_order:
        for sv in sec_var_order:
            for wl in wv_sorted:
                chunk = buckets.get((mv, sv, wl), [])
                ordered.extend(chunk)
            # No-wavelengths, after those with wavelength
            chunk = buckets.get((mv, sv, None), [])
            ordered.extend(chunk)
    # Extras
    expected_keys = set((mv, sv, wl) for mv in main_var_order for sv in sec_var_order for wl in ([None] + wv_sorted))
    for k, files in buckets.items():
        if k not in expected_keys:
            ordered.extend(files)
    return ordered

def ordered_image_list(filenames, priority_substrings=["aeronet_matchup"]):
    used = set()
    ordered = []
    for substr in priority_substrings:
        matching = [f for f in filenames if (substr in f) and (f not in used)]
        ordered.extend(matching)
        used.update(matching)
    rest = [f for f in filenames if f not in used]
    ordered_rest = group_and_order(rest)
    return ordered + ordered_rest
