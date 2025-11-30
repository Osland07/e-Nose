import joblib
import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QLabel, 
    QPushButton, 
    QComboBox, 
    QGroupBox,
    QFileDialog,
    QMessageBox,
    QHBoxLayout,
    QFrame,
    QDialog # <-- Tambahkan ini
)
from PyQt6.QtCore import pyqtSignal, QObject, QThread, Qt
from ml.predictor import Predictor

class ModelLoader(QObject):
    """Worker for loading the model in a separate thread."""
    finished = pyqtSignal(object)

    def __init__(self, model_path):
        super().__init__()
        self.model_path = model_path

    def run(self):
        try:
            payload = joblib.load(self.model_path)
            self.finished.emit(payload)
        except Exception as e:
            print(f"Error loading model in worker thread: {e}")
            self.finished.emit(None)


class VotingConfigDialog(QDialog):
    def __init__(self, available_models, current_selection, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Konfigurasi Tim Voting (Ensemble)")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Pilih model yang akan ikut serta dalam voting:"))
        
        self.checks = {}
        
        # Scroll Area jika modelnya banyak
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        for model in available_models:
            chk = QCheckBox(model)
            # Default checked jika list kosong (pertama kali) atau ada di list
            if not current_selection or model in current_selection:
                chk.setChecked(True)
            content_layout.addWidget(chk)
            self.checks[model] = chk
            
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Tombol Aksi
        btn_layout = QHBoxLayout()
        btn_all = QPushButton("Pilih Semua")
        btn_none = QPushButton("Hapus Semua")
        btn_all.clicked.connect(self.select_all)
        btn_none.clicked.connect(self.select_none)
        
        btn_layout.addWidget(btn_all)
        btn_layout.addWidget(btn_none)
        layout.addLayout(btn_layout)
        
        btn_save = QPushButton("Simpan Konfigurasi")
        btn_save.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 8px;")
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save)

    def select_all(self):
        for chk in self.checks.values(): chk.setChecked(True)
        
    def select_none(self):
        for chk in self.checks.values(): chk.setChecked(False)
        
    def get_selected(self):
        return [name for name, chk in self.checks.items() if chk.isChecked()]


class ModelControlWidget(QWidget):
    model_loaded = pyqtSignal(bool)

    def __init__(self, predictor, parent=None):
        super().__init__(parent)
        self.predictor = predictor
        self.thread = None
        self.worker = None
        self.voting_whitelist = [] # Daftar model yang boleh ikut voting

        # --- UI Setup (Minimalist Style) ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(8)
        
        # Header Label
        lbl_header = QLabel("🤖 Model Deteksi (AI)")
        lbl_header.setStyleSheet("font-weight: bold; color: #475569; font-size: 12px;")
        layout.addWidget(lbl_header)
        
        # Container Row (Dropdown + Upload)
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        self.model_selector = QComboBox()
        self.model_selector.setMinimumHeight(30)
        self.model_selector.setStyleSheet("""
            QComboBox { padding: 2px 10px; border: 1px solid #CBD5E1; border-radius: 6px; background-color: white; color: #334155; }
            QComboBox::drop-down { border: 0px; }
        """)
        
        self.upload_button = QPushButton("📂")
        self.upload_button.setToolTip("Upload model baru")
        self.upload_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_button.setFixedSize(30, 30)
        self.upload_button.setStyleSheet("QPushButton { background-color: white; border: 1px solid #CBD5E1; border-radius: 6px; } QPushButton:hover { background-color: #F1F5F9; }")

        row_layout.addWidget(self.model_selector, 1)
        row_layout.addWidget(self.upload_button)
        layout.addLayout(row_layout)
        
        # Tombol Config Voting
        self.btn_voting_config = QPushButton("⚙️ Atur Tim Voting")
        self.btn_voting_config.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_voting_config.setStyleSheet("background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; border-radius: 6px; padding: 5px; font-weight: bold; font-size: 11px;")
        self.btn_voting_config.clicked.connect(self.open_voting_config)
        layout.addWidget(self.btn_voting_config)
        
        # Status Label
        self.model_status_label = QLabel("Status: Menunggu...")
        self.model_status_label.setStyleSheet("font-size: 10px; color: #94A3B8; margin-left: 2px;")
        layout.addWidget(self.model_status_label)

        # --- Signal Connections ---
        self.upload_button.clicked.connect(self.upload_new_model)
        self.model_selector.currentIndexChanged.connect(self.start_model_loading)
        
        # --- Initial State ---
        self.populate_model_selector()

    def open_voting_config(self):
        all_models = self.predictor.get_available_models()
        if not all_models:
            QMessageBox.warning(self, "Info", "Belum ada model tersedia. Silakan Training dulu.")
            return
            
        dlg = VotingConfigDialog(all_models, self.voting_whitelist, self)
        if dlg.exec():
            self.voting_whitelist = dlg.get_selected()
            count = len(self.voting_whitelist)
            self.btn_voting_config.setText(f"⚙️ Tim Voting: {count} Model")
            
    def get_voting_whitelist(self):
        return self.voting_whitelist

    def upload_new_model(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Pilih File Model", "", "Joblib Files (*.joblib)")
        if fileName:
            try:
                model_dir = "model"
                if not os.path.exists(model_dir):
                    os.makedirs(model_dir)
                dest_path = os.path.join(model_dir, os.path.basename(fileName))
                shutil.copy(fileName, dest_path)
                self.populate_model_selector()
                self.model_selector.setCurrentText(os.path.basename(fileName))
                
                QMessageBox.information(self, "Sukses", f"Model '{os.path.basename(fileName)}' berhasil ditambahkan!")
                
            except Exception as e:
                self.show_error_message("Upload Gagal", f"Terjadi kesalahan saat menyalin file model: {e}")

    def populate_model_selector(self):
        self.model_selector.blockSignals(True)
        self.model_selector.clear()
        models = self.predictor.get_available_models()
        if models:
            self.model_selector.addItems(models)
            self.start_model_loading()
        else:
            self.model_selector.addItem("Tidak ada model")
            self.model_status_label.setText("Status: Silakan upload model.")
            self.model_loaded.emit(False)
        self.model_selector.blockSignals(False)

    def start_model_loading(self):
        selected_model_file = self.model_selector.currentText()
        if selected_model_file in ["Tidak ada model", ""]:
            self.model_status_label.setText("Status: Pilih model.")
            self.model_loaded.emit(False)
            return
        
        self.set_loading_state(True)
        model_path = os.path.join(self.predictor.MODEL_DIR, selected_model_file)
        
        self.thread = QThread()
        self.worker = ModelLoader(model_path)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_load_finished)
        
        self.thread.start()

    def on_load_finished(self, payload):
        selected_model_file = self.model_selector.currentText()
        
        if payload and self.predictor.load_model_from_payload(payload):
            self.predictor.loaded_model_name = selected_model_file
            
            # DETEKSI TIPE MODEL
            model_obj = payload.get('model')
            model_type = type(model_obj).__name__
            
            # Terjemahkan nama teknis ke bahasa manusia
            if "SVC" in model_type: readable_type = "SVM (Support Vector Machine)"
            elif "RandomForest" in model_type: readable_type = "Random Forest (Ensemble)"
            elif "KNeighbors" in model_type: readable_type = "KNN (K-Nearest Neighbor)"
            elif "MLP" in model_type: readable_type = "Neural Network (MLP)"
            else: readable_type = model_type # Fallback
            
            # Update Label Status dengan info lengkap
            self.model_status_label.setText(f"✅ Aktif: {selected_model_file}\n🧠 Algoritma: {readable_type}")
            self.model_status_label.setStyleSheet("font-size: 10px; color: #10B981; font-weight: bold;")
            self.model_loaded.emit(True)
        else:
            self.model_status_label.setText(f"❌ Error: {selected_model_file}")
            self.model_status_label.setStyleSheet("font-size: 10px; color: #EF4444;")
            self.model_loaded.emit(False)
            self.show_error_message("Model tidak valid", "File model rusak/tidak kompatibel.")
        
        self.set_loading_state(False)

        if self.thread is not None:
            self.thread.quit()
            self.thread.wait()

    def set_loading_state(self, is_loading):
        self.model_selector.setEnabled(not is_loading)
        self.upload_button.setEnabled(not is_loading)
        if is_loading:
            self.model_status_label.setText("⏳ Memuat model...")
            self.model_status_label.setStyleSheet("font-size: 10px; color: #F59E0B;")
        
    def show_error_message(self, title, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(title)
        msg_box.setInformativeText(message)
        msg_box.setWindowTitle("Error")
        msg_box.exec()
