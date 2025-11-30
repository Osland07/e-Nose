import pandas as pd
import numpy as np
import joblib
import os
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from ml.feature_extractor import extract_features

# --- KONFIGURASI ---
MODEL_DIR = "model"
MODEL_NAME = "REALISTIC_MODEL.joblib"
SAMPLES_PER_CLASS = 100

print("--- GENERATING REALISTIC SYNTHETIC DATA ---")

# Kita buat data latih yang MIRIP dengan apa yang dihasilkan Arduino 'realistic_sim.ino'
data_rows = []
labels = []

# 1. Generate Data "Tidak Terdeteksi" (Udara Bersih)
# Karakteristik: Nilai 20-40, Noise rendah
for _ in range(SAMPLES_PER_CLASS):
    row = {}
    # MQ & QCM
    for i, sensor in enumerate(['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']):
        base = 30.0 + (i * 2)
        noise = np.random.uniform(-2, 2)
        row[sensor] = base + noise
    
    data_rows.append(row)
    labels.append("Tidak Terdeteksi")

# 2. Generate Data "Terdeteksi Biomarker" (Daging)
# Karakteristik: Sesuai dengan coding Arduino (MQ135 & QCM tinggi)
for _ in range(SAMPLES_PER_CLASS):
    row = {}
    # Tambahkan random noise biar SVM belajar sebarannya
    row['MQ2'] = 150.0 + np.random.uniform(-5, 5)
    row['MQ3'] = 300.0 + np.random.uniform(-10, 10)
    row['MQ4'] = 120.0 + np.random.uniform(-5, 5)
    row['MQ6'] = 80.0 + np.random.uniform(-5, 5)
    row['MQ7'] = 90.0 + np.random.uniform(-5, 5)
    row['MQ8'] = 180.0 + np.random.uniform(-5, 5)
    row['MQ135'] = 550.0 + np.random.uniform(-15, 15) # Signifikan
    row['QCM'] = 600.0 + np.random.uniform(-20, 20)   # Signifikan
    
    data_rows.append(row)
    labels.append("Terdeteksi Biomarker")

# Buat DataFrame
df_raw = pd.DataFrame(data_rows)

print("--- EXTRACTING FEATURES ---")
# Ekstraksi fitur (Mean, Std, Skew, dll)
processed_features = []
for _, row_series in df_raw.iterrows():
    # Konversi Series ke DataFrame 1 baris
    row_df = pd.DataFrame([row_series]) 
    feats = extract_features(row_df)
    processed_features.append(feats)

X_df = pd.DataFrame(processed_features).fillna(0)

print("--- TRAINING SVM MODEL ---")
# Label Encoding
le = LabelEncoder()
y = le.fit_transform(labels)

# Scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_df)
feature_columns = X_df.columns.tolist()

# Train SVM (RBF Kernel - Standar untuk data sensor non-linear)
model = SVC(kernel='rbf', C=10, gamma='scale', probability=True)
model.fit(X_scaled, y)

# Simpan
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

payload = {
    'model': model,
    'scaler': scaler,
    'columns': feature_columns
}

save_path = os.path.join(MODEL_DIR, MODEL_NAME)
joblib.dump(payload, save_path)

print(f"\n✅ Model Realistis Berhasil Disimpan: {save_path}")
print(f"   Label: {le.classes_}")
print("   Gunakan model ini bersama Arduino code 'realistic_sim.ino'")
