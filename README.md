# 👃 E-Nose AI Dashboard (Pro Version)

Sistem Deteksi Daging Babi/Sapi berbasis Electronic Nose (E-Nose) dengan Integrasi Multi-Model Artificial Intelligence.

---

## 🌟 Fitur Utama

1.  **Multi-Model AI Engine:**
    *   Mendukung **10+ Algoritma** sekaligus (SVM, Random Forest, XGBoost, Neural Net, KNN, dll).
    *   **Voting System:** Keputusan diambil berdasarkan suara terbanyak dari berbagai model.
    *   **Deep Learning Ready:** Mendukung MLP dan Deep Neural Network.

2.  **Training Center (GUI):**
    *   Tidak perlu koding! Cukup klik-klik di menu "Training Center".
    *   Pilih folder data, centang model yang diinginkan, lalu "Mulai Training".
    *   Live Log Console untuk memantau proses belajar AI.

3.  **Real-Time Monitoring:**
    *   Grafik sensor yang responsif dengan mode **Line / Area**.
    *   Indikator Suhu, Kelembaban, dan Tekanan Udara.
    *   Mode **Simulasi (Tanpa Alat)** untuk keperluan demo/presentasi.

4.  **Data Management:**
    *   Penyimpanan otomatis ke Database SQLite.
    *   **Export to Excel (.xlsx)** untuk keperluan laporan/skripsi.
    *   Pencarian dan Filter riwayat deteksi.

---

## 🛠️ Teknologi

*   **Bahasa:** Python 3.11
*   **GUI:** PyQt6 (Modern Theme)
*   **AI/ML:** Scikit-Learn, XGBoost, TensorFlow
*   **Data:** Pandas, NumPy, OpenPyXL
*   **Hardware:** Arduino (via Serial USB)

---

## 🚀 Cara Menggunakan

### A. Persiapan Awal
1.  Pastikan library terinstal:
    ```bash
    pip install -r requirements.txt
    pip install tensorflow xgboost pyqtdarktheme
    ```
2.  Jalankan aplikasi:
    *   Double klik `KLIK_SAYA_UNTUK_MULAI.bat`, ATAU
    *   Lewat terminal: `.venv\Scripts\python.exe main.py`

### B. Melatih Model (Training)
1.  Masuk ke Tab **"⚙️ TRAINING CENTER"**.
2.  Pilih folder data (pastikan berisi file `.csv` di folder `Sapi` dan `Babi`).
3.  Centang model yang ingin dilatih (Saran: SVM, Random Forest, XGBoost, Neural Net).
4.  Klik **"MULAI TRAINING"**.
5.  Tunggu hingga muncul pesan "Sukses".

### C. Melakukan Deteksi
1.  Masuk ke Tab **"📊 DASHBOARD UTAMA"**.
2.  **Koneksi Alat:**
    *   Jika ada alat: Colokkan USB, tunggu status "Terhubung".
    *   Jika tanpa alat: Centang **"Mode Simulasi"** di panel kanan.
3.  **Pilih Model:** Di panel kanan, pilih model AI yang baru dilatih.
4.  Klik **"MULAI DETEKSI"**.
5.  Tunggu durasi habis (default 15 detik).
6.  Hasil akan muncul di layar.

### D. Export Data
1.  Masuk ke Tab **"📂 RIWAYAT DATA"**.
2.  Filter data jika perlu.
3.  Klik **"Export All to Excel"**.

---

## 📂 Struktur Data CSV (Raw Data)
Jika ingin menggunakan data latih sendiri, pastikan format CSV-nya:
*   Pemisah: Titik koma (`;`)
*   Desimal: Koma (`,`) atau Titik (`.`)
*   Kolom Wajib: `MQ2;MQ3;MQ4;MQ6;MQ7;MQ8;MQ135;QCM`

---

## 🐛 Troubleshooting
*   **Error "Invalid Data Format":** Pastikan jumlah kolom data sensor sesuai (8 Sensor Gas).
*   **Aplikasi tidak muncul:** Coba jalankan lewat terminal untuk melihat pesan error.
*   **Grafik diam:** Pastikan port USB benar atau Mode Simulasi aktif.

---
**© 2025 E-Nose Research Team**
