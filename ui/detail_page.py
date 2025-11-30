import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QTableWidget, 
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QPushButton,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
import numpy as np

from database.database import create_connection, get_record_by_id

class DetailPage(QDialog):
    def __init__(self, record_id, parent=None):
        super().__init__(parent)
        self.record_id = record_id
        self.setWindowTitle(f"Detail Rekaman #{self.record_id}")
        self.setMinimumSize(900, 600)
        
        # Layout Utama
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- HEADER INFO ---
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #F1F5F9; border-radius: 10px; padding: 10px;")
        header_layout = QHBoxLayout(header_frame)
        
        self.lbl_id = QLabel(f"ID: #{record_id}")
        self.lbl_id.setStyleSheet("font-weight: bold; font-size: 16px; color: #475569;")
        
        self.lbl_time = QLabel("Waktu: --")
        self.lbl_time.setStyleSheet("font-size: 14px;")
        
        self.lbl_result = QLabel("Hasil: --")
        self.lbl_result.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        header_layout.addWidget(self.lbl_id)
        header_layout.addSpacing(20)
        header_layout.addWidget(self.lbl_time)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_result)
        
        layout.addWidget(header_frame)

        # --- GRAFIK REKAMAN ---
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        self.graph_widget.addLegend(offset=(10, 10))
        self.graph_widget.setMouseEnabled(x=True, y=True)
        
        # Styling Axis
        styles = {'color': '#334155', 'font-size': '10px'}
        self.graph_widget.getAxis('left').setPen('#334155')
        self.graph_widget.getAxis('bottom').setPen('#334155')
        
        layout.addWidget(QLabel("📈 Grafik Rekaman Sensor:"))
        layout.addWidget(self.graph_widget, 2) # Expand

        # --- TABEL STATISTIK ---
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(9) # 8 Gas + 1 Avg
        self.stats_table.setHorizontalHeaderLabels(['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM', 'Status'])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.setFixedHeight(100)
        self.stats_table.setStyleSheet("QTableWidget { background-color: white; border: 1px solid #CBD5E1; }")
        
        layout.addWidget(QLabel("📊 Statistik Rata-rata:"))
        layout.addWidget(self.stats_table)
        
        # --- LOAD DATA ---
        self._load_data()

    def _load_data(self):
        conn = create_connection()
        if not conn: return
        
        record = get_record_by_id(conn, self.record_id)
        conn.close()

        if not record:
            QMessageBox.warning(self, "Error", "Data tidak ditemukan.")
            return

        # Unpack data: id, timestamp, result, raw_data
        _, timestamp, result, raw_data_str = record
        
        self.lbl_time.setText(f"🕒 {timestamp}")
        
        # Style Result
        if "Terdeteksi" in result:
            self.lbl_result.setText(f"🔴 {result}")
            self.lbl_result.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 16px;")
        else:
            self.lbl_result.setText(f"🟢 {result}")
            self.lbl_result.setStyleSheet("color: #10B981; font-weight: bold; font-size: 16px;")

        # Parse Raw Data
        if not raw_data_str: return

        try:
            # Raw data format: "val1,val2,..." (separated by newlines)
            # Kita harus handle newline literal jika tersimpan sebagai text "\n"
            raw_rows = raw_data_str.replace('\\n', '\n').split('\n')
            
            data_matrix = []
            for row in raw_rows:
                if not row.strip(): continue
                vals = [float(x) for x in row.split(',') if x.strip()]
                # Ambil 8 sensor gas pertama
                if len(vals) >= 8:
                    data_matrix.append(vals[:8])
            
            if not data_matrix: return
            
            # --- Plot Grafik ---
            sensor_names = ["MQ-2", "MQ-3", "MQ-4", "MQ-6", "MQ-7", "MQ-8", "MQ-135", "QCM"]
            colors = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#06B6D4', '#F97316', '#EC4899']
            
            # Transpose matrix untuk plotting per sensor
            np_data = np.array(data_matrix)
            
            for i in range(8):
                color = colors[i]
                pen = pg.mkPen(color=color, width=2)
                self.graph_widget.plot(np_data[:, i], pen=pen, name=sensor_names[i])

            # --- Isi Tabel Statistik ---
            self.stats_table.setRowCount(1)
            means = np.mean(np_data, axis=0)
            
            for i in range(8):
                item = QTableWidgetItem(f"{means[i]:.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.stats_table.setItem(0, i, item)
            
            status_item = QTableWidgetItem("Valid")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stats_table.setItem(0, 8, status_item)

        except Exception as e:
            print(f"Error parsing detail: {e}")
            QMessageBox.warning(self, "Error Data", "Format data rusak/tidak kompatibel.")