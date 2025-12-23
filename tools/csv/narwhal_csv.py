"""
reformat csv into a more standard format
"""

import pandas as pd

def reformat_csv(file1, file2):
    
    df1=pd.read_csv(file1)
    df2=pd.read_csv(file2)
    
    #reformat df
    #target
    df1 = format_df_target(df1)
    #pace
    df2 = format_df_pace(df2)
    
    df3 = pd.merge(df1, df2)
    df1 = redefine_df(df3, str1='target_')
    df2 = redefine_df(df3, str1='pace_')
    #reset file1 and file2
    df1.to_csv(file1)
    df2.to_csv(file2)
    
def format_df_target(df1):

    # Step 1: First rename the specified columns
    df1 = df1.rename(columns={
        'datetime': 'pace_datetime',
        'count': 'target_count',
        'site': 'target_site',
        'datetime_aeronet': 'target_datetime'
    })
    
    # Step 2: Add 'target_' prefix to all remaining columns that don't already have it
    columns_to_rename = {}
    for col in df1.columns:
        if not col.startswith('target_') and not col.startswith('pace_'):
            columns_to_rename[col] = f'target_var_{col}'
    
    df1 = df1.rename(columns=columns_to_rename)
    
    return df1
    
def format_df_pace(df2):
    # Assuming your dataframe is called 'df2'
    
    # Step 1: Rename columns
    df2 = df2.rename(columns={
        'datetime': 'pace_datetime', 
        'timestamp': 'pace_timestamp',
        'site': 'target_site',
        'aeronet_lon': 'target_lon',
        'aeronet_lat': 'target_lat'  # Fixed the typo from 'aernet_lat'
    })

    # pace_date is duplicated with pace_datetime
    if 'pace_date' in df2.columns:
        df2 = df2.drop('pace_date', axis=1)
    
    # Step 2: Define column groups
    front_columns = ['pace_datetime', 'pace_timestamp', 'pace_lon', 'pace_lat', 'target_site', 'target_lon', 'target_lat']
    
    end_columns = ['pace_count','pace_aot_wv548', 'pace_chi2',  'pace_nv_ref', 
                   'pace_nv_dolp', 'pace_quality_flag', 'pace_loc_index_lon', 'pace_loc_index_lat',
                   'pace_distance1_haversine', 'pace_distance2_euclidean']
    
    # Step 3: Add 'pace_' prefix to end columns that don't already have it
    rename_dict = {}
    for col in ['aot_wv548', 'chi2', 'count', 'nv_ref', 'nv_dolp', 'quality_flag', 
                'distance1_haversine', 'distance2_euclidean']:
        if col in df2.columns:
            rename_dict[col] = f'pace_{col}'
    
    df2 = df2.rename(columns=rename_dict)
    
    # Step 4: Identify middle columns (those not in front or end)
    all_columns = df2.columns.tolist()
    middle_columns = [col for col in all_columns if col not in front_columns and col not in end_columns]
    
    # Step 5: Add 'pace_' prefix to middle columns that don't already contain 'pace_'
    middle_rename_dict = {}
    for col in middle_columns:
        if not col.startswith('pace_') and not col.startswith('target_'):
            middle_rename_dict[col] = f'pace_var_{col}'
    
    df2 = df2.rename(columns=middle_rename_dict)
    
    # Step 6: Update middle_columns list after renaming
    all_columns = df2.columns.tolist()
    middle_columns = [col for col in all_columns if col not in front_columns and col not in end_columns]
    
    # Step 7: Reorder the dataframe
    new_column_order = front_columns + middle_columns + end_columns
    df2 = df2[new_column_order]
    
    print("New column order:")
    print(df2.columns.tolist())
    return df2

def redefine_df(df3, str1='pace_'):
    """
    Redefine df1 from df3 with specified columns and put columns starting with str1 at the end
    
    Parameters:
    df3: Source dataframe
    str1: String prefix to move to end ('pace_' or 'target_')
    """
    
    # Get all columns that start with 'var_'
    var_columns = [col for col in df3.columns if col.startswith(str1+'var_')]
    
    # Define the base columns you want
    base_columns = ['pace_timestamp', 'pace_datetime', 'pace_lon', 'pace_lat', 
                'target_site', 'target_datetime', 'target_lon', 'target_lat']
    if(str1=='pace_'):
        base_columns = ['target_site', 'pace_datetime', 'pace_lon', 'pace_lat']
    elif(str1=='target_'):
        base_columns = ['target_site', 'target_datetime', 'target_lon', 'target_lat']
    else:
        print("str1 not valid")
        sys.exit(1)
    
    # Combine base columns with all var_ columns
    primary_columns = base_columns + var_columns
    
    # Filter to only include columns that actually exist in df3
    existing_primary_columns = [col for col in primary_columns if col in df3.columns]
    
    # Get the count column
    count_column = str1 + 'count'
    
    # Get columns that start with str1 (excluding those already in primary_columns and count column)
    str1_columns = [col for col in df3.columns 
                    if col.startswith(str1) and col not in existing_primary_columns and col != count_column]
    
    # Sort str1_columns for consistency
    str1_columns.sort()
    
    # Organize str1 columns: count first, then var columns, then others
    str1_count = [count_column] if count_column in df3.columns else []
    str1_var = [col for col in str1_columns if col.startswith(str1+'var_')]
    str1_other = [col for col in str1_columns if not col.startswith(str1+'var_')]
    
    # Final order for str1 columns: count, then var, then others
    ordered_str1_columns = str1_count + str1_var + str1_other
    
    # Final column order: primary columns first, then ordered str1 columns at the end
    final_columns = existing_primary_columns + ordered_str1_columns
    
    # Redefine df1
    df1 = df3[final_columns].copy()
    
    # Check for missing columns
    missing_columns = [col for col in primary_columns if col not in df3.columns]
    
    print(f"df1 redefined with {len(final_columns)} columns")
    print(f"Primary columns: {existing_primary_columns}")
    print(f"Columns starting with '{str1}' at the end:")
    print(f"  - Count: {str1_count}")
    print(f"  - Var: {str1_var}")
    print(f"  - Other: {str1_other}")
    
    if missing_columns:
        print(f"Warning: These primary columns were not found in df3: {missing_columns}")
    
    return df1