from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QRadioButton, QButtonGroup, QHBoxLayout
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from arduino.serial_worker import SerialWorker, get_available_ports
import random

class DeviceControlWidget(QWidget):
    connection_status_changed = pyqtSignal(bool, str)
    data_received = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_connected = False
        self.is_connecting = False
        self.current_port = None
        self.serial_worker = None
        self.is_simulation = False # Flag simulasi

        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # --- STATUS LABEL ---
        self.status_label = QLabel("Mencari perangkat...")
        self.status_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #F59E0B;") # Orange
        layout.addWidget(self.status_label)
        
        # --- SIMULATION CONTROLS ---
        sim_layout = QVBoxLayout()
        
        self.chk_simulation = QCheckBox("Mode Simulasi (Tanpa Alat)")
        self.chk_simulation.setStyleSheet("color: #334155; font-weight: bold;")
        self.chk_simulation.toggled.connect(self.toggle_simulation_mode)
        
        # Container pilihan data (Hanya muncul kalau simulasi aktif)
        self.sim_controls_widget = QWidget()
        self.sim_controls_widget.setVisible(False) # Hidden by default
        sim_opts_layout = QVBoxLayout(self.sim_controls_widget)
        sim_opts_layout.setContentsMargins(10, 0, 0, 0)
        
        self.rb_clean = QRadioButton("Data Bersih (Aman)")
        self.rb_biomarker = QRadioButton("Data Biomarker (Terdeteksi)")
        self.rb_clean.setChecked(True)
        
        sim_opts_layout.addWidget(self.rb_clean)
        sim_opts_layout.addWidget(self.rb_biomarker)
        
        sim_layout.addWidget(self.chk_simulation)
        sim_layout.addWidget(self.sim_controls_widget)
        
        layout.addLayout(sim_layout)
        
        # --- TIMERS ---
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self.scan_and_connect)
        self.scan_timer.start(3000) 
        
        # Timer khusus untuk generate data dummy
        self.sim_data_timer = QTimer(self)
        self.sim_data_timer.timeout.connect(self.generate_dummy_data)

    def toggle_simulation_mode(self, checked):
        self.is_simulation = checked
        self.sim_controls_widget.setVisible(checked)
        
        if checked:
            # STOP Scanning asli
            self.scan_timer.stop()
            if self.serial_worker:
                self.serial_worker.stop()
            
            # START Simulasi
            self.status_label.setText("Mode Simulasi: AKTIF")
            self.status_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #3B82F6;") # Blue
            self.sim_data_timer.start(1000) # Generate data tiap 1 detik
            
            # Fake connect signal
            self.is_connected = True
            self.connection_status_changed.emit(True, "Simulasi Terhubung")
            
        else:
            # STOP Simulasi
            self.sim_data_timer.stop()
            self.is_connected = False
            self.connection_status_changed.emit(False, "Simulasi Berhenti")
            
            # RESTART Scanning asli
            self.status_label.setText("Mencari perangkat...")
            self.status_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #F59E0B;")
            self.scan_timer.start(3000)

    def generate_dummy_data(self):
        """Membuat string data CSV palsu sesuai pilihan user"""
        # Format: MQ2, MQ3, MQ4, MQ6, MQ7, MQ8, MQ135, QCM, Temp, Hum, Pres
        
        data = []
        is_bio = self.rb_biomarker.isChecked()
        
        # Generate 8 Sensor Gas + QCM
        for i in range(8):
            if is_bio:
                # KASUS BIOMARKER: Buat Nilai SANGAT TINGGI agar AI yakin 99%
                # MQ135 (idx 6) dan QCM (idx 7) adalah fitur utama
                if i == 6: base = 800.0 # MQ135 Tinggi
                elif i == 7: base = 900.0 # QCM Tinggi
                else: base = 400.0 # Sensor lain juga naik
            else:
                # KASUS BERSIH: Nilai Sangat Rendah
                base = 20.0
            
            # Tambah noise random dikit biar grafik goyang
            val = base + random.uniform(-5, 5)
            data.append(f"{val:.2f}")
            
        # Generate Environment (Temp, Hum, Pres)
        data.append(f"{28.0 + random.uniform(-0.5, 0.5):.1f}") # Temp
        data.append(f"{60.0 + random.uniform(-2, 2):.1f}")    # Hum
        data.append(f"{1005.0 + random.uniform(-1, 1):.1f}")  # Pres
        
        data_str = ",".join(data)
        self.data_received.emit(data_str)

    def scan_and_connect(self):
        if self.is_simulation: return # Jangan scan kalau lagi simulasi
        
        if self.is_connected or self.is_connecting: 
            return
            
        # print(f"DEBUG (DeviceControl): Scanning for ports...") 
        ports = get_available_ports()
        # print(f"DEBUG (DeviceControl): Available ports: {ports}")

        if not ports:
            self.status_label.setText("Hubungkan Perangkat")
            self.status_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #F59E0B;")
            return

        # If not connected, try to connect to the first available port
        self.current_port = ports[0]
        # print(f"DEBUG (DeviceControl): Attempting to connect to: {self.current_port}")
        
        self.is_connecting = True 
        if self.serial_worker:
            self.serial_worker.stop()

        self.serial_worker = SerialWorker(self.current_port)
        self.serial_worker.data_received.connect(self.data_received.emit)
        self.serial_worker.connection_status.connect(self.handle_connection_status)
        self.serial_worker.error_occurred.connect(self.handle_error_occurred)
        self.serial_worker.start()

    def handle_connection_status(self, status, message=None):
        self.is_connected = status
        self.is_connecting = False
        
        if status:
            self.scan_timer.stop() 
            self.status_label.setText("Perangkat TERHUBUNG")
            self.status_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #10B981;") # Green
        else:
            if self.serial_worker:
                self.serial_worker.stop()
            self.serial_worker = None
            self.current_port = None
            self.status_label.setText(message or "Perangkat Terputus")
            self.status_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #EF4444;") # Red
            
            if not self.is_simulation:
                self.scan_timer.start(3000)
        
        self.connection_status_changed.emit(status, message)

    def handle_error_occurred(self, error_message):
        self.handle_connection_status(False, f"Error: {error_message}")