import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QTableWidget, 
    QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt

from database.database import create_connection, get_record_by_id

class DetailPage(QDialog):
    def __init__(self, record_id, parent=None):
        super().__init__(parent)
        self.record_id = record_id
        self.setWindowTitle(f"Detail for Record #{self.record_id}")
        self.setMinimumSize(800, 600)
        self.setModal(True) # Block interaction with the main window

        # --- Layouts ---
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout() # For summary info
        bottom_layout = QHBoxLayout() # For graph and table
        
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        # --- UI Components ---
        self.title_label = QLabel(f"Detail Record #{self.record_id}")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #1E3A8A;")
        
        self.timestamp_label = QLabel("Timestamp: --")
        self.result_label = QLabel("Result: --")
        
        self.graph_widget = pg.PlotWidget()
        self.data_table = QTableWidget()

        # --- Setup UI ---
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.timestamp_label)
        top_layout.addSpacing(20)
        top_layout.addWidget(self.result_label)

        bottom_layout.addWidget(self.graph_widget, 2) # Graph takes 2/3 of space
        bottom_layout.addWidget(self.data_table, 1) # Table takes 1/3 of space

        self._configure_widgets()
        self._load_and_display_data()

    def _configure_widgets(self):
        # Graph configuration
        self.graph_widget.setBackground('w')
        self.graph_widget.setTitle("Sensor Readings", color="#1E3A8A", size="16pt")
        styles = {'color':'#1E3A8A', 'font-size':'12pt'}
        self.graph_widget.setLabel('left', 'Sensor Value', **styles)
        self.graph_widget.setLabel('bottom', 'Time (sample)', **styles)
        self.graph_widget.addLegend()
        self.graph_widget.showGrid(x=True, y=True)
        
        # Table configuration
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.verticalHeader().setVisible(False)
        self.data_table.setAlternatingRowColors(True)

    def _load_and_display_data(self):
        conn = create_connection()
        if not conn:
            self.title_label.setText("Error: Could not connect to database.")
            return
        
        record = get_record_by_id(conn, self.record_id)
        conn.close()

        if not record:
            self.title_label.setText(f"Error: Record #{self.record_id} not found.")
            return

        # record = (id, timestamp, result, raw_data)
        _id, timestamp, result, raw_data_str = record
        
        self.timestamp_label.setText(f"<b>Timestamp:</b> {timestamp}")
        self.result_label.setText(f"<b>Result:</b> {result}")
        
        if not raw_data_str:
            # Handle cases where there's no raw data
            return

        # --- Parse and Process Data ---
        try:
            lines = raw_data_str.split('\n')
            sensor_names = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM', 'Temp', 'Hum', 'Press']
            parsed_data = []
            for line in lines:
                if line:
                    parsed_data.append([float(x) for x in line.split(',')])

            # --- Populate Graph ---
            num_graph_sensors = 8 # Only graph the gas sensors
            colors = ['#E53935', '#1E88E5', '#43A047', '#FDD835', '#FB8C00', '#8E24AA', '#00897B', '#D81B60']
            for i in range(num_graph_sensors):
                sensor_data = [row[i] for row in parsed_data]
                pen = pg.mkPen(color=colors[i % len(colors)], width=2)
                self.graph_widget.plot(sensor_data, pen=pen, name=sensor_names[i])
            
            # --- Populate Table ---
            self.data_table.setColumnCount(len(sensor_names))
            self.data_table.setHorizontalHeaderLabels(sensor_names)
            self.data_table.setRowCount(len(parsed_data))

            for row_idx, row_data in enumerate(parsed_data):
                for col_idx, cell_data in enumerate(row_data):
                    self.data_table.setItem(row_idx, col_idx, QTableWidgetItem(f"{cell_data:.2f}"))
            
            self.data_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error parsing or displaying data for record #{self.record_id}: {e}")
            # Optionally show an error in the UI
