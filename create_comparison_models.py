import pandas as pd
import numpy as np
import joblib
import os
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from ml.feature_extractor import extract_features

# --- KONFIGURASI ---
MODEL_DIR = "model"
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

print("--- GENERATING MULTI-MODEL COMPARISON ---")

# 1. GENERATE DATA LATIHAN (Sama seperti Realistic Model)
data_rows = []
labels = []
SAMPLES = 200

# Kelas Aman (Nilai Rendah)
for _ in range(SAMPLES):
    row = {s: 20.0 + np.random.uniform(-5, 5) for s in ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']}
    data_rows.append(row)
    labels.append("Udara Bersih")

# Kelas Bahaya (Nilai Tinggi)
for _ in range(SAMPLES):
    row = {}
    # Pola khas: MQ135 dan QCM sangat tinggi
    for s in ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8']:
        row[s] = 400.0 + np.random.uniform(-50, 50)
    row['MQ135'] = 800.0 + np.random.uniform(-50, 50)
    row['QCM'] = 900.0 + np.random.uniform(-50, 50)
    
    data_rows.append(row)
    labels.append("Terdeteksi Biomarker")

# Preprocessing
df_raw = pd.DataFrame(data_rows)
processed_features = [extract_features(pd.DataFrame([row])) for _, row in df_raw.iterrows()]
X_df = pd.DataFrame(processed_features).fillna(0)

le = LabelEncoder()
y = le.fit_transform(labels)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_df)
feature_columns = X_df.columns.tolist()

# --- DEFINISI MODEL ---
models_to_train = [
    {
        "name": "MODEL_SVM_PRO.joblib",
        "model": SVC(kernel='rbf', probability=True)
    },
    {
        "name": "MODEL_SVM_LINEAR.joblib",
        "model": SVC(kernel='linear', probability=True)
    },
    {
        "name": "MODEL_RANDOM_FOREST.joblib",
        "model": RandomForestClassifier(n_estimators=100, random_state=42)
    },
    {
        "name": "MODEL_KNN.joblib", # K-Nearest Neighbors
        "model": KNeighborsClassifier(n_neighbors=5)
    },
    {
        "name": "MODEL_NEURAL_NET.joblib", # MLP (Versi Ringan dari Deep Learning)
        "model": MLPClassifier(hidden_layer_sizes=(50, 50), max_iter=500)
    }
]

# --- TRAINING LOOP ---
for m in models_to_train:
    print(f"Training {m['name']}...")
    clf = m['model']
    clf.fit(X_scaled, y)
    
    payload = {
        'model': clf,
        'scaler': scaler,
        'columns': feature_columns
    }
    
    save_path = os.path.join(MODEL_DIR, m['name'])
    joblib.dump(payload, save_path)
    print(f"✅ Saved: {save_path}")

print("\n--- SELESAI ---")
print("Buka Aplikasi GUI, dan lihat di Dropdown 'Pilih Model'.")
print("Sekarang Anda punya 4 otak berbeda untuk dicoba!")
