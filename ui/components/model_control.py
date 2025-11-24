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
    QMessageBox
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

        # --- UI Setup ---
        layout = QGroupBox("Upload Model")
        form_layout = QVBoxLayout(layout)
        form_layout.setContentsMargins(8, 10, 8, 8)
        form_layout.setSpacing(6)
        
        self.model_selector = QComboBox()
        self.upload_button = QPushButton("📁 Pilih File Model")
        self.model_status_label = QLabel("Model: (belum ada)")

        form_layout.addWidget(QLabel("Pilih Model:"))
        form_layout.addWidget(self.model_selector)
        form_layout.addSpacing(2)
        form_layout.addWidget(self.upload_button)
        form_layout.addSpacing(2)
        form_layout.addWidget(self.model_status_label)
        
        # Main layout for this widget
        main_v_layout = QVBoxLayout(self)
        main_v_layout.addWidget(layout)
        
        self.setup_ui_styles()

        # --- Signal Connections ---
        self.upload_button.clicked.connect(self.upload_new_model)
        self.model_selector.currentIndexChanged.connect(self.start_model_loading)
        
        # --- Initial State ---
        self.populate_model_selector()

    def setup_ui_styles(self):
        self.setStyleSheet("""
            QGroupBox { font-size: 13px; font-weight: bold; color: #1E3A8A; margin-top: 8px; border: 2px solid #3B82F6; border-radius: 6px; background-color: #F0F9FF; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 3px 8px; }
        """)
        self.upload_button.setStyleSheet("""
            QPushButton { background-color: #3B82F6; color: white; font-size: 11px; font-weight: 600; padding: 8px 12px; border: none; border-radius: 4px; } 
            QPushButton:hover { background-color: #2563EB; }
            QPushButton:disabled { background-color: #9CA3AF; color: #E5E7EB; }
        """)
        self.upload_button.setMinimumHeight(32)
        self.model_selector.setStyleSheet("QComboBox { font-size: 10px; padding: 6px; border: 1px solid #D1D5DB; border-radius: 4px; background-color: white; } QComboBox:disabled { background-color: #F3F4F6; }")
        self.model_status_label.setStyleSheet("font-size: 9px; color: #64748B; font-style: italic;")

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
            self.model_status_label.setText("Model: Upload model Anda.")
            self.model_loaded.emit(False)
        self.model_selector.blockSignals(False)

    def start_model_loading(self):
        selected_model_file = self.model_selector.currentText()
        if selected_model_file in ["Tidak ada model", ""]:
            self.model_status_label.setText("Model: Tidak ada model terpilih.")
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
            # Also set the filename for reference
            self.predictor.loaded_model_name = selected_model_file
            self.model_status_label.setText(f"Model: {selected_model_file}")
            self.model_loaded.emit(True)
        else:
            self.model_status_label.setText(f"Gagal memuat: {selected_model_file}")
            self.model_loaded.emit(False)
            self.show_error_message("Model tidak valid", "File model yang dipilih rusak atau tidak memiliki format yang benar (harus berisi 'model', 'scaler', dan 'columns').")
        
        self.set_loading_state(False)

        # Clean up thread
        if self.thread is not None:
            self.thread.quit()
            self.thread.wait()

    def set_loading_state(self, is_loading):
        self.model_selector.setEnabled(not is_loading)
        self.upload_button.setEnabled(not is_loading)
        if is_loading:
            self.model_status_label.setText("<i>Memuat model...</i>")
        
    def show_error_message(self, title, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(title)
        msg_box.setInformativeText(message)
        msg_box.setWindowTitle("Error")
        msg_box.exec()