import numpy as np
import pandas as pd

def get_aodf(aodf500, aef500, wv):
    """compute aod at wv with sda data"""
    return aodf500*(500/wv)**(aef500)

def get_sda_aod(df1b, wvv=[440, 550, 670, 870]):
    """
    Compute AOD, fine, and coarse mode AODs from AERONET or MAN SDA data.
    
    Handles both naming conventions automatically:
    
    AERONET:
        Fine_Mode_AOD_500nm[tau_f]
        AE-Fine_Mode_500nm[alpha_f]
        Total_AOD_500nm[tau_a]
        Angstrom_Exponent(AE)-Total_500nm[alpha]
    
    MAN:
        Fine_Mode_AOD_500nm(tau_f)
        AE_Fine_Mode_500nm(alpha_f)
        Total_AOD_500nm(tau_a)
        Angstrom_Exponent(AE)_Total_500nm(alpha)
    """

    # Detect dataset type based on column names
    if any('[' in col for col in df1b.columns):
        # AERONET style
        fine_aod_col = 'Fine_Mode_AOD_500nm[tau_f]'
        fine_ae_col  = 'AE-Fine_Mode_500nm[alpha_f]'
        total_aod_col = 'Total_AOD_500nm[tau_a]'
        total_ae_col  = 'Angstrom_Exponent(AE)-Total_500nm[alpha]'
        dataset_type = "AERONET"
    else:
        # MAN style
        fine_aod_col = 'Fine_Mode_AOD_500nm(tau_f)'
        fine_ae_col  = 'AE_Fine_Mode_500nm(alpha_f)'
        total_aod_col = 'Total_AOD_500nm(tau_a)'
        total_ae_col  = 'Angstrom_Exponent(AE)_Total_500nm(alpha)'
        dataset_type = "MAN"

    # Extract variables safely (default to NaN if missing)
    def safe_get(col):
        return df1b[col].values if col in df1b.columns else np.full(len(df1b), np.nan)
    
    aodf500 = safe_get(fine_aod_col)
    aef500  = safe_get(fine_ae_col)
    aod500  = safe_get(total_aod_col)
    ae500   = safe_get(total_ae_col)

    df1c = pd.DataFrame()

    # Compute AODs for each wavelength
    for wv1 in wvv:
        aodf = get_aodf(aodf500, aef500, wv1)
        aod  = get_aodf(aod500, ae500, wv1)

        df1c[f'aot_wv{wv1}']        = aod
        df1c[f'aot_fine_wv{wv1}']   = aodf
        df1c[f'aot_coarse_wv{wv1}'] = aod - aodf

    print(f"Processed {dataset_type} SDA data ({len(df1b)} records)")
    return df1c