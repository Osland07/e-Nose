from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class ResultWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        self.result_label = QLabel("Menunggu Deteksi")
        self.confidence_label = QLabel("")
        self.progress_bar = QProgressBar()

        self._setup_styles()

        layout.addWidget(self.result_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.confidence_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

    def _setup_styles(self):
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("""
            font-size: 28px; 
            font-weight: bold; 
            color: #4B5563; 
            padding: 10px; 
            border: 2px dashed #D1D5DB; 
            border-radius: 8px;
        """)
        self.confidence_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #4B5563; padding-bottom: 10px;")
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)

    def set_progress_max(self, value):
        self.progress_bar.setRange(0, value)

    def set_progress_value(self, value):
        self.progress_bar.setValue(value)

    def show_progress(self, visible):
        self.progress_bar.setVisible(visible)

    def set_collecting_state(self, duration_s):
        self.result_label.setText("Mengumpulkan data...")
        self.confidence_label.setText(f"durasi {duration_s} detik")
        self.result_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #4B5563; padding: 10px; border: 2px dashed #D1D5DB; border-radius: 8px;")
        self.show_progress(True)
        self.set_progress_value(0)

    def set_cancelled_state(self):
        self.result_label.setText("Deteksi Dibatalkan")
        self.confidence_label.setText("")
        self.show_progress(False)

    def set_insufficient_data_state(self):
        self.result_label.setText("Gagal: Data tidak cukup")
        self.confidence_label.setText("Coba lagi.")
        self.show_progress(False)

    def set_result(self, label, confidence):
        self.result_label.setText(label)
        self.confidence_label.setText(f"Tingkat kepercayaan: {confidence:.2f}%")
        if "Terdeteksi" in label:
            self.result_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #DC2626; padding: 10px; border: 2px solid #DC2626; border-radius: 8px;")
        else:
            self.result_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #16A34A; padding: 10px; border: 2px solid #16A3A; border-radius: 8px;")
        self.show_progress(False)
    
    def reset(self):
        self.result_label.setText("Menunggu Deteksi")
        self.confidence_label.setText("")
        self.result_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #4B5563; padding: 10px; border: 2px dashed #D1D5DB; border-radius: 8px;")
        self.show_progress(False)

