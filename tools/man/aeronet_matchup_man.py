"""
currently treat every point in MAN data as a seperate site
need clustering in location and time

"""
import pandas as pd
import glob

import os
import glob
import pandas as pd
from IPython.display import display, HTML

def format_man_df(df2, flag_man=True, flag_list=False):
    """
    if for man, every row become a different site
    AOD: Site_Latitude(Degrees),Site_Longitude(Degrees)
    MAN: 
    """
    if(flag_man):
        #MAN
        df2['Site_Name'] = df2['AERONET_Site'] + '_p'+df2.index.astype(str)
        df2['Longitude(decimal_degrees)']=df2['Longitude']
        df2['Latitude(decimal_degrees)']=df2['Latitude']
    else:
        #AERONET
        df2['Site_Name'] = df2['AERONET_Site']
        df2['Longitude(decimal_degrees)']=df2['Site_Longitude(Degrees)']
        df2['Latitude(decimal_degrees)']=df2['Site_Latitude(Degrees)']
    
    # Move all three to the front
    top_cols = ['Site_Name', 'Longitude(decimal_degrees)', 'Latitude(decimal_degrees)']
    other_cols = [col for col in df2.columns if col not in top_cols]
    
    if(flag_list):
        df2 = df2[top_cols]
    else:
        df2 = df2[top_cols + other_cols]

    #drop duplicated elements
    #for AERONET, only keep one row
    df2 = df2.drop_duplicates(subset=['Site_Name'])
    
    return df2

    
def get_file_list(base_path, tspan):
    """
    get all file path
    """

    # Generate date strings
    dates = pd.date_range(start=tspan[0], end=tspan[1], freq='D')
    date_strs = [d.strftime('%Y%m%d') for d in dates]

    pathv = []
    for ds in date_strs:
        dir_path = os.path.join(base_path, ds)
        pathv.append(dir_path)
    pathv.sort()
    return pathv


def get_man_all(man_path, tspan, flag_man=True, flag_list=False):
    """
    get all man data in the path and tspan
    """
    pathv = get_file_list(man_path, tspan)
    dfv2 = []
    
    for path1 in pathv:
        df2 = get_man_csv(path1, flag_man=flag_man, flag_list=flag_list)
        # Only append non-empty dataframes
        if not df2.empty:
            dfv2.append(df2)
    
    try:
        if dfv2:  # Check if the list is not empty
            dfv2 = pd.concat(dfv2, ignore_index=True)
        else:
            # Return an empty DataFrame if no data was found
            dfv2 = pd.DataFrame()
    except Exception as e:
        # Optionally log the error
        print(f"Error concatenating dataframes: {e}")
        dfv2 = pd.DataFrame()

    dfv2=dfv2.sort_values('Site_Name')
    
    return dfv2

def get_man_site(folder1, site1):
    dfv2 = get_man_csv(folder1)
    df2 = dfv2.loc[dfv2.Site_Name==site1]
    return df2
    
def get_man_csv(folder1, flag_man=True, flag_list=False):
    """
    combine all aeronet data together, and return df
    note that: some variables contains (int) some do not
    """
    filev2 = glob.glob(os.path.join(folder1, '*.csv'))
    dfv2 = []
    
    for file2 in filev2:
        df2 = pd.read_csv(file2)
        df2.columns = df2.columns.str.replace(r'\(int\)', '', regex=True)
        df2 = format_man_df(df2, flag_man=flag_man, flag_list=flag_list)
        dfv2.append(df2)

    try:
        if dfv2:  # Check if the list is not empty
            dfv2 = pd.concat(dfv2, ignore_index=True)
        else:
            # Return an empty DataFrame with the appropriate columns
            # You may need to adjust this based on your expected columns
            dfv2 = pd.DataFrame()  # or with specific columns: pd.DataFrame(columns=['col1', 'col2'])
    except Exception as e:
        # Optionally log the error
        print(f"Error concatenating dataframes: {e}")
        dfv2 = pd.DataFrame()  # Return empty dataframe in case of error
    
    return dfv2
