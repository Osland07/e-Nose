from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QLinearGradient
import pyqtgraph as pg

# --- Configuration ---
NUM_GRAPH_SENSORS = 8
MAX_DATA_POINTS = 100 # Kurangi dikit biar lebih responsif/zoom-in

class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout Container
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Frame Pembungkus (Biar ada border radius)
        self.container = QFrame()
        self.container.setObjectName("GraphContainer")
        self.container.setStyleSheet("""
            QFrame#GraphContainer {
                background-color: white; 
                border-radius: 15px;
                border: 1px solid #CBD5E1; /* Slate-300 */
            }
        """)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 15, 15, 15)

        # --- HEADER (Title + View Controls) ---
        header_layout = QHBoxLayout()
        
        title = QLabel("MONITOR DATA SENSOR")
        title.setStyleSheet("color: #475569; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        
        # Group Tombol Style (Segmented Control)
        style_group = QFrame()
        style_group.setStyleSheet(".QFrame { background-color: #F1F5F9; border-radius: 6px; border: 1px solid #E2E8F0; }")
        style_layout = QHBoxLayout(style_group)
        style_layout.setContentsMargins(2, 2, 2, 2)
        style_layout.setSpacing(2)
        
        def create_style_btn(text, icon, mode_idx):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setAutoExclusive(True) # Biar cuma 1 yg aktif
            btn.setFixedHeight(24)
            if mode_idx == 0: btn.setChecked(True) # Default Line
            
            # Style khusus state checked
            btn.setStyleSheet("""
                QPushButton {
                    border: none; border-radius: 4px; color: #64748B; font-size: 10px; font-weight: 600; padding: 0 8px;
                }
                QPushButton:checked {
                    background-color: white; color: #2563EB; border: 1px solid #CBD5E1;
                }
                QPushButton:hover:!checked {
                    background-color: #E2E8F0;
                }
            """)
            btn.clicked.connect(lambda: self.set_graph_mode(mode_idx))
            return btn

import numpy as np # Butuh numpy untuk hitung sin/cos

# ...

        self.btn_line = create_style_btn("Garis", "📈", 0)
        self.btn_area = create_style_btn("Area", "⛰️", 1)
        self.btn_dots = create_style_btn("Titik", "∴", 2)
        self.btn_radar = create_style_btn("Radar", "🕸️", 3) # New Mode
        
        style_layout.addWidget(self.btn_line)
        style_layout.addWidget(self.btn_area)
        style_layout.addWidget(self.btn_dots)
        style_layout.addWidget(self.btn_radar)

# ...

    def refresh_graph_style(self):
        self.graph_widget.clear()
        self.plot_lines = []
        
        # Reset View (Normal vs Polar)
        if self.graph_mode == 3: # Radar Mode
            self.graph_widget.setAspectLocked(True)
            self.graph_widget.showGrid(x=False, y=False)
            self.graph_widget.hideAxis('bottom')
            self.graph_widget.hideAxis('left')
            self._draw_radar_grid() # Gambar jaring laba-laba
        else:
            self.graph_widget.setAspectLocked(False)
            self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
            self.graph_widget.showAxis('bottom')
            self.graph_widget.showAxis('left')

        sensor_names = ["MQ-2", "MQ-3", "MQ-4", "MQ-6", "MQ-7", "MQ-8", "MQ-135", "QCM"]
        colors = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#06B6D4', '#F97316', '#EC4899']
        
        if self.graph_mode == 3: # RADAR PLOT LOGIC
            # Kita gambar polygon statis sebagai placeholder
            # Update real-time radar agak kompleks, kita buat visualisasi simple
            # Tiap sensor punya sudut tertentu (0, 45, 90...)
            pass 
            
        else:
            # MODE 0, 1, 2 (Time Series)
            for i in range(NUM_GRAPH_SENSORS):
                color = colors[i % len(colors)]
                if self.graph_mode == 0:
                    pen = pg.mkPen(color=color, width=2)
                    line = self.graph_widget.plot([], [], pen=pen, name=sensor_names[i])
                elif self.graph_mode == 1:
                    pen = pg.mkPen(color=color, width=1)
                    base = self.graph_widget.plot([], [], pen=None)
                    line = self.graph_widget.plot([], [], pen=pen, name=sensor_names[i])
                    fill = pg.FillBetweenItem(curve1=line, curve2=base, brush=QColor(color + "40"))
                    self.graph_widget.addItem(fill)
                elif self.graph_mode == 2:
                    line = self.graph_widget.plot([], [], pen=None, symbol='o', symbolBrush=color, symbolSize=6)
                
                self.plot_lines.append(line)

    def _draw_radar_grid(self):
        # Gambar lingkaran grid
        for r in [20, 40, 60, 80, 100]:
            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r*2, r*2)
            circle.setPen(pg.mkPen('#334155', width=1, style=Qt.PenStyle.DashLine))
            self.graph_widget.addItem(circle)
        
        # Gambar garis jari-jari
        angles = np.linspace(0, 2*np.pi, NUM_GRAPH_SENSORS, endpoint=False)
        for ang in angles:
            x = 100 * np.cos(ang)
            y = 100 * np.sin(ang)
            self.graph_widget.plot([0, x], [0, y], pen=pg.mkPen('#334155', width=1))

    def update_plot(self, graph_values):
        if len(graph_values) != NUM_GRAPH_SENSORS: return

        # Update Data Storage
        for i in range(NUM_GRAPH_SENSORS):
            self.y_data[i].append(graph_values[i])
            if len(self.y_data[i]) > MAX_DATA_POINTS: self.y_data[i].pop(0)

        # Render
        if self.graph_mode == 3:
            # Update Radar Polygon
            # Clear previous polygon
            for item in self.plot_lines: self.graph_widget.removeItem(item)
            self.plot_lines.clear()
            
            # Convert values to polar coordinates
            angles = np.linspace(0, 2*np.pi, NUM_GRAPH_SENSORS, endpoint=False)
            # Tambahkan titik awal di akhir agar loop tertutup
            angles = np.append(angles, angles[0])
            
            # Normalize values (assuming max 1000, scale to 100 radius)
            vals = []
            for v in graph_values:
                norm_v = min(v / 10.0, 100) # Scale down simple logic
                vals.append(norm_v)
            vals.append(vals[0]) # Close loop
            
            x = vals * np.cos(angles)
            y = vals * np.sin(angles)
            
            # Draw Polygon
            pen = pg.mkPen(color='#3B82F6', width=2)
            poly = self.graph_widget.plot(x, y, pen=pen, fillLevel=0.2, brush=QColor(59, 130, 246, 100))
            self.plot_lines.append(poly)
            
        else:
            # Normal Update
            for i in range(NUM_GRAPH_SENSORS):
                self.plot_lines[i].setData(list(range(len(self.y_data[i]))), self.y_data[i])
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setToolTip("Reset Zoom")
        self.reset_btn.setFixedWidth(60)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: white; color: #475569; border: 1px solid #CBD5E1;
                border-radius: 6px; padding: 4px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #F8FAFC; }
        """)
        self.reset_btn.clicked.connect(self.reset_view)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(style_group)
        header_layout.addSpacing(5)
        header_layout.addWidget(self.reset_btn)
        
        container_layout.addLayout(header_layout)

    def set_graph_mode(self, mode):
        self.graph_mode = mode
        self.refresh_graph_style()

    def refresh_graph_style(self):
        """Apply style based on current self.graph_mode"""
        # Clear old fills/items
        self.graph_widget.clear()
        self.plot_lines = []
        
        sensor_names = ["MQ-2", "MQ-3", "MQ-4", "MQ-6", "MQ-7", "MQ-8", "MQ-135", "QCM"]
        colors = [
            '#EF4444', '#3B82F6', '#10B981', '#F59E0B', 
            '#8B5CF6', '#06B6D4', '#F97316', '#EC4899'
        ]
        
        for i in range(NUM_GRAPH_SENSORS):
            color = colors[i % len(colors)]
            
            if self.graph_mode == 0: # LINE
                pen = pg.mkPen(color=color, width=2)
                line = self.graph_widget.plot([0], [0], pen=pen, name=sensor_names[i])
                self.plot_lines.append(line)

            elif self.graph_mode == 1: # AREA
                pen = pg.mkPen(color=color, width=1)
                base = self.graph_widget.plot([0], [0], pen=None) 
                line = self.graph_widget.plot([0], [0], pen=pen, name=sensor_names[i])
                fill = pg.FillBetweenItem(curve1=line, curve2=base, brush=QColor(color + "40"))
                self.graph_widget.addItem(fill)
                self.plot_lines.append(line)

            elif self.graph_mode == 2: # DOTS
                line = self.graph_widget.plot([0], [0], pen=None, symbol='o', symbolBrush=color, symbolSize=6, name=sensor_names[i])
                self.plot_lines.append(line)
        
        # Repaint data
        for i in range(NUM_GRAPH_SENSORS):
            if len(self.y_data[i]) > 0:
                self.plot_lines[i].setData(list(range(len(self.y_data[i]))), self.y_data[i])

    def toggle_graph_style(self):
        pass # Deprecated

    def _setup_graph_lines(self):
        self.graph_mode = 0
        self.refresh_graph_style()

    def update_plot(self, graph_values):
        if len(graph_values) != NUM_GRAPH_SENSORS:
            return

        for i in range(NUM_GRAPH_SENSORS):
            self.y_data[i].append(graph_values[i])
            
            # Limit Data Points (Scrolling effect)
            if len(self.y_data[i]) > MAX_DATA_POINTS:
                self.y_data[i].pop(0)
            
            # Update Garis
            self.plot_lines[i].setData(list(range(len(self.y_data[i]))), self.y_data[i])
            
            # Update Fills jika mode area aktif (perlu reset curve2 base ke 0)
            # (PyQtGraph handle fill update otomatis as long as curve references stay valid)

    def update_plot(self, graph_values):
        if len(graph_values) != NUM_GRAPH_SENSORS:
            return

        for i in range(NUM_GRAPH_SENSORS):
            self.y_data[i].append(graph_values[i])
            
            # Limit Data Points (Scrolling effect)
            if len(self.y_data[i]) > MAX_DATA_POINTS:
                self.y_data[i].pop(0)
            
            # Update Garis
            self.plot_lines[i].setData(list(range(len(self.y_data[i]))), self.y_data[i])

    def reset(self):
        self.y_data = [[] for _ in range(NUM_GRAPH_SENSORS)]
        for i in range(NUM_GRAPH_SENSORS):
            self.plot_lines[i].setData([0], [0])