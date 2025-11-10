from PyQt6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QLabel, 
    QPushButton, 
    QComboBox, 
    QHBoxLayout, 
    QGroupBox,
    QStyle,
    QFileDialog,
    QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from datetime import datetime
import os
import numpy as np
import shutil
import random

from arduino.serial_worker import SerialWorker, get_available_ports
from database.database import create_connection, add_detection_record
from ml.predictor import Predictor, get_available_models

import pyqtgraph as pg

# --- Configuration ---
NUM_GRAPH_SENSORS = 7  # MQ-2, MQ-3, MQ-4, MQ-6, MQ-7, MQ-8, MQ-135
TOTAL_EXPECTED_VALUES = 10 # 7 for graph + 3 from BME280 (Temp, Hum, Press)
MAX_DATA_POINTS = 200 # Number of data points to display on the graph

class SensorDisplay(QWidget):
    """A widget to display a single sensor reading with an icon, value, and unit."""
    def __init__(self, icon_path: str, unit: str, title: str):
        super().__init__()
        self.setMinimumWidth(110)
        self.setMaximumWidth(150)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # Main container for styling
        container = QWidget()
        container.setObjectName("sensorCard")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(4, 4, 4, 4)
        container_layout.setSpacing(4)

        # Icon on the left
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(icon_path).pixmap(24, 24))
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Value and Unit Layout on the right
        value_layout = QVBoxLayout()
        value_layout.setSpacing(0)
        value_layout.setContentsMargins(0, 0, 0, 0)
        
        self.value_label = QLabel("--")
        self.value_label.setObjectName("sensorValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        unit_label = QLabel(unit)
        unit_label.setObjectName("sensorUnit")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_layout.addWidget(self.value_label)
        value_layout.addWidget(unit_label)

        # Add icon and value layout to container
        container_layout.addWidget(icon_label)
        container_layout.addLayout(value_layout, 1)

        # Title Label below
        title_label = QLabel(title)
        title_label.setObjectName("sensorTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(container)
        main_layout.addWidget(title_label)

        self.setStyleSheet("""
            #sensorCard {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 0px;
            }
            #sensorValue {
                font-size: 18px;
                font-weight: bold;
                color: #1E3A8A;
            }
            #sensorUnit {
                font-size: 10px;
                color: #64748B;
            }
            #sensorTitle {
                font-size: 10px;
                font-weight: 500;
                color: #334155;
            }
        """)

    def set_value(self, value: float, precision: int = 2):
        self.value_label.setText(f"{value:.{precision}f}")

    def reset(self):
        self.value_label.setText("--")

class MainPage(QWidget):
    record_added = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # --- Main Layout ---
        main_layout = QHBoxLayout(self)

        # --- Left Panel for Main Content ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # --- Right Panel for Sensors ---
        right_panel = QWidget()
        right_panel.setFixedWidth(200) # Set a fixed width for the right panel
        right_layout = QVBoxLayout(right_panel)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

        # --- Device & Model + Environment Container (for the right panel) ---
        self.controls_environment_group = QGroupBox("Device & Model Control")
        controls_env_layout = QVBoxLayout(self.controls_environment_group)
        
        # --- Sensor Displays (for the right panel) ---
        self.sensor_group = QGroupBox("Environment")
        sensor_layout = QVBoxLayout(self.sensor_group) # Changed to QVBoxLayout
        sensor_layout.setContentsMargins(5, 15, 5, 5)  # Increased top margin for spacing
        self.sensor_group.setMinimumHeight(160)  # Increased minimum height
        self.sensor_group.setMaximumHeight(220)  # Increased maximum height
        
        base_path = os.path.abspath(os.path.dirname(__file__))
        assets_path = os.path.join(base_path, '..', 'assets')

        self.temperature_display = SensorDisplay(os.path.join(assets_path, 'temperature.svg'), "°C", "Temperature")
        self.humidity_display = SensorDisplay(os.path.join(assets_path, 'humidity.svg'), "%", "Humidity")
        self.pressure_display = SensorDisplay(os.path.join(assets_path, 'pressure.svg'), "hPa", "Pressure")

        sensor_layout.addWidget(self.temperature_display)
        sensor_layout.addSpacing(5)
        sensor_layout.addWidget(self.humidity_display)
        sensor_layout.addSpacing(5)
        sensor_layout.addWidget(self.pressure_display)
        sensor_layout.addStretch() # Pushes sensors to the top

        # --- Device & Model Control Group (now contains both controls and environment) ---
        self.status_label = QLabel("Mencari perangkat...")
        self.model_selector = QComboBox()
        self.upload_button = QPushButton("📁 Pilih File")
        self.model_status_label = QLabel("Model: (belum ada)")

        # Upload Model Form Section
        upload_form_group = QGroupBox("Upload Model")
        upload_form_layout = QVBoxLayout(upload_form_group)
        upload_form_layout.setContentsMargins(8, 10, 8, 8)
        upload_form_layout.setSpacing(6)
        
        # Model Selection Row
        select_label = QLabel("Pilih Model:")
        select_label.setStyleSheet("font-weight: 600;")
        upload_form_layout.addWidget(select_label)
        upload_form_layout.addWidget(self.model_selector)
        
        # Upload Button
        upload_form_layout.addSpacing(2)
        upload_form_layout.addWidget(self.upload_button)
        
        # Status Info
        upload_form_layout.addSpacing(2)
        upload_form_layout.addWidget(self.model_status_label)

        controls_env_layout.addSpacing(8)  # Space at top
        controls_env_layout.addWidget(self.status_label)
        controls_env_layout.addSpacing(10)
        controls_env_layout.addWidget(upload_form_group)
        controls_env_layout.addSpacing(10)
        controls_env_layout.addWidget(self.sensor_group)
        controls_env_layout.addStretch()

        # Graph Group (for the left panel)
        graph_group = QGroupBox("Grafik Sensor Gas")
        self.graph_widget = pg.PlotWidget()
        
        # Result & Action (for the left panel)
        self.result_label = QLabel("Menunggu Deteksi")
        self.start_button = QPushButton("Mulai Deteksi")

        # --- Configure Widgets & Layouts ---
        
        # Device & Model Control + Environment Group (Right Panel)
        self.controls_environment_group.setStyleSheet("""
            QGroupBox { font-size: 16px; font-weight: bold; color: #1E3A8A; margin-top: 10px; border: 1px solid #D1D5DB; border-radius: 8px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 5px 10px; }
        """)
        
        # Upload Model Form Group styling
        upload_form_group.setStyleSheet("""
            QGroupBox { 
                font-size: 13px; 
                font-weight: bold; 
                color: #1E3A8A; 
                margin-top: 8px; 
                border: 2px solid #3B82F6; 
                border-radius: 6px;
                background-color: #F0F9FF;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                subcontrol-position: top left; 
                padding: 3px 8px; 
            }
        """)
        
        # Sensor Group (nested inside controls_environment_group)
        self.sensor_group.setStyleSheet("""
            QGroupBox { font-size: 14px; font-weight: bold; color: #1E3A8A; margin-top: 8px; border: 1px solid #E2E8F0; border-radius: 6px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 3px 8px; }
        """)
        
        self.status_label.setStyleSheet("font-size: 10px; font-weight: bold; color: orange;")
        
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-size: 11px;
                font-weight: 600;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        self.upload_button.setMinimumHeight(32)
        
        self.model_selector.setStyleSheet("""
            QComboBox {
                font-size: 10px;
                padding: 6px;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self.model_status_label.setStyleSheet("font-size: 9px; color: #64748B; font-style: italic;")
        
        right_layout.addWidget(self.controls_environment_group)
        right_layout.addStretch()

        # Graph Group (Left Panel)
        graph_group.setStyleSheet("""
            QGroupBox { font-size: 18px; font-weight: bold; color: #1E3A8A; margin-top: 10px; border: 1px solid #D1D5DB; border-radius: 8px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; }
        """)
        graph_layout = QVBoxLayout(graph_group)
        graph_layout.addWidget(self.graph_widget)
        
        self.graph_widget.setBackground('w')
        self.graph_widget.setTitle("Data Sensor Real-time", color="#1E3A8A", size="16pt")
        styles = {'color':'#1E3A8A', 'font-size':'12pt'}
        self.graph_widget.setLabel('left', 'Nilai Sensor', **styles)
        self.graph_widget.setLabel('bottom', 'Waktu (sampel)', **styles)
        self.graph_widget.addLegend()
        self.graph_widget.showGrid(x=True, y=True)

        # Result Label (Left Panel)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #4B5563; padding: 20px; border: 2px dashed #D1D5DB; border-radius: 8px;")

        # Start Button (Left Panel)
        self.start_button.setMinimumHeight(50)
        self.start_button.setStyleSheet("""
            QPushButton { background-color: #2563EB; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
            QPushButton:disabled { background-color: #9CA3AF; }
        """)
        self.start_button.setEnabled(False)

        # --- Add Widgets to Left Panel Layout ---
        left_layout.addWidget(graph_group)
        left_layout.addWidget(self.result_label)
        left_layout.addStretch()
        left_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addStretch()

        # --- Connect Signals ---
        self.start_button.clicked.connect(self.start_detection_simulation)
        self.model_selector.currentIndexChanged.connect(self.load_selected_model)
        self.upload_button.clicked.connect(self.upload_new_model)
        
        # --- Initialize State & Timers ---
        self.predictor = Predictor()
        self.setup_graph_lines()
        
        self.serial_worker = None
        self.is_connected = False
        self.current_port = None
        
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self.scan_and_connect)
        self.scan_timer.start(3000)
        self.scan_and_connect()
        self.populate_model_selector()

    def setup_graph_lines(self):
        self.y_data = [[] for _ in range(NUM_GRAPH_SENSORS)]
        self.plot_lines = []
        sensor_names = ["MQ-2", "MQ-3", "MQ-4", "MQ-6", "MQ-7", "MQ-8", "MQ-135"]
        colors = ['#E53935', '#1E88E5', '#43A047', '#FDD835', '#FB8C00', '#8E24AA', '#00897B', '#D81B60']
        for i in range(NUM_GRAPH_SENSORS):
            pen = pg.mkPen(color=colors[i % len(colors)], width=2)
            self.plot_lines.append(self.graph_widget.plot([0], [0], pen=pen, name=sensor_names[i]))

    def upload_new_model(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Pilih File Model SVM", "", "Joblib Files (*.joblib);;All Files (*)")
        if fileName:
            try:
                model_dir = "model"
                if not os.path.exists(model_dir): os.makedirs(model_dir)
                base_name = os.path.basename(fileName)
                dest_path = os.path.join(model_dir, base_name)
                shutil.copy(fileName, dest_path)
                self.populate_model_selector()
                index = self.model_selector.findText(base_name)
                if index != -1: self.model_selector.setCurrentIndex(index)
                self.model_status_label.setText(f"Upload sukses: '{base_name}'")
            except Exception as e:
                self.model_status_label.setText(f"Error upload: {e}")

    def populate_model_selector(self):
        self.model_selector.clear()
        models = get_available_models()
        if models:
            self.model_selector.addItems(models)
            self.load_selected_model()
        else:
            self.model_selector.addItem("Tidak ada model")
            self.model_status_label.setText("Model: Upload model Anda.")
            self.start_button.setEnabled(False)

    def load_selected_model(self):
        selected_model_file = self.model_selector.currentText()
        if selected_model_file in ["Tidak ada model", ""]:
            self.model_status_label.setText("Model: Tidak ada model terpilih.")
            self.start_button.setEnabled(False)
            return
        if self.predictor.load_model(selected_model_file):
            self.model_status_label.setText(f"Model digunakan: {selected_model_file}")
            self.start_button.setEnabled(self.is_connected)
        else:
            self.model_status_label.setText(f"Gagal memuat: {selected_model_file}")
            self.start_button.setEnabled(False)

    def scan_and_connect(self):
        if self.is_connected and self.current_port in get_available_ports(): return
        ports = get_available_ports()
        if not ports:
            self.handle_connection_status(False, "Hubungkan")
            return
        self.current_port = ports[0]
        self.serial_worker = SerialWorker(self.current_port)
        self.serial_worker.data_received.connect(self.handle_data_received)
        self.serial_worker.connection_status.connect(self.handle_connection_status)
        self.serial_worker.error_occurred.connect(self.handle_error_occurred)
        self.serial_worker.start()

    def handle_data_received(self, data):
        try:
            sensor_values = [float(x.strip()) for x in data.split(',')]
            if len(sensor_values) != TOTAL_EXPECTED_VALUES:
                self.status_label.setText(f"Data Error: Diterima {len(sensor_values)} nilai, diharapkan {TOTAL_EXPECTED_VALUES}.")
                return
            
            graph_values = sensor_values[:NUM_GRAPH_SENSORS]
            bme_values = sensor_values[NUM_GRAPH_SENSORS:]
            
            self.temperature_display.set_value(bme_values[0])
            self.humidity_display.set_value(bme_values[1])
            self.pressure_display.set_value(bme_values[2] / 100)
            
            for i in range(NUM_GRAPH_SENSORS):
                self.y_data[i].append(graph_values[i])
                if len(self.y_data[i]) > MAX_DATA_POINTS: self.y_data[i].pop(0)
            self.update_plot()
            
            if self.predictor.model:
                prediction_data_string = ','.join(map(str, graph_values))
                prediction_result = self.predictor.predict(prediction_data_string)
                self.result_label.setText(prediction_result)
                if "Halal" in prediction_result:
                    self.result_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #16A34A; padding: 20px; border: 2px solid #16A34A; border-radius: 8px;")
                else:
                    self.result_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #DC2626; padding: 20px; border: 2px solid #DC2626; border-radius: 8px;")
        except (ValueError, IndexError) as e:
            self.status_label.setText(f"Error proses data: {e}")

    def update_plot(self):
        for i in range(NUM_GRAPH_SENSORS):
            current_x_data = list(range(len(self.y_data[i])))
            self.plot_lines[i].setData(current_x_data, self.y_data[i])

    def handle_connection_status(self, status, message=None):
        self.is_connected = status
        if status:
            self.status_label.setText("Perangkat terhubung")
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
            self.start_button.setEnabled(self.predictor.model is not None)
        else:
            if self.serial_worker: self.serial_worker.stop()
            self.serial_worker = None
            self.current_port = None
            self.status_label.setText(message or "Perangkat terputus.")
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")
            
            self.temperature_display.reset()
            self.humidity_display.reset()
            self.pressure_display.reset()

            self.result_label.setText("Menunggu Deteksi")
            self.result_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #4B5563; padding: 20px; border: 2px dashed #D1D5DB; border-radius: 8px;")
            self.start_button.setEnabled(False)

    def handle_error_occurred(self, error_message):
        self.handle_connection_status(False, f"Koneksi Error: {error_message}")

    def start_detection_simulation(self):
        if self.predictor.model is None:
            self.model_status_label.setText("Tidak bisa mulai: Model belum dimuat.")
            return
        
        self.start_button.setText("Mendeteksi...")
        self.start_button.setEnabled(False)
        
        dummy_values = [random.randint(50, 300) for _ in range(NUM_GRAPH_SENSORS)]
        dummy_data_string = ','.join(map(str, dummy_values))
        
        prediction_result = self.predictor.predict(dummy_data_string)
        self.result_label.setText(f"Simulasi: {prediction_result}")
        if "Halal" in prediction_result:
            self.result_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #16A34A; padding: 20px; border: 2px solid #16A34A; border-radius: 8px;")
        else:
            self.result_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #DC2626; padding: 20px; border: 2px solid #DC2626; border-radius: 8px;")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = create_connection()
        if conn:
            add_detection_record(conn, timestamp, prediction_result)
            conn.close()
            self.record_added.emit()
        
        QTimer.singleShot(1500, lambda: self.start_button.setText("Mulai Deteksi"))
        QTimer.singleShot(1500, lambda: self.start_button.setEnabled(True))
