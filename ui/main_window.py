import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QStyle
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from ui.training_page import TrainingPage
from ui.help_page import HelpPage
from ui.components.toast import ToastNotification

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
# ... (kode init) ...
        # --- Pages Setup ---
        self.main_page = MainPage()
        self.history_page = HistoryPage()
        self.training_page = TrainingPage()
        self.help_page = HelpPage() # Halaman Baru
        
        self.pages.addWidget(self.main_page)
        self.pages.addWidget(self.history_page)
        self.pages.addWidget(self.training_page)
        self.pages.addWidget(self.help_page)

        # Connect signals
        self.main_page.record_added.connect(self.refresh_history_page)

        # --- Populate Nav ---
        self.add_nav_item("📊  DASHBOARD UTAMA")
        self.add_nav_item("📂  RIWAYAT DATA")
        self.add_nav_item("⚙️  TRAINING CENTER")
        self.add_nav_item("❓  BANTUAN & INFO") # Menu Baru

        self.nav_list.currentRowChanged.connect(self.switch_page)
        self.nav_list.setCurrentRow(0)
        
        # --- TOAST NOTIFICATION ---
        self.toast = ToastNotification(self)

    def add_nav_item(self, text):
        item = QListWidgetItem(text)
        item.setSizeHint(QSize(0, 50))
        self.nav_list.addItem(item)

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)

    def refresh_history_page(self):
        self.history_page.populate_table()
        
    def show_toast(self, message, type="info"):
        self.toast.show_message(message, type)

    def closeEvent(self, event):
        # Ensure the serial worker thread is stopped safely
        if hasattr(self, 'main_page') and hasattr(self.main_page, 'device_control'):
            if self.main_page.device_control.serial_worker and self.main_page.device_control.serial_worker.isRunning():
                self.main_page.device_control.serial_worker.stop()
        event.accept()
