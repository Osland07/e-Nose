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

from ui.main_page import MainPage
from ui.history_page import HistoryPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("e-Nose")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("background-color: #FFFFFF;")

        # Main container
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # --- Sidebar ---
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(240)
        sidebar_widget.setStyleSheet("background-color: #E6F2FF;") # Light Blue
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(10, 0, 10, 10)
        sidebar_layout.setSpacing(0)
        sidebar_widget.setLayout(sidebar_layout)
        main_layout.addWidget(sidebar_widget)

        # Logo placeholder
        logo_label = QLabel("e-Nose")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setMinimumHeight(80)
        logo_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1E3A8A; /* Dark Blue */
            background-color: #E6F2FF; /* Match sidebar */
            padding-top: 10px;
        """)
        sidebar_layout.addWidget(logo_label)

        # Navigation list
        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #E6F2FF; /* Light Blue */
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: #1E3A8A; /* Dark Blue for text */
            }
            QListWidget::item {
                padding: 15px 20px;
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background-color: #D1E3FF; /* Slightly darker blue */
            }
            QListWidget::item:selected {
                background-color: #FFFFFF; /* White */
                color: #1E3A8A; /* Dark Blue */
            }
        """)
        sidebar_layout.addWidget(self.nav_list)

        # --- Main Content ---
        self.pages = QStackedWidget()
        content_container = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_container.setLayout(content_layout)
        content_layout.addWidget(self.pages)
        main_layout.addWidget(content_container)

        # --- Pages ---
        self.main_page = MainPage()
        self.history_page = HistoryPage()
        self.pages.addWidget(self.main_page)
        self.pages.addWidget(self.history_page)

        # Connect signals
        self.main_page.record_added.connect(self.refresh_history_page)

        # --- Navigation Items ---
        home_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon)
        history_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)

        self.add_nav_item(home_icon, "Main Page", self.nav_list)
        self.add_nav_item(history_icon, "History", self.nav_list)

        self.nav_list.currentRowChanged.connect(self.switch_page)
        self.nav_list.setCurrentRow(0)

    def add_nav_item(self, icon, text, list_widget):
        item = QListWidgetItem(icon, text)
        item.setSizeHint(QSize(0, 60))
        list_widget.addItem(item)

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)

    def refresh_history_page(self):
        self.history_page.populate_table()

    def closeEvent(self, event):
        # Ensure the serial worker thread is stopped when the application closes
        if self.main_page.serial_worker and self.main_page.serial_worker.isRunning():
            self.main_page.serial_worker.stop()
        event.accept()

