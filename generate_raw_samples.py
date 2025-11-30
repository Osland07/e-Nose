import os
import pandas as pd
import numpy as np
import random

# --- KONFIGURASI ---
BASE_DIR = "sample_data"

# DEFINISI PROFIL BAU (DATASET RAKSASA)
# Total 10.000 File (5000 Positif + 5000 Negatif)
CLASSES = {
    "Tidak Terdeteksi": {
        "base": 50,   "var": 20, "desc": "Udara Bersih/Sapi Murni"
    },
    "Terdeteksi Biomarker": {
        "base": 450,  "var": 100, "desc": "Terkontaminasi Babi"
    }
}

SENSORS = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM', 'Temp', 'Hum', 'Pres']

print("--- GENERATOR DATA MENTAH (BIG DATA - 10.000 SAMPEL) ---")

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

for label, config in CLASSES.items():
    # Buat Subfolder
    folder_path = os.path.join(BASE_DIR, label)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # FIX: Loop manual 5000 kali
    TARGET_COUNT = 5000
    print(f"📂 Membuat {TARGET_COUNT} file di folder: {label}...") 
    
    for i in range(TARGET_COUNT):
        rows = []
        for _ in range(15): # 15 detik data
            row = {}
            base_val = config['base']
            variance = config['var']
            
            # Sensor Gas
            for s in SENSORS[:8]: 
                noise = random.uniform(-variance, variance)
                
                # Karakteristik Khas Biomarker (MQ135 & QCM Naik Signifikan)
                if label == "Terdeteksi Biomarker" and s in ['MQ135', 'QCM']:
                    val = base_val * 1.5 + noise # Lebih tinggi lagi
                else:
                    val = base_val + noise
                
                row[s] = max(10, val)
            
            # Lingkungan
            row['Temp'] = 28.5 + random.uniform(-1, 1)
            row['Hum'] = 60.0 + random.uniform(-5, 5)
            row['Pres'] = 1005.0 + random.uniform(-2, 2)
            
            rows.append(row)
        
        # Simpan CSV
        df = pd.DataFrame(rows)
        filename = f"sample_{i+1:05d}.csv" # 00001.csv
        filepath = os.path.join(folder_path, filename)
        df.to_csv(filepath, sep=';', decimal=',', index=False)
        
        # Progress bar sederhana di terminal
        if (i+1) % 500 == 0:
            print(f"   ... {i+1} file selesai.")

print("\n✅ SELESAI! 10.000 File CSV siap.")
print("👉 Proses Training nanti akan butuh waktu agak lama (1-3 menit).")
