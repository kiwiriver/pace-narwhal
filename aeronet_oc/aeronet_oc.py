"""
read original df0 file: df0=get_f0_tsis(f0_file)
read integrated df0 file: df0=pd.read_csv(f0_file,index_col=0)
"""
import numpy as np
import pandas as pd


def get_df0_avg(df0, bandwidth=10):
    """
    get df0 with integration over all the aeronet oc bands in the file (some may be not used
    wvv2 are all the wavelength get from aeronet oc files
    """

    #path5='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data/LWN15/'
    #file5='aeronet_v3_LWN15_ALL_20251001_20251001.txt'
    #wvv2=get_aeronet_oc_wv(path5+file5)
    
    wvv2=[340,  380,  400,  412,  440,  443,  490,  500,  510,  531,  532,
        551,  555,  560,  620,  667,  675,  681,  709,  779,  865,  870,
       1020]
    
    bvv2 = np.repeat(bandwidth, len(wvv2))
    
    f0avg2, stats2 = trapezoidal_mean_in_bands(df0, wvv2, bvv2)
    
    df2=pd.DataFrame()
    df2['wv']=wvv2
    df2['bv']=bvv2
    df2['f0']=f0avg2
    df2.to_csv(f'f0_tsis_aeronet_oc_bw{bandwidth}.csv')
    
    return df2
    
def get_aeronet_oc_wv(file):
    
    df5=pd.read_csv(file, skiprows=5)

    key1v=[]
    wvv=[]
    for key1 in df5.keys():
        if 'Exact_Wavelengths(um)' in key1:
            key1v.append(key1)

    print("all wv keys", key1v)

    wvvstr=[key1.split('Exact_Wavelengths(um)_')[1] for key1 in key1v]

    print("wv values", wvvstr)

    wvv2 = np.array([np.int32(item) for item in wvvstr if item.isdigit()])
    print("valid wv values", wvv2)

    return wvv2

    
def get_aeronet_oc_rrs(df0, df3, key1='Lwn_f/Q[', key2='Exact_Wavelengths(um)_'):
    """
    Rrs = Lwn/F0, 

    Input: df0 contains f0 already integrated at the corresponding wavelength and bandwidth
    
    No need to divide f0*cos(sz), 
    if needed sz can be found:
    #key1='Solar_Zenith_Angle'
    #key1v=get_aeronet_oc_key(key1, df3)
    
    """

    df3 = df3.replace(-999, np.nan)
    df3 = df3.dropna(axis=1, how='all')

    key1v=get_aeronet_oc_key(key1, df3)
    lwn1 = df3[key1v].values

    #at the selected wavelength
    key2v=get_aeronet_oc_key(key2, df3)
    wvv2 = np.array([np.int32(keyt.split(key2)[1]) for keyt in key2v])

    try:
        f0avg2 = df0[df0['wv'].isin(wvv2)]['f0'].values
        wvavg2 = df0[df0['wv'].isin(wvv2)]['wv'].values
        
    except:
        print("****aeronet oc wavelength do not match****")
        sys.exit()

    rrs2 = lwn1/f0avg2

    return wvv2, rrs2
    
def get_aeronet_oc_key(key2, df3):
    """
    based on key2 pattern, return all the keys

    Typical variables: 
    key2v=['Lwn_f/Q[', 'Lwn_IOP[', 'Lwn[', 'LwQ[', 'Lw[', 'Solar_Zenith_Angle', 'Exact_Wavelengths(um)']
    key2v2=['Lwn_f/Q', 'Lwn_IOP', 'Lwn', 'LwQ', 'Lw']

    Variable of interests: 'Total_Ozone(Du)','Total_NO2(DU)','Total_Precipitable_Water(cm)','Chlorophyll-a','Wind_Speed(m/s)','Pressure(hPa)'
    
    Typical wavelength: 400,  412,  443,  490,  510,  560,  620,  667,  779,  865, 1020
    
    From AERONET OC website: The most recent SeaPRISM system configuration performs ocean color measurements 
    at the 400, 412.5, 442.5, 490, 510, 560, 620, 665, and 667 nm center-wavelengths. 
    Additional measurements are performed at 709, 865, and 1020 nm for quality checks, 
    turbid water flagging, and for the application of alternative above-water methods (Zibordi et al. 2002).
    
    """
    key1v=[]
    wvv=[]
    for key1 in df3.keys():
        if key2 in key1:
            key1v.append(key1)
    return key1v
    
def get_f0_tsis(file):
    """
    f0 downloaded from: https://oceancolor.gsfc.nasa.gov/resources/docs/rsr/sources/lores/f0_tsis.txt
    Unit: mW/cm^2/um
    """
    
    df0=pd.read_csv(file, skiprows=14, sep='\s+', index_col=0)
    df0 = df0.reset_index()
    df0=df0.rename(columns={
        df0.columns[0]: 'wv',    # Rename first column to 'wv'
        df0.columns[1]: 'f0'     # Rename second column to 'f0'
    })
    return df0
    
def trapezoidal_mean_in_bands(df0, wvv, bvv):
    """
    Calculate mean f0 values using trapezoidal integration method
    Mean = Integrated_area / bandwidth
    """
    mean_values = []
    band_info = []
    
    for i, (center_wv, bandwidth) in enumerate(zip(wvv, bvv)):
        # Define band edges
        wv_min = center_wv - bandwidth / 2
        wv_max = center_wv + bandwidth / 2
        
        # Filter data within the band
        mask = (df0['wv'] >= wv_min) & (df0['wv'] <= wv_max)
        band_data = df0[mask].sort_values('wv')  # Sort by wavelength
        
        if len(band_data) > 1:
            # Use trapezoidal integration
            integrated_area = np.trapz(band_data['f0'], band_data['wv'])
            actual_width = band_data['wv'].max() - band_data['wv'].min()
            mean_f0 = integrated_area / actual_width if actual_width > 0 else band_data['f0'].mean()
            n_points = len(band_data)
            
        elif len(band_data) == 1:
            # Single point - use that value
            mean_f0 = band_data['f0'].iloc[0]
            n_points = 1
            
        else:
            # No data in band
            mean_f0 = np.nan
            n_points = 0
        
        mean_values.append(mean_f0)
        band_info.append({
            'band': i+1,
            'center_wv': center_wv,
            'bandwidth': bandwidth,
            'wv_min': wv_min,
            'wv_max': wv_max,
            'mean_f0_trapz': mean_f0,
            'n_points': n_points
        })
    
    return np.array(mean_values), pd.DataFrame(band_info)