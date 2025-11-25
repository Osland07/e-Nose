from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QSpinBox, QLabel, QFormLayout
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from datetime import datetime

from ml.predictor import Predictor
from database.database import create_connection, add_detection_record

from .components.device_control import DeviceControlWidget
from .components.model_control import ModelControlWidget
from .components.environment_widget import EnvironmentWidget
from .components.graph_widget import GraphWidget, NUM_GRAPH_SENSORS
from .components.result_widget import ResultWidget

# --- Configuration ---
TOTAL_EXPECTED_VALUES = 11
# DETECTION_DURATION_MS = 15000 # This is now user-configurable

class MainPage(QWidget):
    record_added = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # --- State & Core Objects ---
        self.predictor = Predictor()
        self.is_detecting = False
        self.data_buffer = []
        
        # --- UI Components ---
        self.device_control = DeviceControlWidget()
        self.model_control = ModelControlWidget(self.predictor)
        self.environment_widget = EnvironmentWidget()
        self.graph_widget = GraphWidget()
        self.result_widget = ResultWidget()
        self.start_button = QPushButton("Mulai Deteksi")
        self.duration_spinbox = QSpinBox()
        
        self.setup_ui()
        self.connect_signals()

        # --- Timers ---
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._update_progress)

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # --- Left Panel ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(self.graph_widget)
        left_layout.addWidget(self.result_widget)
        left_layout.addStretch()
        left_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addStretch()
        
        # --- Right Panel ---
        right_panel = QWidget()
        right_panel.setFixedWidth(220)
        right_layout = QVBoxLayout(right_panel)
        
        # --- Settings Group ---
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setContentsMargins(8, 15, 8, 8)
        self.duration_spinbox.setRange(5, 120)
        self.duration_spinbox.setValue(15)
        self.duration_spinbox.setSuffix(" s")
        settings_layout.addRow(QLabel("Detection Duration:"), self.duration_spinbox)
        
        controls_group = QGroupBox("Device & Model Control")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.addWidget(self.device_control)
        controls_layout.addWidget(self.model_control)
        
        right_layout.addWidget(controls_group)
        right_layout.addWidget(settings_group)
        right_layout.addWidget(self.environment_widget)
        right_layout.addStretch()

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

        self.start_button.setEnabled(False)
        self.start_button.setMinimumHeight(50)
        self.start_button.setStyleSheet("""
            QPushButton { background-color: #2563EB; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:disabled { background-color: #9CA3AF; }
        """)
        # The progress bar max will be set dynamically now
        # self.result_widget.set_progress_max(DETECTION_DURATION_MS)

    def connect_signals(self):
        self.device_control.connection_status_changed.connect(self.on_connection_status_changed)
        self.device_control.data_received.connect(self.on_data_received)
        self.model_control.model_loaded.connect(self.on_model_loaded)
        self.start_button.clicked.connect(self.toggle_detection)

    def on_connection_status_changed(self, is_connected, message):
        self.update_start_button_state()
        if not is_connected:
            self.environment_widget.reset()
            if self.is_detecting:
                self.toggle_detection() 
            self.result_widget.reset()

    def on_model_loaded(self, is_loaded):
        self.update_start_button_state()

    def on_data_received(self, data_string):
        print(f"DEBUG: Data string received: '{data_string}'") # Re-added for debugging
        try:
            sensor_values = [float(x.strip()) for x in data_string.split(',')]
            if len(sensor_values) != TOTAL_EXPECTED_VALUES:
                print(f"DEBUG: Incorrect number of sensor values. Expected {TOTAL_EXPECTED_VALUES}, got {len(sensor_values)} for '{data_string}'") # Re-added for debugging
                return

            graph_values = sensor_values[:NUM_GRAPH_SENSORS]
            bme_values = sensor_values[NUM_GRAPH_SENSORS:]
            
            self.graph_widget.update_plot(graph_values)
            self.environment_widget.update_values(bme_values[0], bme_values[1], bme_values[2])
            
            if self.is_detecting:
                self.data_buffer.append(data_string)

        except (ValueError, IndexError) as e:
            print(f"DEBUG: Parsing error in on_data_received for '{data_string}': {e}") # Re-added for debugging
            pass 

    def toggle_detection(self):
        if self.is_detecting:
            # --- Cancel Detection ---
            self.is_detecting = False
            self.progress_timer.stop()
            self.start_button.setText("Mulai Deteksi")
            self.duration_spinbox.setEnabled(True)
            self.model_control.setEnabled(True)
            self.update_start_button_state()
            self.result_widget.set_cancelled_state()
        else:
            # --- Start Detection ---
            self.data_buffer.clear()
            self.is_detecting = True
            
            duration_s = self.duration_spinbox.value()
            duration_ms = duration_s * 1000
            
            self.start_button.setText("Batalkan")
            self.duration_spinbox.setEnabled(False)
            self.model_control.setEnabled(False)
            
            self.result_widget.set_progress_max(duration_ms)
            self.result_widget.set_collecting_state(duration_s)
            self.progress_timer.start(100) 
            
            QTimer.singleShot(duration_ms, self._finish_detection)

    def _update_progress(self):
        if self.is_detecting:
            current_value = self.result_widget.progress_bar.value() + self.progress_timer.interval()
            self.result_widget.set_progress_value(current_value)

    def _finish_detection(self):
        if not self.is_detecting:
            return
            
        self.is_detecting = False
        self.progress_timer.stop()
        
        self.duration_spinbox.setEnabled(True)
        self.model_control.setEnabled(True)
        
        if len(self.data_buffer) < 10: 
            self.result_widget.set_insufficient_data_state()
            self.start_button.setText("Mulai Deteksi")
            self.update_start_button_state()
            return

        result_label, confidence = self.predictor.predict(self.data_buffer)
        self.result_widget.set_result(result_label, confidence)
        self._save_record(f"{result_label} ({confidence:.2f}%)", self.data_buffer)
            
        self.start_button.setText("Mulai Deteksi")
        self.update_start_button_state()
    
    def _save_record(self, result_string, data_buffer):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        raw_data_str = "\\n".join(data_buffer)
        
        conn = create_connection()
        if conn:
            add_detection_record(conn, timestamp, result_string, raw_data_str)
            conn.close()
            self.record_added.emit()

    def update_start_button_state(self):
        can_start = self.predictor.model is not None and self.device_control.is_connected
        self.start_button.setEnabled(can_start)