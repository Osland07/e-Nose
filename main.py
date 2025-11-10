import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from database.database import initialize_database

if __name__ == "__main__":
    initialize_database() # Initialize the database
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
