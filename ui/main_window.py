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

# --- IMPORT HALAMAN ---
from ui.main_page import MainPage
from ui.history_page import HistoryPage
from ui.training_page import TrainingPage
from ui.help_page import HelpPage
from ui.components.toast import ToastNotification

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-Nose AI Dashboard")
        self.setGeometry(100, 100, 1100, 750) 

        # --- Main Layout ---
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # --- 1. SIDEBAR ---
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(260)
        sidebar_widget.setStyleSheet("background-color: #1E3A8A;") # Navy Blue
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 20) # Reset margin atas/bawah
        sidebar_layout.setSpacing(5)
        sidebar_widget.setLayout(sidebar_layout)
        main_layout.addWidget(sidebar_widget)

        # Logo Area
        logo_container = QWidget()
        logo_container.setStyleSheet("background-color: #172554; border-bottom: 1px solid #1E40AF;") # Darker Navy
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(20, 30, 20, 30)
        
        logo_label = QLabel("E-NOSE\nDETECTOR")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        logo_label.setStyleSheet("font-size: 24px; font-weight: 900; color: #FFFFFF; border: none;")
        logo_layout.addWidget(logo_label)
        
        sidebar_layout.addWidget(logo_container)
        sidebar_layout.addSpacing(10)

        # Navigation
        self.nav_list = QListWidget()
        self.nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Hilangkan garis putus-putus saat klik
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: transparent; border: none; outline: none;
                font-size: 14px; font-weight: 600; color: #93C5FD; /* Light Blue Text */
            }
            QListWidget::item {
                padding: 15px 25px; 
                border-left: 4px solid transparent;
                margin-bottom: 2px;
            }
            QListWidget::item:hover {
                background-color: #172554; /* Darker Hover */
                color: #FFFFFF;
            }
            QListWidget::item:selected {
                background-color: #2563EB; /* Bright Blue Selected */
                color: #FFFFFF;
                border-left: 4px solid #FFFFFF; /* White accent */
            }
        """)
        sidebar_layout.addWidget(self.nav_list)

        # Footer
        version_label = QLabel("v3.0 (Ultimate)\n© 2025 Lab Riset")
        version_label.setStyleSheet("color: #60A5FA; font-size: 10px; padding-bottom: 10px;") # Lighter Blue
        version_label.setStyleSheet("color: #475569; font-size: 10px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(version_label)

        # --- 2. MAIN CONTENT ---
        # Inisialisasi StackedWidget (YANG TADI HILANG)
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background-color: transparent;") 
        
        content_container = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30) 
        content_layout.addWidget(self.pages)
        content_container.setLayout(content_layout)
        
        main_layout.addWidget(content_container)

        # --- Pages Setup ---
        self.main_page = MainPage()
        self.history_page = HistoryPage()
        self.training_page = TrainingPage()
        self.help_page = HelpPage()
        
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
        self.add_nav_item("❓  BANTUAN & INFO")

        self.nav_list.currentRowChanged.connect(self.switch_page)
        self.nav_list.setCurrentRow(0)
        
        # --- TOAST ---
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
        if hasattr(self, 'main_page') and hasattr(self.main_page, 'device_control'):
            if self.main_page.device_control.serial_worker and self.main_page.device_control.serial_worker.isRunning():
                self.main_page.device_control.serial_worker.stop()
        event.accept()