from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from arduino.serial_worker import SerialWorker, get_available_ports

class DeviceControlWidget(QWidget):
    connection_status_changed = pyqtSignal(bool, str)
    data_received = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_connected = False
        self.is_connecting = False # Added flag
        self.current_port = None
        self.serial_worker = None

        layout = QVBoxLayout(self)
        self.status_label = QLabel("Mencari perangkat...")
        self.status_label.setStyleSheet("font-size: 10px; font-weight: bold; color: orange;")
        layout.addWidget(self.status_label)
        
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self.scan_and_connect)
        self.scan_timer.start(3000) # Start the timer to initiate scanning

    def scan_and_connect(self):
        if self.is_connected or self.is_connecting: # Check both flags
            return
            
        print(f"DEBUG (DeviceControl): Scanning for ports...")
        ports = get_available_ports()
        print(f"DEBUG (DeviceControl): Available ports: {ports}")

        if not ports:
            self.status_label.setText("Hubungkan Perangkat")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
            return

        # If not connected, try to connect to the first available port
        self.current_port = ports[0]
        print(f"DEBUG (DeviceControl): Attempting to connect to: {self.current_port}")
        
        self.is_connecting = True # Set connecting flag
        if self.serial_worker:
            self.serial_worker.stop()

        self.serial_worker = SerialWorker(self.current_port)
        self.serial_worker.data_received.connect(self.data_received.emit)
        self.serial_worker.connection_status.connect(self.handle_connection_status)
        self.serial_worker.error_occurred.connect(self.handle_error_occurred)
        self.serial_worker.start()

    def handle_connection_status(self, status, message=None):
        self.is_connected = status
        self.is_connecting = False # Reset connecting flag
        print(f"DEBUG (DeviceControl): Connection status changed: {status}. Message: {message}")
        
        if status:
            self.scan_timer.stop() # Stop scanning once connected
            self.status_label.setText("Perangkat terhubung")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")
        else:
            if self.serial_worker:
                self.serial_worker.stop()
            self.serial_worker = None
            self.current_port = None
            self.status_label.setText(message or "Perangkat terputus.")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
            self.scan_timer.start(3000) # Restart scanning if disconnected
        
        self.connection_status_changed.emit(status, message)

    def handle_error_occurred(self, error_message):
        self.handle_connection_status(False, f"Koneksi Error: {error_message}")
