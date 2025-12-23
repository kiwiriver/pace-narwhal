import re
import os
import math
import time
import traceback

from tqdm import tqdm
import xarray as xr
import pandas as pd
import numpy as np

from netCDF4 import Dataset
from scipy.spatial import cKDTree

import matplotlib.pyplot as plt
import cartopy
import cartopy.crs as ccrs

def plot_search(indexvv, boundingboxv, outfile=None):
    """
    plot the global map with candicate matchup pixels
    """
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    
    ax.add_feature(cartopy.feature.OCEAN, edgecolor='w', linewidth=0.01)
    ax.add_feature(cartopy.feature.LAND, edgecolor='w', linewidth=0.01)
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
    
    count = 0
    colors = plt.cm.tab10.colors  # 10 unique colors; change colormap if you have more than 10 groups
    
    for i, time1 in enumerate(indexvv.keys()):           # Each group (e.g. Aeronet site)
        col = colors[i % len(colors)]
        lons, lats = boundingboxv[time1]
        #print(lons)
        #print(lats)
        plt.plot(lons, lats, color=col, transform=ccrs.PlateCarree())
    
        for index in indexvv[time1]:                       # Each match within the group
            count += 1
            lon1, lat1 = index['aeronet_loc']     # Assuming index is a list and that the dict is at index[0]
            plt.plot(lon1, lat1, '.', color=col, transform=ccrs.PlateCarree())     # Note: plot(lon, lat), as this is (x, y)
            lon2, lat2 = index['pace_loc']
            plt.plot(lon2, lat2, '+', color=col, transform=ccrs.PlateCarree())
            
    print("total count", count)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Validation Matchup Locations')
    if(outfile):
        plt.savefig(outfile, dpi=300)
    plt.close()

def check_netcdf_file(nc_path):
    """
    Check if NetCDF file is accessible and not corrupted
    """
    print("     ***check file validity")
    try:
        # Check if file exists and has reasonable size
        if not os.path.exists(nc_path):
            print("     File does not exist")
            return False
        
        file_size = os.path.getsize(nc_path)
        if file_size == 0:
            print("     File is empty")
            return False
        
        if file_size < 1000:  # Very small file, likely corrupted
            print(f"     File too small ({file_size} bytes)")
            return False
        
        # Try both methods that your module uses
        try:
            # First try the same method as your module
            datatree = xr.open_datatree(nc_path, decode_timedelta=False)
            datatree.close()
            print("     ****File OK***** (datatree method)")
            return True
        except:
            # Fallback to dataset method
            with xr.open_dataset(nc_path, decode_times=False) as ds:
                _ = ds.attrs
                _ = list(ds.variables.keys())
            print("     ****File OK***** (dataset method)")
            return True
    
    except Exception as e:
        print("     ****File NOT OK*****", str(e))
        print("     Full traceback:")
        traceback.print_exc()
        return False 
        
def aeronet_search(aeronet_df1, filev, search_center_radius = 10, \
                   aeronet_lon_var='Longitude(decimal_degrees)', aeronet_lat_var='Latitude(decimal_degrees)', \
                   aeronet_site_var='Site_Name'):
    """
    search validation site location from the l2 granules:
    validation data structure may be used for other data such as pace_pax and earthcare,
    make the variable name flexible.

    filev is the l2 pace data, the variable names are fixed, no need to modify
    """
    locv = aeronet_df1[[aeronet_lon_var,aeronet_lat_var]].to_numpy()
    lon_loc, lat_loc = locv[:,0], locv[:,1]
    namev = aeronet_df1[aeronet_site_var].to_numpy()
    
    
    t1=time.time()
    
    indexvv={}
    boundingboxv={}
    
    for nc_path in tqdm(filev[:]):
        
        #print("***nc path:", nc_path)
        #check_netcdf_file(nc_path)

        try:
            datetime1 = re.search(r'(\d{8}T\d{6})', nc_path).group(1)
            #dataset = xr.open_datatree(nc_path, group='geolocation_data')
            #dataset = xr.open_dataset(nc_path, group='geolocation_data')

            #use datatree instead of dataset to avoid mixing configuration of xarray
            datatree = xr.open_datatree(nc_path, decode_timedelta=False)
            dataset = xr.merge(datatree.to_dict().values())
        
            lon_variable = dataset['longitude'].values
            lat_variable = dataset['latitude'].values
            lons, lats = get_boundingbox(lon_variable, lat_variable)
            boundingboxv[datetime1]=[lons, lats]

            #print("load lat and lon from nc file")
            
            indexv = get_match(datetime1, lon_variable, lat_variable, lon_loc, lat_loc, namev, search_center_radius = search_center_radius)
            indexvv[datetime1]=indexv

        except Exception as e:
            print(f"  Error searching path {nc_path}: {str(e)}")
            print("  Full traceback:")
            traceback.print_exc()
        
    t2=time.time()
    print("total time cost", t2-t1)
    return indexvv, boundingboxv
    
#everything is in the sequence of lon, lat
def get_dis(loc1, loc2):
    """get distance in km"""
    return np.sqrt((loc1[0]-loc2[0])**2+(loc1[1]-loc2[1])**2)*110
    
def haversine(loc1, loc2):
    """
    lon1, lat1 = loc1
    lon2, lat2= loc2
    """
    lon1, lat1 = loc1
    lon2, lat2 = loc2
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lon1 = math.radians(lon1)
    lat1 = math.radians(lat1)

    lon2 = math.radians(lon2)
    lat2 = math.radians(lat2)
     
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate the distance
    distance = R * c

    return distance
    
def get_kdtree(lon_pace, lat_pace):
    """construct kdtree"""
    
    # Flatten the 2D matrices into 1D arrays
    
    flat_lons = lon_pace.flatten()
    flat_lats = lat_pace.flatten()
    
    # Combine latitudes and longitudes into a 2D array of coordinates
    coordinates = np.column_stack((flat_lons, flat_lats))
    
    # Build a KD-tree using these combined coordinates
    kdtree = cKDTree(coordinates)
    return kdtree

def get_match(datetime1, lon_pace, lat_pace, lon_aeronet, lat_aeronet, namev, search_center_radius = 5):
    """
    find the locations which match the kdtree
    datetime1 is for the kdtree from a harpcube sat data file
    search_center_radius = 5 in km, convert to degree by /110km.

    locv and namev are in the same dimension

    dis0: kdtree search, direct line in km
    dis1: consider earth curvature
    dis2: direct line


    input: lon, lat
    output: also in (lon, lat) pairs
    """

    kdtree = get_kdtree(lon_pace, lat_pace)
    
    indexv=[]
    #print(len(locv))
    
    for i1 in range(len(lon_aeronet)):
        #print(list(range(len(locv))))
        #print(i1)
        # Perform a nearest neighbor search for a target point (e.g., target_lat, target_lon)
        name = namev[i1]
        target_lon = lon_aeronet[i1] #locv[i1,0]
        target_lat = lat_aeronet[i1] #ocv[i1,1]
        target_point = np.array([target_lon, target_lat])

        dis0, indices = kdtree.query(target_point)
        dis0 = dis0*110

        if(dis0<=search_center_radius):

            #nearest_neighbor_coordinates = coordinates[indices_within_radius[j1]]
            original_indices = np.unravel_index(indices, lat_pace.shape)
            new_point=[lon_pace[original_indices], lat_pace[original_indices]]

            
            dis1 = haversine(target_point, new_point) #real distance
            dis2 = get_dis(target_point, new_point) #estimated distance with straight line
            data1 = [i1, datetime1, original_indices,\
                    dis0, dis1, dis2, target_point, new_point]

            data1 = {'site_index':i1, 'site':name,'pace_date': datetime1, \
                     'pace_loc_index':original_indices,\
                     'distance0_kdtree':dis0, 'distance1_haversine':dis1, 'distance2_euclidean':dis2, \
                     'aeronet_loc':target_point, 'pace_loc':new_point}
            

    
            #indexv1.append(data1)
            #print(data1)    
            #indexv.append(indexv1)
            indexv.append(data1)
    
    return indexv

def get_boundingbox(lon, lat):
    lons = [lon[0,0], lon[0,-1], lon[-1,-1], lon[-1,0], lon[0,0]]
    lats = [lat[0,0], lat[0,-1], lat[-1,-1], lat[-1,0], lat[0,0]]
    
    boundingbox = [lons, lats]
    return boundingbox