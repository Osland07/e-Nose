import os
import pandas as pd
import numpy as np
import random

# --- KONFIGURASI ---
BASE_DIR = "sample_data"
CLASSES = {
    "Terdeteksi Biomarker": {"base_val": 800, "count": 500}, # Nilai Tinggi (Banyakin jadi 500)
    "Tidak Terdeteksi":     {"base_val": 30,  "count": 500}  # Nilai Rendah (Banyakin jadi 500)
}
SENSORS = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM', 'Temp', 'Hum', 'Pres']

print("--- GENERATOR DATA MENTAH (RAW CSV) ---")

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

for label, config in CLASSES.items():
    # Buat Subfolder
    folder_path = os.path.join(BASE_DIR, label)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    print(f"📂 Membuat {config['count']} file di folder: {label}...")
    
    for i in range(config['count']):
        # Generate Data Palsu (Misal 10 detik perekaman per file)
        rows = []
        for _ in range(10): # 10 baris data per file
            row = {}
            base = config['base_val']
            
            # Sensor Gas (MQ & QCM)
            for s in SENSORS[:8]: 
                # Variasi: MQ135 dan QCM paling sensitif
                if s in ['MQ135', 'QCM'] and label == "Terdeteksi Biomarker":
                    val = base + random.uniform(50, 150)
                else:
                    val = base + random.uniform(-10, 10)
                
                # Pastikan tidak negatif
                row[s] = max(0, val)
            
            # Lingkungan (Temp, Hum, Pres)
            row['Temp'] = 28.5 + random.uniform(-0.5, 0.5)
            row['Hum'] = 60.0 + random.uniform(-2, 2)
            row['Pres'] = 1005.0 + random.uniform(-1, 1)
            
            rows.append(row)
        
        # Buat DataFrame
        df = pd.DataFrame(rows)
        
        # Simpan ke CSV (Format Excel Indo: sep=; decimal=,)
        filename = f"sample_{i+1:03d}.csv"
        filepath = os.path.join(folder_path, filename)
        
        # Trik simpan format Indo
        df.to_csv(filepath, sep=';', decimal=',', index=False)

print("\n✅ SELESAI! Folder 'sample_data' sudah terisi.")
print("👉 Sekarang Anda bisa mencoba menu 'Training Center' di aplikasi.")
