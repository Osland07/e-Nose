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

# ... (kode atas tetap sama) ...

# Scale Data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_df)
feature_columns = X_df.columns.tolist()

# SAFETY CHECK: Pastikan data tidak kosong/nol semua
if X_scaled.shape[0] == 0:
    print("❌ FATAL ERROR: Tidak ada data features yang berhasil diekstrak.")
    exit()

print(f"\n📊 Statistik Data:")
print(f"   - Total Sampel: {len(X_scaled)}")
print(f"   - Jumlah Fitur per Sampel: {X_scaled.shape[1]}")
print(f"   - Sebaran Kelas: {dict(pd.Series(y).value_counts())}")
print(f"     (0 = {le.inverse_transform([0])[0]}, 1 = {le.inverse_transform([1])[0]})")

# Split Data (80% Latih, 20% Uji)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)

# 3. TRAINING LOOP
models_to_train = [
    {
        "name": "REAL_SVM.joblib",
        "model": SVC(kernel='rbf', probability=True)
    },
    {
        "name": "REAL_RANDOM_FOREST.joblib",
        "model": RandomForestClassifier(n_estimators=100, random_state=42)
    },
    {
        "name": "REAL_KNN.joblib",
        "model": KNeighborsClassifier(n_neighbors=3)
    },
    {
        "name": "REAL_NEURAL_NET.joblib",
        "model": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1000)
    }
]

print("\n" + "="*50)
print("   MULAI TRAINING & VALIDASI (Ujian Model)")
print("="*50)

for m in models_to_train:
    print(f"\n🤖 Sedang Melatih: {m['name']}...")
    clf = m['model']
    clf.fit(X_train, y_train)
    
    # UJIAN (Testing)
    y_pred = clf.predict(X_test)
    
    # Hitung Nilai
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=le.classes_)
    cm = confusion_matrix(y_test, y_pred)
    
    print(f"   ✅ Akurasi: {acc*100:.2f}%")
    print("   📝 Laporan Detail:")
    print(report)
    print(f"   🧩 Confusion Matrix (Benar vs Salah Tebak):")
    print(cm)
    
    # Simpan
    payload = {
        'model': clf,
        'scaler': scaler,
        'columns': feature_columns
    }
    save_path = os.path.join(MODEL_DIR, m['name'])
    joblib.dump(payload, save_path)

print("\n" + "="*50)
print("✅ SELESAI! Semua model tersimpan di folder 'model/'.")
print("👉 Silakan buka aplikasi GUI dan pilih model 'REAL_...' untuk pengujian.")
