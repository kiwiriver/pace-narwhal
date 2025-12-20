print("===load fastmapol function===")
import sys
mapolpath='../'
sys.path.append(mapolpath)

import warnings
warnings.filterwarnings("ignore")

import os

# compute the directory that holds this __init__.py
_pkg_dir = os.path.dirname(__file__)

# for every immediate subfolder under tools/
for name in os.listdir(_pkg_dir):
    sub = os.path.join(_pkg_dir, name)
    # skip non-dirs and private dirs
    if os.path.isdir(sub) and not name.startswith("_"):
        # append it to the package search path
        __path__.append(sub)


#check version:
import sys
import xarray as xr
import numpy as np

print(f"Python version: {sys.version}")
print(f"Python version (short): {sys.version_info}")
print(f"xarray version: {xr.__version__}")
print(f"numpy version: {np.__version__}")