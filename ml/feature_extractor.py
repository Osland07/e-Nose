import pandas as pd
import numpy as np

def extract_features(df):
    """Ekstraksi fitur statistik + rasio dari 8 sensor gas."""
    
    sensors = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']
    features = {}
    epsilon = 1e-6

    for col in sensors:
        if col not in df.columns:
            print(f"⚠ Kolom '{col}' tidak ditemukan → isi 0")
            for stat in ['mean', 'std', 'min', 'max', 'range', 'skew', 'kurt']:
                features[f'{col}_{stat}'] = 0
            continue

        # Konversi jika ada koma
        if df[col].dtype == 'object':
            df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')

        df[col] = df[col].fillna(0)

        features[f'{col}_mean'] = df[col].mean()
        features[f'{col}_std'] = df[col].std()
        features[f'{col}_min'] = df[col].min()
        features[f'{col}_max'] = df[col].max()
        features[f'{col}_range'] = df[col].max() - df[col].min()
        features[f'{col}_skew'] = df[col].skew()
        features[f'{col}_kurt'] = df[col].kurtosis()

    # Rasio penting
    features['mq2_mq135_ratio'] = features['MQ2_mean'] / (features['MQ135_mean'] + epsilon)
    features['mq3_mq135_ratio'] = features['MQ3_mean'] / (features['MQ135_mean'] + epsilon)
    features['mq4_mq135_ratio'] = features['MQ4_mean'] / (features['MQ135_mean'] + epsilon)

    # Rasio ke QCM
    for s in ['MQ2','MQ3','MQ4','MQ6','MQ7','MQ8','MQ135']:
        features[f"{s}_qcm_ratio"] = features[f"{s}_mean"] / (features["QCM_mean"] + epsilon)

    return features
