from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, 
    QSpinBox, QLabel, QFormLayout, QFileDialog, QMessageBox, QInputDialog
)
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from datetime import datetime
import pandas as pd
import os

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

        # --- Live Replay Timer ---
        self.replay_timer = QTimer(self)
        self.replay_timer.timeout.connect(self._on_replay_tick)
        self.replay_data = []
        self.replay_index = 0
        self.replay_df = None # Simpan DataFrame asli untuk prediksi akhir

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20) # Jarak antar panel kiri & kanan
        
        # --- Left Panel (Visual Data) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(15)
        
        # 1. Header Data (Environment) - Kita ubah EnvWidget jadi Horizontal di dalamnya
        # Karena EnvironmentWidget aslinya Vertical, kita taruh dia di layout horizontal container kalau mau
        # Tapi ide EnvironmentWidget di kanan bawah itu lama.
        # Mari kita taruh Env Widget di ATAS Grafik.
        
        # Agar EnvWidget berjejer horizontal, kita perlu modifikasi sedikit EnvironmentWidget (sudah dilakukan di step sebelumnya? 
        # Oh wait, di kode EnvironmentWidget saya tadi buatnya Vertical Layout (layout = QVBoxLayout(self)). 
        # SAYA PERLU UBAH EnvironmentWidget JADI HORIZONTAL DULU BIAR BAGUS DI ATAS.
        
        left_layout.addWidget(self.environment_widget) # Nanti kita ubah jadi horizontal
        left_layout.addWidget(self.graph_widget)
        
        # --- Right Panel (Control & Result) ---
        right_panel = QWidget()
        right_panel.setFixedWidth(320) # Lebih lebar biar Result enak dilihat
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(15)
        
        right_layout.addWidget(self.result_widget) # Result paling atas biar kelihatan
        
        # Tombol Save Dataset (Labeling)
        self.btn_save_dataset = QPushButton("💾 Simpan ke Dataset (Labeling)")
        self.btn_save_dataset.clicked.connect(self.save_to_dataset)
        self.btn_save_dataset.setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold; padding: 8px;")
        self.btn_save_dataset.hide() # Sembunyikan default
        right_layout.addWidget(self.btn_save_dataset)
        
        # Container untuk kontrol
        controls_box = QGroupBox("Control Center")
        controls_layout = QVBoxLayout(controls_box)
        controls_layout.setSpacing(10)
        
        controls_layout.addWidget(self.device_control)
        controls_layout.addWidget(self.model_control)
        
        # Settings Time
        settings_layout = QHBoxLayout()
        lbl_durasi = QLabel("Durasi Deteksi:")
        lbl_durasi.setStyleSheet("font-weight: bold;")
        
        self.duration_spinbox.setRange(5, 300) # Bisa sampai 300 detik (5 menit)
        self.duration_spinbox.setValue(15)
        self.duration_spinbox.setSuffix(" Detik") # Keterangan lebih jelas
        self.duration_spinbox.setFixedWidth(120)
        
        settings_layout.addWidget(lbl_durasi)
        settings_layout.addWidget(self.duration_spinbox)
        controls_layout.addLayout(settings_layout)

        # Tombol Analisis CSV
        self.btn_csv = QPushButton("📂 Analisis File CSV")
        self.btn_csv.clicked.connect(self.analyze_file)
        self.btn_csv.setStyleSheet("background-color: #64748B; color: white; font-weight: bold;")
        controls_layout.addWidget(self.btn_csv)
        
        right_layout.addWidget(controls_box)
        
        # Tombol Start Paling Bawah Besar
        self.start_button.setMinimumHeight(60)
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        right_layout.addWidget(self.start_button)
        right_layout.addStretch()

        main_layout.addWidget(left_panel, 1) # Left panel expand
        main_layout.addWidget(right_panel)

        self.start_button.setEnabled(False)
        # Styling Tombol Start
        self.start_button.setStyleSheet("""
            QPushButton { 
                background-color: #2563EB; 
                color: white; 
                border: none; 
                border-radius: 10px; 
                font-size: 18px; 
                font-weight: bold; 
                letter-spacing: 1px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:disabled { background-color: #334155; color: #64748B; }
        """)

    def connect_signals(self):
        self.device_control.connection_status_changed.connect(self.on_connection_status_changed)
        self.device_control.data_received.connect(self.on_data_received)
        self.model_control.model_loaded.connect(self.on_model_loaded)
        self.start_button.clicked.connect(self.toggle_detection)

    def save_to_dataset(self):
        if not self.data_buffer:
            QMessageBox.warning(self, "Kosong", "Tidak ada data buffer untuk disimpan!")
            return

        # 1. Minta Nama Label (Folder)
        label, ok = QInputDialog.getText(self, "Labeling Data", "Masukkan Nama Label/Zat (Folder):")
        if not ok or not label.strip():
            return
            
        # Bersihkan nama folder
        safe_label = "".join([c for c in label if c.isalpha() or c.isdigit() or c==' ']).strip()
        
        # 2. Buat Folder
        base_path = "sample_data"
        target_dir = os.path.join(base_path, safe_label)
        
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Gagal membuat folder: {e}")
                return
        
        # 3. Simpan CSV
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{safe_label}_{timestamp}.csv"
        filepath = os.path.join(target_dir, filename)
        
        try:
            # Header Sensor + Env
            header = "MQ2;MQ3;MQ4;MQ6;MQ7;MQ8;MQ135;QCM;Temp;Hum;Pres"
            
            with open(filepath, 'w') as f:
                f.write(header + "\n")
                for line in self.data_buffer:
                    # Ubah koma jadi titik koma (standar CSV kita)
                    # Dan pastikan angka pakai koma desimal jika perlu, tapi standar kita titik
                    # Data buffer kita formatnya: "val,val,val" (koma separated, titik decimal)
                    # Kita ubah jadi ";" separated
                    f.write(line.replace(',', ';') + "\n")
                    
            QMessageBox.information(self, "Sukses", f"Data berhasil disimpan ke:\n{filepath}")
            self.btn_save_dataset.hide() # Sembunyikan setelah save
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menyimpan file: {e}")

    def analyze_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih File CSV Data", "", "CSV Files (*.csv);;All Files (*)")
        
        if not file_path:
            return

        try:
            # Baca CSV
            df = pd.read_csv(file_path, sep=';', decimal=',')
            if df.shape[1] < 3: 
                df = pd.read_csv(file_path, sep=',', decimal='.')
            
            if df.empty:
                QMessageBox.warning(self, "Error", "File kosong atau format salah!")
                return

            # --- SETUP REPLAY ---
            # Normalisasi Header agar mudah akses kolom
            df.columns = df.columns.str.strip().str.upper().str.replace(' ', '')
            
            self.replay_df = df # Simpan untuk prediksi nanti
            self.replay_data = []
            
            # Convert DataFrame ke List of dict untuk iterasi cepat
            # Kita perlu ekstrak 8 sensor + 3 env (jika ada)
            sensors = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']
            envs = ['TEMP', 'HUM', 'PRES'] # Asumsi nama kolom environment
            
            for _, row in df.iterrows():
                # Ambil data sensor
                vals = []
                for s in sensors:
                    vals.append(row.get(s, 0.0))
                
                # Ambil data env (fallback ke 0 jika gak ada)
                # Coba berbagai variasi nama kolom env umum
                t = row.get('TEMP', row.get('TEMPERATURE', row.get('SUHU', 0.0)))
                h = row.get('HUM', row.get('HUMIDITY', row.get('KELEMBABAN', 0.0)))
                p = row.get('PRES', row.get('PRESSURE', row.get('TEKANAN', 0.0)))
                
                self.replay_data.append({
                    'sensors': vals,
                    'env': [t, h, p]
                })

            # UI State Update
            self.btn_csv.setEnabled(False)
            self.btn_csv.setText("⏹ Stop Replay")
            self.start_button.setEnabled(False)
            
            # Reset Grafik
            self.graph_widget.reset()
            self.result_widget.reset()
            self.result_widget.set_collecting_state(len(self.replay_data) * 0.05) # Estimasi waktu visual
            
            # Mulai Timer (Speed: 50ms per data point = 20Hz)
            self.replay_index = 0
            self.replay_timer.start(50)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal membaca file:\n{str(e)}")

    def _on_replay_tick(self):
        if self.replay_index >= len(self.replay_data):
            self._finish_csv_analysis()
            return

        # Ambil data frame saat ini
        frame = self.replay_data[self.replay_index]
        
        # Update UI
        self.graph_widget.update_plot(frame['sensors'])
        self.environment_widget.update_values(*frame['env'])
        
        # Update Progress Bar di Result Widget (biar gak diam)
        self.result_widget.set_progress_value(self.replay_index * 50)
        
        self.replay_index += 1

    def _finish_csv_analysis(self):
        self.replay_timer.stop()
        self.btn_csv.setEnabled(True)
        self.btn_csv.setText("📂 Analisis File CSV")
        self.update_start_button_state()

        try:
            # Lakukan Prediksi Final
            whitelist = self.model_control.get_voting_whitelist()
            result_label, confidence, details = self.predictor.predict_from_dataframe(self.replay_df, whitelist)
            
            # Tampilkan Hasil
            self.result_widget.set_result(result_label, confidence, details)
            
            # Opsional: Tampilkan popup ringkasan
            # QMessageBox.information(self, "Selesai", f"Replay Selesai.\nHasil: {result_label}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal analisis akhir:\n{e}")

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
        print(f"DEBUG: Data string received: '{data_string}'") 
        try:
            sensor_values = [float(x.strip()) for x in data_string.split(',')]
            
            # Toleransi jumlah data:
            # Jika data kurang dari 11, kita pad dengan 0.
            # Jika data lebih dari 11, kita potong.
            if len(sensor_values) < TOTAL_EXPECTED_VALUES:
                print(f"DEBUG: Data kurang ({len(sensor_values)}), padding dengan 0.")
                sensor_values.extend([0.0] * (TOTAL_EXPECTED_VALUES - len(sensor_values)))
            elif len(sensor_values) > TOTAL_EXPECTED_VALUES:
                print(f"DEBUG: Data berlebih ({len(sensor_values)}), memotong data.")
                sensor_values = sensor_values[:TOTAL_EXPECTED_VALUES]

            graph_values = sensor_values[:NUM_GRAPH_SENSORS]
            bme_values = sensor_values[NUM_GRAPH_SENSORS:]
            
            # Pastikan bme_values punya minimal 3 data (Temp, Hum, Pres)
            # Jika tidak ada, isi default 0
            t = bme_values[0] if len(bme_values) > 0 else 0
            h = bme_values[1] if len(bme_values) > 1 else 0
            p = bme_values[2] if len(bme_values) > 2 else 0
            
            self.graph_widget.update_plot(graph_values)
            self.environment_widget.update_values(t, h, p)
            
            if self.is_detecting:
                self.data_buffer.append(data_string)

        except (ValueError, IndexError) as e:
            print(f"DEBUG: Parsing error in on_data_received for '{data_string}': {e}")
            pass 

    def toggle_detection(self):
        # Safety: Matikan Replay jika ada
        if self.replay_timer.isActive():
            self.replay_timer.stop()
            self.btn_csv.setEnabled(True)
            self.btn_csv.setText("📂 Analisis File CSV")

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
            self.btn_save_dataset.hide() # Sembunyikan tombol save saat mulai baru
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
            
            # Hitung Sisa Waktu untuk Countdown
            max_val = self.result_widget.progress_bar.maximum()
            remaining = max_val - current_value
            if remaining < 0: remaining = 0
            self.result_widget.update_countdown(remaining)

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

        # --- ENSEMBLE PREDICTION ---
        # Ambil whitelist dari control panel
        whitelist = self.model_control.get_voting_whitelist()
        
        # Kita panggil 'predict_all_models' untuk dapat voting
        result_label, confidence, details = self.predictor.predict_all_models(self.data_buffer, whitelist)
        
        self.result_widget.set_result(result_label, confidence, details)
        self._save_record(f"{result_label} ({confidence:.0f}%)", self.data_buffer)
            
        self.start_button.setText("Mulai Deteksi")
        self.update_start_button_state()
        
        # Tampilkan tombol Save Dataset
        self.btn_save_dataset.show()
    
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