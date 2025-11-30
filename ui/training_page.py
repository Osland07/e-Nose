from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QCheckBox, QProgressBar, QTextEdit, QGroupBox, QFileDialog, 
    QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os
import sys

# Worker Thread agar aplikasi tidak macet saat training berat
class TrainingWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    progress_signal = pyqtSignal(int)

    def __init__(self, selected_models, data_path):
        super().__init__()
        self.selected_models = selected_models
        self.data_path = data_path

    def run(self):
        # Import di dalam thread agar GUI muncul duluan
        try:
            self.log_signal.emit("🚀 Memulai Training Center...")
            self.log_signal.emit(f"📂 Folder Data: {self.data_path}")
            
            # Import Library Berat
            import pandas as pd
            import numpy as np
            import joblib
            import glob
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler, LabelEncoder
            from sklearn.metrics import accuracy_score
            from ml.feature_extractor import extract_features
            
            # Import Model-Model
            from sklearn.svm import SVC
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier, ExtraTreesClassifier
            from sklearn.neighbors import KNeighborsClassifier
            from sklearn.naive_bayes import GaussianNB
            from sklearn.neural_network import MLPClassifier
            import xgboost as xgb
            
            # --- 1. LOAD DATA (AUTO-DETECT LABELS) ---
            self.log_signal.emit("\n📊 Membaca Data CSV...")
            
            all_features = []
            all_labels = []
            
            # Scan subfolder di dalam data_path
            if not os.path.exists(self.data_path):
                self.finished_signal.emit(False, f"Folder data tidak ditemukan: {self.data_path}")
                return

            subfolders = [f.path for f in os.scandir(self.data_path) if f.is_dir()]
            
            if not subfolders:
                self.log_signal.emit("⚠ Tidak ada subfolder (kelas) ditemukan di dalam sample_data.")
                self.log_signal.emit("ℹ Struktur yang benar:\n   sample_data/\n     ├── Kelas A/ (isi file csv)\n     └── Kelas B/ (isi file csv)")
                self.finished_signal.emit(False, "Struktur folder salah.")
                return

            self.log_signal.emit(f"🔎 Ditemukan {len(subfolders)} Kelas:")
            
            for folder_path in subfolders:
                label_name = os.path.basename(folder_path) # Nama folder jadi Label
                csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
                
                self.log_signal.emit(f"   📂 {label_name}: {len(csv_files)} file")
                
                if not csv_files:
                    continue

                for fpath in csv_files:
                    try:
                        df = pd.read_csv(fpath, sep=';', decimal=',')
                        # Cek validitas data (min 8 kolom)
                        if df.shape[1] < 8:
                            continue
                            
                        feats = extract_features(df)
                        all_features.append(feats)
                        all_labels.append(label_name) # Gunakan nama folder sebagai label
                    except: pass
            
            if not all_features:
                self.finished_signal.emit(False, "Tidak ada data valid (CSV) yang berhasil dibaca!")
                return
            
            self.log_signal.emit(f"\n✅ Total Data Latih: {len(all_features)} Sampel")

            # --- 2. PREPROCESSING ---
            self.log_signal.emit("\n⚙️ Preprocessing Data...")
            X_df = pd.DataFrame(all_features).fillna(0)
            le = LabelEncoder()
            y = le.fit_transform(all_labels)
            
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_df)
            feature_columns = X_df.columns.tolist()
            
            X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
            
            # --- 3. TRAINING LOOP ---
            MODEL_DIR = "model"
            if not os.path.exists(MODEL_DIR): os.makedirs(MODEL_DIR)
            
            total_models = len(self.selected_models)
            for idx, model_key in enumerate(self.selected_models):
                self.log_signal.emit(f"\n🔥 Melatih Model ({idx+1}/{total_models}): {model_key}...")
                
                clf = None
                name = f"{model_key}.joblib"
                
                # Factory Model
                if model_key == "SVM (RBF)": clf = SVC(kernel='rbf', probability=True)
                elif model_key == "SVM (Linear)": clf = SVC(kernel='linear', probability=True)
                elif model_key == "Random Forest": clf = RandomForestClassifier(n_estimators=100)
                elif model_key == "Extra Trees": clf = ExtraTreesClassifier(n_estimators=100)
                elif model_key == "Gradient Boosting": clf = GradientBoostingClassifier()
                elif model_key == "AdaBoost": clf = AdaBoostClassifier()
                elif model_key == "XGBoost": clf = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
                elif model_key == "KNN": clf = KNeighborsClassifier(n_neighbors=5)
                elif model_key == "Naive Bayes": clf = GaussianNB()
                elif model_key == "Neural Net (MLP)": clf = MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500)
                elif model_key == "Deep Neural Net (DNN)": clf = MLPClassifier(hidden_layer_sizes=(128, 64, 32), max_iter=1000) # Simulasi DNN pakai MLP dalam
                
                if clf:
                    clf.fit(X_train, y_train)
                    
                    # Test Akurasi
                    acc = accuracy_score(y_test, clf.predict(X_test)) * 100
                    self.log_signal.emit(f"   ✅ Akurasi: {acc:.2f}%")
                    
                    # Simpan
                    payload = {'model': clf, 'scaler': scaler, 'columns': feature_columns}
                    joblib.dump(payload, os.path.join(MODEL_DIR, name))
                
                # Update Progress
                progress = int((idx + 1) / total_models * 100)
                self.progress_signal.emit(progress)

            self.finished_signal.emit(True, "Semua model berhasil dilatih!")
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.log_signal.emit(f"❌ TERJADI ERROR:\n{error_msg}") # Kirim sinyal, jangan akses GUI langsung
            self.finished_signal.emit(False, str(e))


class TrainingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.data_path = os.path.join(os.getcwd(), "sample_data")
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        title = QLabel("Training Center (AI Factory)")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E3A8A;")
        layout.addWidget(title)
        
        # --- Settings Area ---
        settings_group = QGroupBox("Konfigurasi Training")
        settings_layout = QVBoxLayout(settings_group)
        
        # Folder Selection
        path_layout = QHBoxLayout()
        self.path_input = QLabel(self.data_path)
        self.path_input.setStyleSheet("border: 1px solid #ccc; padding: 5px; background: white;")
        btn_browse = QPushButton("📂 Pilih Folder Data")
        btn_browse.clicked.connect(self.browse_folder)
        path_layout.addWidget(QLabel("Sumber Data:"))
        path_layout.addWidget(self.path_input, 1)
        path_layout.addWidget(btn_browse)
        settings_layout.addLayout(path_layout)
        
        # Model Selection Grid
        self.model_checkboxes = {}
        grid_frame = QFrame()
        grid_layout = QHBoxLayout(grid_frame)
        
        # Kolom 1: Klasik
        col1 = QVBoxLayout()
        col1.addWidget(QLabel("<b>Klasik & Stabil</b>"))
        self.add_check("SVM (RBF)", col1, True)
        self.add_check("Random Forest", col1, True)
        self.add_check("KNN", col1, True)
        self.add_check("Naive Bayes", col1)
        col1.addStretch()
        
        # Kolom 2: Ensemble
        col2 = QVBoxLayout()
        col2.addWidget(QLabel("<b>Ensemble (Kuat)</b>"))
        self.add_check("XGBoost", col2, True)
        self.add_check("Gradient Boosting", col2)
        self.add_check("Extra Trees", col2)
        self.add_check("AdaBoost", col2)
        col2.addStretch()
        
        # Kolom 3: Deep Learning
        col3 = QVBoxLayout()
        col3.addWidget(QLabel("<b>Deep Learning</b>"))
        self.add_check("Neural Net (MLP)", col3, True)
        self.add_check("Deep Neural Net (DNN)", col3)
        col3.addStretch()
        
        grid_layout.addLayout(col1)
        grid_layout.addLayout(col2)
        grid_layout.addLayout(col3)
        settings_layout.addWidget(grid_frame)
        
        # Peringatan Berat
        self.lbl_warning = QLabel("⚠ PERHATIAN: Model Deep Learning butuh waktu training lama & CPU Tinggi!")
        self.lbl_warning.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 12px; background-color: #FEF2F2; padding: 5px; border-radius: 4px;")
        self.lbl_warning.hide() # Sembunyikan dulu
        settings_layout.addWidget(self.lbl_warning)
        
        layout.addWidget(settings_group)
        
        # --- Action Area ---
        btn_layout = QHBoxLayout()
        self.btn_train = QPushButton("🚀 MULAI TRAINING (Bangun Model)")
        self.btn_train.setFixedHeight(50)
        self.btn_train.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; font-size: 14px;")
        self.btn_train.clicked.connect(self.start_training)
        
        btn_layout.addWidget(self.btn_train)
        layout.addLayout(btn_layout)
        
        # --- Progress & Log ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("background-color: #1E293B; color: #38BDF8; font-family: Consolas;")
        layout.addWidget(self.log_console)

    def add_check(self, name, layout, checked=False):
        chk = QCheckBox(name)
        chk.setChecked(checked)
        chk.stateChanged.connect(self.check_heavy_models) # Cek setiap kali diklik
        layout.addWidget(chk)
        self.model_checkboxes[name] = chk

    def check_heavy_models(self):
        # Daftar model berat
        heavy_list = ["Deep Neural Net (DNN)", "XGBoost", "Gradient Boosting"]
        is_heavy = any(self.model_checkboxes[m].isChecked() for m in heavy_list if m in self.model_checkboxes)
        
        if is_heavy:
            self.lbl_warning.show()
        else:
            self.lbl_warning.hide()

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Data")
        if folder:
            self.data_path = folder
            self.path_input.setText(folder)

    def start_training(self):
        selected = [name for name, chk in self.model_checkboxes.items() if chk.isChecked()]
        
        if not selected:
            QMessageBox.warning(self, "Peringatan", "Pilih minimal 1 model untuk dilatih!")
            return
            
        self.btn_train.setEnabled(False)
        self.log_console.clear()
        self.progress_bar.setValue(0)
        
        # Start Thread
        self.worker = TrainingWorker(selected, self.data_path)
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.on_training_finished)
        self.worker.start()

    def append_log(self, text):
        self.log_console.append(text)

    def on_training_finished(self, success, msg):
        self.btn_train.setEnabled(True)
        if success:
            QMessageBox.information(self, "Sukses", msg)
        else:
            QMessageBox.critical(self, "Error", f"Training Gagal:\n{msg}")
