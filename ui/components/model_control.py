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
    QFrame
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


class ModelControlWidget(QWidget):
    model_loaded = pyqtSignal(bool)

    def __init__(self, predictor, parent=None):
        super().__init__(parent)
        self.predictor = predictor
        self.thread = None
        self.worker = None

        # --- UI Setup (Minimalist Style) ---
        # Gunakan QFrame biasa (bukan GroupBox) agar lebih bersih
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(8)
        
        # Header Label
        lbl_header = QLabel("🤖 Model Deteksi (AI)")
        lbl_header.setStyleSheet("font-weight: bold; color: #475569; font-size: 12px;")
        layout.addWidget(lbl_header)
        
        # Container Row
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        self.model_selector = QComboBox()
        self.model_selector.setMinimumHeight(30)
        self.model_selector.setStyleSheet("""
            QComboBox {
                padding: 2px 10px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background-color: white;
                color: #334155;
            }
            QComboBox::drop-down { border: 0px; }
        """)
        
        self.upload_button = QPushButton("📂 Upload")
        self.upload_button.setToolTip("Upload file model baru (.joblib)")
        self.upload_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_button.setFixedSize(80, 30)
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2563EB;
                border: 1px solid #2563EB;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EFF6FF;
            }
        """)

        row_layout.addWidget(self.model_selector, 1) # Expand combo
        row_layout.addWidget(self.upload_button)
        
        layout.addLayout(row_layout)
        
        # Status Label (Small)
        self.model_status_label = QLabel("Status: Menunggu...")
        self.model_status_label.setStyleSheet("font-size: 10px; color: #94A3B8; margin-left: 2px;")
        layout.addWidget(self.model_status_label)

        # --- Signal Connections ---
        self.upload_button.clicked.connect(self.upload_new_model)
        self.model_selector.currentIndexChanged.connect(self.start_model_loading)
        
        # --- Initial State ---
        self.populate_model_selector()

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
