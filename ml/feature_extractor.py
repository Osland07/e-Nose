import pandas as pd
import numpy as np

def extract_features(df, active_sensors=None):
    """
    Ekstraksi fitur statistik + rasio dari sensor gas.
    Ini adalah SINGLE SOURCE OF TRUTH untuk ekstraksi fitur di seluruh proyek.
    Jangan membuat fungsi ekstraksi fitur duplikat di file lain.
    """
    
    # Default sensors jika tidak ada yang dipilih
    if active_sensors:
        sensors = active_sensors
    else:
        # Standar 8 Sensor E-Nose
        sensors = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']
        
    features = {}
    epsilon = 1e-6 # Untuk menghindari pembagian dengan nol

    # Normalisasi nama kolom input (Hapus spasi, Uppercase)
    # Agar 'MQ 3' terbaca sama dengan 'MQ3'
    df_cols_norm = {c.upper().strip().replace(' ', ''): c for c in df.columns}
    
    # 1. Statistik Dasar Per Sensor
    for sensor_name in sensors:
        col_std = sensor_name.upper() # Nama standar (misal MQ3)
        col_orig = df_cols_norm.get(col_std) # Nama asli di CSV (misal 'MQ 3')

        if not col_orig:
            # Jika sensor hilang dari data, isi 0 semua
            for stat in ['mean', 'std', 'min', 'max', 'range', 'skew', 'kurt']:
                features[f'{sensor_name}_{stat}'] = 0.0
            continue

        # Ambil series data
        series = df[col_orig]

        # Konversi numeric (handle koma desimal Indonesia)
        if series.dtype == 'object':
            series = pd.to_numeric(series.str.replace(',', '.'), errors='coerce')

        series = series.fillna(0)
        
        if len(series) == 0:
            # Handle file kosong
            for stat in ['mean', 'std', 'min', 'max', 'range', 'skew', 'kurt']:
                features[f'{sensor_name}_{stat}'] = 0.0
            continue

        # Hitung Statistik
        features[f'{sensor_name}_mean'] = float(series.mean())
        features[f'{sensor_name}_std']  = float(series.std())
        features[f'{sensor_name}_min']  = float(series.min())
        features[f'{sensor_name}_max']  = float(series.max())
        features[f'{sensor_name}_range'] = float(series.max() - series.min())
        features[f'{sensor_name}_skew'] = float(series.skew()) if len(series) > 1 else 0.0
        features[f'{sensor_name}_kurt'] = float(series.kurtosis()) if len(series) > 1 else 0.0

    # 2. Feature Engineering (Rasio Antar Sensor)
    # Helper untuk ambil nilai mean yang sudah dihitung di atas
    def get_mean(s):
        return features.get(f'{s}_mean', 0.0)

    # Rasio Penting (Domain Knowledge)
    features['mq2_mq135_ratio'] = get_mean('MQ2') / (get_mean('MQ135') + epsilon)
    features['mq3_mq135_ratio'] = get_mean('MQ3') / (get_mean('MQ135') + epsilon)
    features['mq4_mq135_ratio'] = get_mean('MQ4') / (get_mean('MQ135') + epsilon)

    # Rasio ke QCM (jika QCM ada)
    if 'QCM' in sensors:
        qcm_val = get_mean('QCM')
        for s in sensors:
            if s != 'QCM':
                features[f"{s}_qcm_ratio"] = get_mean(s) / (qcm_val + epsilon)

    return features