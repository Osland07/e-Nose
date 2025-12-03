from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QCheckBox, QProgressBar, QTextEdit, QGroupBox, QFileDialog, 
    QScrollArea, QFrame, QMessageBox, QDialog, QTableWidget, 
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSlider, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os
import sys
import random
import json
import pandas as pd
from PyQt6.QtGui import QColor
from ui.components.graph_widget import GraphWidget

# --- DIALOG UNTUK MAPPING LABEL ---
class LabelMappingDialog(QDialog):
    def __init__(self, folder_list, current_mapping, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Konfigurasi Label Training")
        self.resize(700, 500)
        self.folder_list = folder_list
        self.mapping = current_mapping
        self.final_mapping = {}
        
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #334155; }
            QTableWidget { 
                background-color: white; 
                border: 1px solid #E2E8F0; 
                gridline-color: #F1F5F9;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-weight: bold;
                color: #475569;
            }
            QLineEdit {
                padding: 5px; border: 1px solid #CBD5E1; border-radius: 4px;
            }
            QLineEdit:focus { border: 1px solid #3B82F6; }
        """)
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # HEADER AREA
        header_layout = QHBoxLayout()
        
        title_container = QWidget()
        title_vbox = QVBoxLayout(title_container)
        title_vbox.setContentsMargins(0,0,0,0)
        
        lbl_title = QLabel("🏷️ Pemetaan Label (Labelling)")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E3A8A;")
        
        lbl_desc = QLabel(
            "Sistem membaca nama folder sebagai label otomatis. \n"
            "Ubah 'Label Target' untuk keperluan training. \n"
            "✅ AMAN: Nama folder asli di komputer TIDAK akan berubah."
        )
        lbl_desc.setStyleSheet("color: #64748B; font-size: 12px;")
        
        title_vbox.addWidget(lbl_title)
        title_vbox.addWidget(lbl_desc)
        
        header_layout.addWidget(title_container)
        layout.addLayout(header_layout)
        
        # TABLE AREA
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["📁 Folder Sumber (Asli)", "🏷️ Label Target (Hasil Output)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        
        self.table.setRowCount(len(self.folder_list))
        
        for i, folder in enumerate(self.folder_list):
            # Kolom 1: Nama Folder (Read Only, Bold)
            item_folder = QTableWidgetItem(folder)
            item_folder.setFlags(Qt.ItemFlag.ItemIsEnabled) # Read only
            item_folder.setForeground(QColor("#334155"))
            font = item_folder.font(); font.setBold(True); item_folder.setFont(font)
            self.table.setItem(i, 0, item_folder)
            
            # Kolom 2: Target Label (Editable)
            current_target = self.mapping.get(folder, folder) # Default sama dengan folder
            item_target = QTableWidgetItem(current_target)
            item_target.setForeground(QColor("#2563EB")) # Blue text for editable
            self.table.setItem(i, 1, item_target)
            
        layout.addWidget(self.table)
        
        # FOOTER BUTTONS
        btn_layout = QHBoxLayout()
        
        btn_reset = QPushButton("↺ Reset ke Default")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setStyleSheet("""
            QPushButton { background-color: white; border: 1px solid #CBD5E1; color: #64748B; padding: 8px 15px; border-radius: 6px; font-weight: bold;}
            QPushButton:hover { background-color: #F1F5F9; }
        """)
        btn_reset.clicked.connect(self.reset_mapping)
        
        btn_cancel = QPushButton("Batal")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("QPushButton { background-color: white; border: none; color: #64748B; font-weight: bold; } QPushButton:hover { color: #334155; }")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Simpan Perubahan")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { background-color: #2563EB; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        btn_save.clicked.connect(self.save_mapping)
        
        btn_layout.addWidget(btn_reset)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
        
    def reset_mapping(self):
        for i in range(self.table.rowCount()):
            folder_name = self.table.item(i, 0).text()
            self.table.item(i, 1).setText(folder_name)
        
    def save_mapping(self):
        new_map = {}
        for i in range(self.table.rowCount()):
            folder = self.table.item(i, 0).text()
            target = self.table.item(i, 1).text().strip()
            if not target: target = folder # Fallback
            new_map[folder] = target
        
        self.final_mapping = new_map
        self.accept()
        
    def get_mapping(self):
        return self.final_mapping

# Worker Thread agar aplikasi tidak macet saat training berat
class TrainingWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    progress_signal = pyqtSignal(int)

    def __init__(self, selected_models, data_path, active_sensors=None, label_mapping=None, test_size=0.2, random_state=42):
        super().__init__()
        self.selected_models = selected_models
        self.data_path = data_path
        self.active_sensors = active_sensors
        self.label_mapping = label_mapping if label_mapping else {}
        self.test_size = test_size
        self.random_state = random_state

    def run(self):
        try:
            self.log_signal.emit("🚀 Memulai Training Center...")
            self.log_signal.emit(f"📂 Folder Data: {self.data_path}")
            self.log_signal.emit(f"⚙️ Konfigurasi: Test Size={int(self.test_size*100)}%, Seed={self.random_state}")
            
            if self.active_sensors:
                 self.log_signal.emit(f"🔌 Sensor Aktif: {', '.join(self.active_sensors)}")
            
            # Import Library Berat
            import pandas as pd
            import numpy as np
            import joblib
            import glob
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler, LabelEncoder
            from sklearn.metrics import accuracy_score, precision_recall_fscore_support
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
            
            if not os.path.exists(self.data_path):
                self.finished_signal.emit(False, f"Folder data tidak ditemukan: {self.data_path}")
                return

            subfolders = [f.path for f in os.scandir(self.data_path) if f.is_dir()]
            if not subfolders:
                self.log_signal.emit("⚠ Tidak ada subfolder (kelas) ditemukan.")
                self.finished_signal.emit(False, "Struktur folder salah.")
                return

            self.log_signal.emit(f"🔎 Ditemukan {len(subfolders)} Kelas Label.")
            
            # Hitung total file dulu untuk progress bar
            total_files = sum([len(glob.glob(os.path.join(f, "*.csv"))) for f in subfolders])
            processed_files = 0
            first_file_checked = False # Flag untuk validasi sensor sekali saja
            
            for folder_path in subfolders:
                raw_label_name = os.path.basename(folder_path)
                
                # --- APLIKASI LABEL MAPPING (DINAMIS DARI USER) ---
                final_label_name = self.label_mapping.get(raw_label_name, raw_label_name)
                
                csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
                
                self.log_signal.emit(f"   📂 {raw_label_name} ➡ Label: '{final_label_name}' ({len(csv_files)} file)")
                
                if not csv_files: continue

                for fpath in csv_files:
                    try:
                        # Coba baca dengan Separator Titik Koma (;)
                        df = pd.read_csv(fpath, sep=';', decimal=',')
                        
                        # Jika gagal (kolom nyatu), coba Separator Koma (,)
                        if df.shape[1] < 3:
                             df_comma = pd.read_csv(fpath, sep=',', decimal='.')
                             if df_comma.shape[1] >= 3:
                                 df = df_comma
                        
                        if df.shape[1] < 3: continue # Masih gagal -> Skip
                        
                        # --- NORMALISASI HEADER (Handle 'MQ 3' vs 'MQ3') ---
                        # Hapus spasi dan uppercase agar cocok dengan checkbox
                        df.columns = df.columns.str.strip().str.upper().str.replace(' ', '')
                        
                        # --- VALIDASI SENSOR (Hanya Cek File Pertama) ---
                        if not first_file_checked and self.active_sensors:
                            # Cek headers di file CSV
                            file_sensors = df.columns.tolist()
                            missing_sensors = [s for s in self.active_sensors if s not in file_sensors]
                            
                            if missing_sensors:
                                # ERROR KRITIKAL: Sensor yang diminta tidak ada di file
                                err_msg = (
                                    f"❌ <b>VALIDASI DATASET GAGAL!</b><br><br>"
                                    f"Anda memilih sensor: <b>{', '.join(missing_sensors)}</b><br>"
                                    f"Tetapi sensor tersebut TIDAK ADA di dalam file dataset.<br><br>"
                                    f"Sensor yang tersedia di file: <br>{', '.join(file_sensors)}<br><br>"
                                    f"👉 <i>Silakan perbaiki dataset atau sesuaikan checklist sensor.</i>"
                                )
                                self.finished_signal.emit(False, err_msg)
                                return # STOP TRAINING
                            
                            first_file_checked = True # Lolos validasi
                            
                        feats = extract_features(df, active_sensors=self.active_sensors)
                        all_features.append(feats)
                        all_labels.append(final_label_name) # Pakai label yang sudah di-mapping
                    except Exception as e: 
                        pass
                    
                    # Update Progress Bar (0% - 50% adalah fase Loading Data)
                    processed_files += 1
                    if total_files > 0:
                        progress = int((processed_files / total_files) * 50) 
                        self.progress_signal.emit(progress)
            
            if not all_features:
                self.finished_signal.emit(False, "Tidak ada data valid (CSV) ditemukan!")
                return
            
            self.log_signal.emit(f"\n✅ Total Dataset: {len(all_features)} Sampel. Mulai Training...")

            # --- 2. PREPROCESSING ---
            X_df = pd.DataFrame(all_features).fillna(0)
            le = LabelEncoder()
            y = le.fit_transform(all_labels)
            
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_df)
            feature_columns = X_df.columns.tolist()
            
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, 
                test_size=self.test_size, 
                random_state=self.random_state, 
                stratify=y
            )
            
            # --- 3. TRAINING LOOP ---
            MODEL_DIR = "model"
            if not os.path.exists(MODEL_DIR): os.makedirs(MODEL_DIR)
            
            total_models = len(self.selected_models)
            
            for idx, model_key in enumerate(self.selected_models):
                self.log_signal.emit(f"\n🔥 Melatih Model ({idx+1}/{total_models}): {model_key}...")
                
                clf = None
                name = f"{model_key}.joblib"
                
                # Factory Model
                if model_key == "SVM" or model_key == "SVM (RBF)": clf = SVC(kernel='rbf', probability=True)
                elif model_key == "SVM (Linear)": clf = SVC(kernel='linear', probability=True)
                elif model_key == "Random Forest": clf = RandomForestClassifier(n_estimators=100)
                elif model_key == "Extra Trees": clf = ExtraTreesClassifier(n_estimators=100)
                elif model_key == "Gradient Boosting": clf = GradientBoostingClassifier()
                elif model_key == "AdaBoost": clf = AdaBoostClassifier()
                elif model_key == "XGBoost": clf = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
                elif model_key == "KNN": clf = KNeighborsClassifier(n_neighbors=5)
                elif model_key == "Naive Bayes": clf = GaussianNB()
                elif model_key == "Neural Net (MLP)": clf = MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500)
                elif model_key == "Deep Neural Net (DNN)": clf = MLPClassifier(hidden_layer_sizes=(128, 64, 32), max_iter=1000) 
                
                # FIX: Pengecekan yang benar untuk objek
                if clf is not None:
                    clf.fit(X_train, y_train)
                    
                    # EVALUASI LENGKAP (F1-Score, dll)
                    y_pred = clf.predict(X_test)
                    
                    # Hitung Metrik
                    acc = accuracy_score(y_test, y_pred) * 100
                    # Average='macro' cocok untuk multiclass (Sapi, Babi, Udara)
                    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)
                    
                    # Tampilkan Rapor di Log Console
                    self.log_signal.emit(f"   ✅ Akurasi   : {acc:.2f}%")
                    self.log_signal.emit(f"   🎯 Precision : {prec:.2f}")
                    self.log_signal.emit(f"   🔎 Recall    : {rec:.2f}")
                    self.log_signal.emit(f"   🏆 F1-Score  : {f1:.2f}")
                    
                    # Simpan Model BESERTA Nama Kelasnya (Penting!)
                    # Agar saat prediksi nanti tidak keluar angka 0/1 doang
                    target_names = list(le.classes_)
                    
                    payload = {
                        'model': clf, 
                        'scaler': scaler, 
                        'columns': feature_columns,
                        'target_names': target_names 
                    }
                    joblib.dump(payload, os.path.join(MODEL_DIR, name))
                
                # Update Progress (50% - 100% adalah fase Training)
                progress = 50 + int(((idx + 1) / total_models) * 50)
                self.progress_signal.emit(progress)

            self.finished_signal.emit(True, "Semua model berhasil dilatih!")
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.log_signal.emit(f"❌ TERJADI ERROR:\n{error_msg}")
            self.finished_signal.emit(False, str(e))


class TrainingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.data_path = os.path.join(os.getcwd(), "sample_data")
        self.worker = None
        self.model_checkboxes = {}
        self.sensor_checkboxes = {}
        self.label_mapping = {} # Mapping dinamis
        self.test_size = 0.2
        self.random_state = 42
        self._init_ui()

    def _init_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0,0,0,0)
        title_layout.setSpacing(0)
        
        title = QLabel("Training Center (AI Factory)")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #1E3A8A;")
        subtitle = QLabel("Latih model Machine Learning dengan data sensor Anda.")
        subtitle.setStyleSheet("font-size: 12px; color: #64748B; margin-top: 4px;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        
        # Tombol Preview (dipindahkan ke Header Kanan)
        btn_preview_random = QPushButton("🎲 Preview Sampel Acak")
        btn_preview_random.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_preview_random.clicked.connect(self.preview_random_sample)
        btn_preview_random.setStyleSheet("""
            QPushButton { background-color: white; color: #F59E0B; font-weight: bold; border: 1px solid #F59E0B; padding: 8px 15px; border-radius: 6px; }
            QPushButton:hover { background-color: #FFFBEB; }
        """)
        header_layout.addWidget(btn_preview_random)
        
        main_layout.addLayout(header_layout)

        # --- BODY CONTAINER (SPLIT LEFT & RIGHT) ---
        body_layout = QHBoxLayout()
        body_layout.setSpacing(20)

        # ==================================================
        # LEFT PANEL: CONFIGURATION & CONTROLS
        # ==================================================
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setStyleSheet("background: transparent;")
        
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(0, 0, 5, 0)
        left_layout.setSpacing(15)
        
        # 1. Data Source Group
        group_data = QGroupBox("Sumber Data")
        group_data.setStyleSheet("QGroupBox { font-weight: bold; color: #334155; border: 1px solid #CBD5E1; border-radius: 8px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        layout_data = QVBoxLayout(group_data)
        
        path_row = QHBoxLayout()
        self.path_input = QLabel(self.data_path)
        self.path_input.setStyleSheet("background: white; border: 1px solid #E2E8F0; border-radius: 4px; padding: 6px; color: #475569;")
        self.path_input.setWordWrap(True)
        
        btn_browse = QPushButton("📂")
        btn_browse.setToolTip("Pilih Folder")
        btn_browse.setFixedSize(35, 35)
        btn_browse.clicked.connect(self.browse_folder)
        
        path_row.addWidget(self.path_input, 1)
        path_row.addWidget(btn_browse)
        
        self.btn_mapping = QPushButton("🏷️ Atur Mapping Label")
        self.btn_mapping.clicked.connect(self.configure_labels)
        self.btn_mapping.setStyleSheet("background-color: #8B5CF6; color: white; font-weight: bold; border-radius: 6px; padding: 8px;")
        
        layout_data.addLayout(path_row)
        layout_data.addWidget(self.btn_mapping)
        left_layout.addWidget(group_data)
        
        # 2. Hyperparameters Group
        group_params = QGroupBox("Parameter Training")
        group_params.setStyleSheet(group_data.styleSheet())
        layout_params = QVBoxLayout(group_params)
        
        # Test Size
        self.lbl_test_size = QLabel(f"Rasio Testing: {int(self.test_size*100)}%")
        self.slider_test = QSlider(Qt.Orientation.Horizontal)
        self.slider_test.setRange(10, 50)
        self.slider_test.setValue(int(self.test_size*100))
        self.slider_test.valueChanged.connect(self.update_test_size)
        layout_params.addWidget(self.lbl_test_size)
        layout_params.addWidget(self.slider_test)
        
        # Seed
        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel("Random Seed:"))
        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(0, 9999)
        self.spin_seed.setValue(self.random_state)
        seed_row.addWidget(self.spin_seed)
        layout_params.addLayout(seed_row)
        
        left_layout.addWidget(group_params)

        # 3. Sensor Selection
        group_sensor = QGroupBox("Filter Sensor")
        group_sensor.setStyleSheet(group_data.styleSheet())
        layout_sensor = QHBoxLayout(group_sensor)
        layout_sensor.setSpacing(10)
        
        # Grid sensor 2 kolom
        sensor_grid = QFrame()
        sensor_grid_layout = QVBoxLayout(sensor_grid)
        sensor_grid_layout.setContentsMargins(0,0,0,0)
        
        all_sensors = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']
        # Bagi jadi 2 baris
        row1 = QHBoxLayout(); row2 = QHBoxLayout()
        
        for i, sensor in enumerate(all_sensors):
            chk = QCheckBox(sensor)
            chk.setChecked(True)
            self.sensor_checkboxes[sensor] = chk
            if i < 4: row1.addWidget(chk)
            else: row2.addWidget(chk)
            
        sensor_grid_layout.addLayout(row1)
        sensor_grid_layout.addLayout(row2)
        layout_sensor.addWidget(sensor_grid)
        left_layout.addWidget(group_sensor)

        # 4. Model Selection
        group_model = QGroupBox("Pilih Algoritma")
        group_model.setStyleSheet(group_data.styleSheet())
        layout_model = QVBoxLayout(group_model)
        
        col1 = QVBoxLayout(); col1.setSpacing(2)
        col1.addWidget(QLabel("<b>Klasik (Ringan)</b>"))
        self.add_check("SVM", col1, True)
        self.add_check("SVM (RBF)", col1)
        self.add_check("KNN", col1, True)
        self.add_check("Random Forest", col1, True)
        self.add_check("Naive Bayes", col1)
        
        col2 = QVBoxLayout(); col2.setSpacing(2)
        col2.addWidget(QLabel("<b>Modern (Berat)</b>"))
        self.add_check("XGBoost", col2, True)
        self.add_check("Gradient Boosting", col2)
        self.add_check("Extra Trees", col2)
        self.add_check("Neural Net (MLP)", col2, True)
        self.add_check("Deep Neural Net (DNN)", col2)

        model_layout_h = QHBoxLayout()
        model_layout_h.addLayout(col1)
        model_layout_h.addSpacing(15)
        model_layout_h.addLayout(col2)
        layout_model.addLayout(model_layout_h)
        
        self.lbl_warning = QLabel("⚠ Peringatan: Model 'Berat' membutuhkan waktu training lama.")
        self.lbl_warning.setStyleSheet("color: #D97706; font-size: 11px; background: #FFFBEB; padding: 4px; border-radius: 4px;")
        self.lbl_warning.hide()
        layout_model.addWidget(self.lbl_warning)
        
        left_layout.addWidget(group_model)
        
        # Start Button
        self.btn_train = QPushButton("🚀 MULAI TRAINING")
        self.btn_train.setFixedHeight(45)
        self.btn_train.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_train.setStyleSheet("""
            QPushButton { background-color: #2563EB; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:disabled { background-color: #94A3B8; }
        """)
        self.btn_train.clicked.connect(self.start_training)
        left_layout.addSpacing(10)
        left_layout.addWidget(self.btn_train)
        left_layout.addStretch() # Dorong ke atas

        left_scroll.setWidget(left_content)
        
        # ==================================================
        # RIGHT PANEL: VISUALIZATION & LOGS
        # ==================================================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        # 1. Graph Preview
        self.graph_preview = GraphWidget()
        # Grafik ambil 40% tinggi kanan
        # Kita bungkus di groupbox biar rapi
        graph_group = QGroupBox("Data Preview")
        graph_group.setStyleSheet(group_data.styleSheet())
        graph_layout = QVBoxLayout(graph_group)
        graph_layout.setContentsMargins(2, 10, 2, 2)
        graph_layout.addWidget(self.graph_preview)
        
        right_layout.addWidget(graph_group, stretch=4)

        # 2. Progress & Logs
        log_group = QGroupBox("Log Aktivitas")
        log_group.setStyleSheet(group_data.styleSheet())
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(2, 10, 2, 2)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #10B981; border-radius: 2px; }")
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("""
            QTextEdit {
                background-color: #1E293B; 
                color: #38BDF8; 
                font-family: Consolas; 
                font-size: 12px;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        log_layout.addWidget(self.progress_bar)
        log_layout.addWidget(self.log_console)
        
        right_layout.addWidget(log_group, stretch=6)

        # Add to Body
        body_layout.addWidget(left_scroll, stretch=35) # 35% Width
        body_layout.addWidget(right_panel, stretch=65) # 65% Width

        main_layout.addLayout(body_layout)

    def update_test_size(self):
        val = self.slider_test.value()
        self.test_size = val / 100.0
        self.lbl_test_size.setText(f"Rasio Testing: {val}%")

    def add_check(self, name, layout, checked=False):
        chk = QCheckBox(name)
        chk.setChecked(checked)
        chk.stateChanged.connect(self.check_heavy_models)
        layout.addWidget(chk)
        self.model_checkboxes[name] = chk

    def check_heavy_models(self):
        heavy_list = ["Deep Neural Net (DNN)", "XGBoost", "Gradient Boosting"]
        is_heavy = any(self.model_checkboxes[m].isChecked() for m in heavy_list if m in self.model_checkboxes)
        
        if is_heavy:
            self.lbl_warning.show()
        else:
            self.lbl_warning.hide()

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Data")
        if folder:
            # Cek apakah folder berubah
            if self.data_path != folder:
                self.data_path = folder
                self.path_input.setText(folder)
                
                # COBA LOAD MAPPING DARI FILE JSON
                json_path = os.path.join(self.data_path, "label_map.json")
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r') as f:
                            self.label_mapping = json.load(f)
                        self.log_console.append(f"📂 Konfigurasi label dimuat dari: {json_path}")
                    except Exception as e:
                        self.log_console.append(f"⚠ Gagal memuat label_map.json: {e}")
                        self.label_mapping = {}
                else:
                    self.label_mapping = {} # Reset jika folder baru & tidak ada config
            
            # Update UI
            self.update_mapping_button_status()
            self.preview_random_sample()

    def update_mapping_button_status(self):
        # Cari tombol mapping (kita simpan referensi dulu atau cari lewat children)
        # Cara mudah: Kita simpan referensi tombol di __init__ nanti.
        # Untuk sekarang, kita cari manual di layout atau simpan di self.btn_mapping
        if hasattr(self, 'btn_mapping'):
            count = len(self.label_mapping)
            if count > 0:
                self.btn_mapping.setText(f"🏷️ Label Configured ({count})")
                self.btn_mapping.setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
            else:
                self.btn_mapping.setText("🏷️ Atur Mapping Label")
                self.btn_mapping.setStyleSheet("background-color: #8B5CF6; color: white; font-weight: bold;")

    def preview_random_sample(self):
        """Mengambil 1 file CSV acak dari data_path dan menampilkannya di grafik."""
        if not os.path.exists(self.data_path):
            return

        # Kumpulkan semua file CSV
        all_csvs = []
        for root, dirs, files in os.walk(self.data_path):
            for f in files:
                if f.lower().endswith('.csv'):
                    all_csvs.append(os.path.join(root, f))

        if not all_csvs:
            self.log_console.append("⚠ Tidak ada file CSV untuk dipreview.")
            return

        # Pilih 1 acak
        chosen_file = random.choice(all_csvs)
        
        try:
            # Baca CSV
            df = pd.read_csv(chosen_file, sep=';', decimal=',')
            if df.shape[1] < 3: 
                df = pd.read_csv(chosen_file, sep=',', decimal='.')
            
            # Normalisasi Kolom
            df.columns = df.columns.str.strip().str.upper().str.replace(' ', '')
            
            # Ambil data 8 sensor standar (jika ada)
            sensors = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']
            graph_data = []
            
            # Kita ambil RATA-RATA dari setiap sensor untuk ditampilkan di grafik (sebagai 1 titik per sensor)
            # ATAU jika ingin time-series, kita harus ambil row-by-row.
            # GraphWidget kita didesain untuk update per-tick.
            # Untuk preview statis CSV (biasanya data E-Nose CSV adalah rekaman waktu), kita bisa ambil mean-nya
            # atau menampilkan snapshot terakhir.
            
            # STRATEGI: Tampilkan Mean Value dari setiap sensor dalam bentuk Bar/Line
            for s in sensors:
                if s in df.columns:
                    val = df[s].mean() # Ambil rata-rata sinyal sensor tsb
                else:
                    val = 0.0
                graph_data.append(val)
            
            # Update Grafik
            self.graph_preview.reset() # Bersihkan dulu
            self.graph_preview.update_plot(graph_data) # Kirim data
            
            # Tampilkan info di log
            folder_name = os.path.basename(os.path.dirname(chosen_file))
            # Terjemahkan folder ke label (jika ada di mapping)
            final_label = self.label_mapping.get(folder_name, folder_name)
            
            self.log_console.append(f"👁 Preview: {os.path.basename(chosen_file)}\n   📂 Asli: {folder_name} ➡ 🏷️ Label: {final_label}")
            
        except Exception as e:
            self.log_console.append(f"❌ Gagal preview {os.path.basename(chosen_file)}: {str(e)}")

    def configure_labels(self):
        if not os.path.exists(self.data_path):
            QMessageBox.warning(self, "Error", "Folder data belum dipilih!")
            return

        # Scan subfolder
        subfolders = [f.name for f in os.scandir(self.data_path) if f.is_dir()]
        if not subfolders:
             QMessageBox.warning(self, "Kosong", "Tidak ada folder data ditemukan di lokasi ini.")
             return
             
        # Dialog
        dlg = LabelMappingDialog(subfolders, self.label_mapping, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.label_mapping = dlg.get_mapping()
            
            # SIMPAN KE JSON AGAR PERMANEN
            try:
                json_path = os.path.join(self.data_path, "label_map.json")
                with open(json_path, 'w') as f:
                    json.dump(self.label_mapping, f, indent=4)
                
                self.log_console.append(f"✅ Konfigurasi label disimpan ke: {json_path}")
                QMessageBox.information(self, "Sukses", "Konfigurasi Label berhasil disimpan dan akan dimuat otomatis nanti.")
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Gagal menyimpan file konfigurasi permanen: {e}")
            
            self.update_mapping_button_status()

    def start_training(self):
        selected_models = [name for name, chk in self.model_checkboxes.items() if chk.isChecked()]
        active_sensors = [name for name, chk in self.sensor_checkboxes.items() if chk.isChecked()]
        
        if not selected_models:
            QMessageBox.warning(self, "Peringatan", "Pilih minimal 1 model untuk dilatih!")
            return
            
        if not active_sensors:
             QMessageBox.warning(self, "Peringatan", "Pilih minimal 1 sensor!")
             return

        self.btn_train.setEnabled(False)
        self.log_console.clear()
        self.progress_bar.setValue(0)
        
        # Start Thread
        self.worker = TrainingWorker(
            selected_models, 
            self.data_path, 
            active_sensors=active_sensors, 
            label_mapping=self.label_mapping,
            test_size=self.test_size,
            random_state=self.spin_seed.value()
        )
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