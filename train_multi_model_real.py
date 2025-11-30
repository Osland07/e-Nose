import os
import pandas as pd
import numpy as np
import glob
import joblib
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from ml.feature_extractor import extract_features

# --- KONFIGURASI PATH ---
BASE_DATA_PATH = 'sample_data'
MODEL_DIR = "model"

if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

print("--- TRAINING REAL DATA (MULTI-MODEL) ---")

# 1. LOAD DATA OTOMATIS (Auto-Detect Folder)
all_features = []
all_labels = []

if not os.path.exists(BASE_DATA_PATH):
    print(f"❌ Error: Folder '{BASE_DATA_PATH}' tidak ditemukan!")
    exit()

# Scan subfolder
subfolders = [f.path for f in os.scandir(BASE_DATA_PATH) if f.is_dir()]
print(f"🔎 Ditemukan {len(subfolders)} Kelas Label.")

for folder_path in subfolders:
    label_name = os.path.basename(folder_path)
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    print(f"   📂 {label_name}: {len(csv_files)} file")
    
    for fpath in csv_files:
        try:
            df = pd.read_csv(fpath, sep=';', decimal=',')
            # Validasi kolom
            if df.shape[1] < 8: continue
            
            feats = extract_features(df)
            all_features.append(feats)
            all_labels.append(label_name)
        except: pass

if not all_features:
    print("❌ Tidak ada data valid!")
    exit()

# 2. PREPROCESSING
print("\n⚙️ Memproses Data...")
X_df = pd.DataFrame(all_features).fillna(0)
le = LabelEncoder()
y = le.fit_transform(all_labels)

print(f"   Mapping Label: {dict(zip(le.classes_, le.transform(le.classes_)))}")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_df)
feature_columns = X_df.columns.tolist()

# Split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)

# 3. TRAINING LOOP
models_to_train = [
    {"name": "REAL_SVM.joblib", "model": SVC(kernel='rbf', probability=True)},
    {"name": "REAL_RANDOM_FOREST.joblib", "model": RandomForestClassifier(n_estimators=100)},
    {"name": "REAL_KNN.joblib", "model": KNeighborsClassifier(n_neighbors=3)},
    {"name": "REAL_NEURAL_NET.joblib", "model": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500)}
]

print("\n" + "="*40)
for m in models_to_train:
    print(f"🔥 Melatih {m['name']}...")
    clf = m['model']
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"   ✅ Akurasi: {acc*100:.2f}%")
    
    payload = {'model': clf, 'scaler': scaler, 'columns': feature_columns}
    joblib.dump(payload, os.path.join(MODEL_DIR, m['name']))

print("\n✅ SELESAI! Model siap digunakan.")