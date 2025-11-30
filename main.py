import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
import qdarktheme # Import library tema
from ui.main_window import MainWindow
from database.database import initialize_database

# --- GLOBAL ERROR HANDLER (AIRBAG) ---
def exception_hook(exctype, value, tb):
    """
    Menangkap semua error yang tidak terduga agar aplikasi tidak langsung force close.
    Menampilkan detail error di jendela pop-up.
    """
    traceback_str = ''.join(traceback.format_tb(tb))
    error_msg = f"{value}"
    
    print("CRITICAL ERROR CAUGHT:")
    print(error_msg)
    print(traceback_str)
    
    # Pastikan ada instance QApplication sebelum menampilkan message box
    app = QApplication.instance()
    if app:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Terjadi Kesalahan Fatal")
        msg.setText("Maaf, terjadi error yang tidak terduga.")
        msg.setInformativeText(error_msg)
        msg.setDetailedText(traceback_str) # User bisa klik "Show Details"
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    # Panggil handler bawaan (biasanya exit)
    sys.__excepthook__(exctype, value, tb)

if __name__ == "__main__":
    # Pasang Airbag
    sys.excepthook = exception_hook
    
    # Initialize Database
    initialize_database() 
    
    app = QApplication(sys.argv)
    
    # --- APPLY MODERN THEME ---
    # Ganti ke 'light' mode sesuai permintaan user agar form terlihat normal
    qdarktheme.setup_theme("light", corner_shape="rounded") 
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
