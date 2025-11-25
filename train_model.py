# ============================================================ 
# IMPORT LIBRARY 
# ============================================================ 
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
import warnings
import glob
import joblib

warnings.filterwarnings('ignore')

# ============================================================ 
# KONFIGURASI PATH DAN LABEL 
# ============================================================ 
BASE_PATH = 'sample_data'
MODEL_DIR = "model"
NEW_MODEL_NAME = "pork_detection_model.joblib"

label_map = {
    'Sapi': 'Tidak Terdeteksi',
    'Babi': 'Terdeteksi Daging Babi',
    'Sapi Babi': 'Terdeteksi Daging Babi'
}

# ============================================================ 
# FUNGSI EKSTRAKSI FITUR SENSOR 
# ============================================================ 
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


# ============================================================ 
# LOAD SELURUH DATASET 
# ============================================================ 
all_features = []
all_labels = []

print("\nMemuat seluruh file CSV dari direktori 'sample_data'...\n")

for folder_name, label in label_map.items():
    folder_path = os.path.join(BASE_PATH, folder_name)
    if not os.path.exists(folder_path):
        print(f"⚠  Folder tidak ditemukan: {folder_path}")
        continue
        
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

    if not csv_files:
        print(f"⚠ Folder '{folder_name}' kosong!")
        continue

    print(f"📂 Folder: {folder_name} → {len(csv_files)} file")

    for file_path in csv_files:
        try:
            # Menggunakan semicolon sebagai separator
            df = pd.read_csv(file_path, sep=';', decimal=',')
            if df.empty:
                print(f"File {file_path} kosong.")
                continue
            features = extract_features(df)
            all_features.append(features)
            all_labels.append(label)
        except Exception as e:
            print(f"❌ Error memproses {file_path}: {e}")

if not all_features:
    print("\n❌ Tidak ada data yang berhasil dimuat. Tidak dapat melanjutkan proses training.")
    exit()

# ============================================================ 
# MEMBUAT DATAFRAME FITUR 
# ============================================================ 
X_df = pd.DataFrame(all_features).fillna(0)
y_series = pd.Series(all_labels, name="Label")

print("\nTotal dataset yang akan di-train:", len(X_df))
print("\nDistribusi kelas:")
print(y_series.value_counts())

# =
# PREPROCESSING
# ============================================================ 
le = LabelEncoder()
y = le.fit_transform(y_series)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_df)

# Simpan nama kolom setelah scaling
feature_columns = X_df.columns.tolist()

# SPLIT DATA
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.20, random_state=42, stratify=y
)

print(f"\nUkuran data latih: {len(X_train)} | Ukuran data uji: {len(X_test)}")

# ============================================================ 
# TRAINING SVM DENGAN GRIDSEARCH 
# ============================================================ 
print("\nMemulai training model SVM dengan GridSearchCV...")
param_grid = {
    'C': [1, 10, 100],
    'gamma': [0.1, 0.01, 0.001],
    'kernel': ['rbf']
}

grid = GridSearchCV(SVC(probability=True, random_state=42), param_grid, cv=3, refit=True, n_jobs=-1, verbose=1)
grid.fit(X_train, y_train)

best_model = grid.best_estimator_
print("\nParameter terbaik ditemukan:", grid.best_params_)

# ============================================================ 
# EVALUASI MODEL 
# ============================================================ 
y_pred = best_model.predict(X_test)

print("\n--- HASIL EVALUASI MODEL BARU ---")
print(f"Akurasi: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred, target_names=le.classes_))


# ============================================================ 
# SIMPAN MODEL, SCALER, DAN KOLOM 
# ============================================================ 
model_payload = {
    'model': best_model,
    'scaler': scaler,
    'columns': feature_columns 
}

if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

model_path = os.path.join(MODEL_DIR, NEW_MODEL_NAME)
joblib.dump(model_payload, model_path)

print(f"\n✅ Model baru berhasil disimpan di: {model_path}")
