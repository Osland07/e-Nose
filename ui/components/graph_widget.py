from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGraphicsEllipseItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QLinearGradient
import pyqtgraph as pg
import numpy as np

# --- Configuration ---
NUM_GRAPH_SENSORS = 8
MAX_DATA_POINTS = 100

class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout Container
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Frame Pembungkus
        self.container = QFrame()
        self.container.setObjectName("GraphContainer")
        self.container.setStyleSheet("""
            QFrame#GraphContainer {
                background-color: white; 
                border-radius: 15px;
                border: 1px solid #CBD5E1; 
            }
        """)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 15, 15, 15)

        # --- HEADER (Title + View Controls) ---
        header_layout = QHBoxLayout()
        
        title = QLabel("MONITOR DATA SENSOR")
        title.setStyleSheet("color: #475569; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        
        # Group Tombol Style
        style_group = QFrame()
        style_group.setStyleSheet(".QFrame { background-color: #F1F5F9; border-radius: 6px; border: 1px solid #E2E8F0; }")
        style_layout = QHBoxLayout(style_group)
        style_layout.setContentsMargins(2, 2, 2, 2)
        style_layout.setSpacing(2)
        
        def create_style_btn(text, icon, mode_idx):
            btn = QPushButton(f"{icon} {text}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setAutoExclusive(True) 
            btn.setFixedHeight(24)
            if mode_idx == 0: btn.setChecked(True) 
            
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

        self.btn_line = create_style_btn("Line", "📈", 0)
        self.btn_area = create_style_btn("Area", "⛰️", 1)
        self.btn_dots = create_style_btn("Dots", "∴", 2)
        self.btn_radar = create_style_btn("Radar", "🕸️", 3)
        
        style_layout.addWidget(self.btn_line)
        style_layout.addWidget(self.btn_area)
        style_layout.addWidget(self.btn_dots)
        style_layout.addWidget(self.btn_radar)
        
        self.reset_btn = QPushButton("↺ Reset")
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

        # --- PYQTGRAPH SETUP ---
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w') 
        
        styles = {'color': '#334155', 'font-size': '10px'}
        self.graph_widget.getAxis('left').setPen('#334155')
        self.graph_widget.getAxis('bottom').setPen('#334155')
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3) 
        
        self.graph_widget.setMouseEnabled(x=True, y=True) 
        self.graph_widget.hideButtons() 

        self.legend = self.graph_widget.addLegend(offset=(10, 10))
        self.legend.setBrush(QColor(255, 255, 255, 150)) 
        self.legend.setLabelTextColor("#000000") 

        container_layout.addWidget(self.graph_widget)
        layout.addWidget(self.container)

        # Data Storage
        self.y_data = [[] for _ in range(NUM_GRAPH_SENSORS)]
        self.plot_lines = []
        self.fill_items = [] 
        self.graph_mode = 0
        
        # Pastikan method ini dipanggil dan ADA
        self._setup_graph_lines()

    def set_graph_mode(self, mode):
        self.graph_mode = mode
        self.refresh_graph_style()

    def reset_view(self):
        self.graph_widget.enableAutoRange()

    def refresh_graph_style(self):
        self.graph_widget.clear()
        self.plot_lines = []
        
        # Radar Mode Config
        if self.graph_mode == 3:
            self.graph_widget.setAspectLocked(True)
            self.graph_widget.showGrid(x=False, y=False)
            self.graph_widget.hideAxis('bottom')
            self.graph_widget.hideAxis('left')
            self._draw_radar_grid()
        else:
            self.graph_widget.setAspectLocked(False)
            self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
            self.graph_widget.showAxis('bottom')
            self.graph_widget.showAxis('left')

        sensor_names = ["MQ-2", "MQ-3", "MQ-4", "MQ-6", "MQ-7", "MQ-8", "MQ-135", "QCM"]
        colors = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#06B6D4', '#F97316', '#EC4899']
        
        if self.graph_mode == 3:
            # Placeholder Radar Logic 
            pass
            
        else:
            for i in range(NUM_GRAPH_SENSORS):
                color = colors[i % len(colors)]
                if self.graph_mode == 0: # Line
                    pen = pg.mkPen(color=color, width=2)
                    line = self.graph_widget.plot([], [], pen=pen, name=sensor_names[i])
                elif self.graph_mode == 1: # Area
                    pen = pg.mkPen(color=color, width=1)
                    base = self.graph_widget.plot([], [], pen=None)
                    line = self.graph_widget.plot([], [], pen=pen, name=sensor_names[i])
                    fill = pg.FillBetweenItem(curve1=line, curve2=base, brush=QColor(color + "40"))
                    self.graph_widget.addItem(fill)
                elif self.graph_mode == 2: # Dots
                    line = self.graph_widget.plot([], [], pen=None, symbol='o', symbolBrush=color, symbolSize=6, name=sensor_names[i])
                
                self.plot_lines.append(line)
        
        # Restore data view
        if self.graph_mode != 3:
            for i in range(NUM_GRAPH_SENSORS):
                if len(self.y_data[i]) > 0:
                    self.plot_lines[i].setData(list(range(len(self.y_data[i]))), self.y_data[i])

    def _draw_radar_grid(self):
        # Simple circles
        for r in [20, 40, 60, 80, 100]:
            circle = QGraphicsEllipseItem(-r, -r, r*2, r*2)
            circle.setPen(pg.mkPen('#CBD5E1', width=1, style=Qt.PenStyle.DashLine))
            self.graph_widget.addItem(circle)
        
        # Spokes
        angles = np.linspace(0, 2*np.pi, NUM_GRAPH_SENSORS, endpoint=False)
        sensor_labels = ["MQ-2", "MQ-3", "MQ-4", "MQ-6", "MQ-7", "MQ-8", "MQ-135", "QCM"]
        
        for i, ang in enumerate(angles):
            x = 100 * np.cos(ang)
            y = 100 * np.sin(ang)
            self.graph_widget.plot([0, x], [0, y], pen=pg.mkPen('#CBD5E1', width=1))
            
            # Add Labels 
            lbl_x = 110 * np.cos(ang)
            lbl_y = 110 * np.sin(ang)
            text = pg.TextItem(sensor_labels[i], color='#475569', anchor=(0.5, 0.5))
            text.setPos(lbl_x, lbl_y)
            self.graph_widget.addItem(text)

    def update_plot(self, graph_values):
        if len(graph_values) != NUM_GRAPH_SENSORS: return

        for i in range(NUM_GRAPH_SENSORS):
            self.y_data[i].append(graph_values[i])
            if len(self.y_data[i]) > MAX_DATA_POINTS: self.y_data[i].pop(0)

        if self.graph_mode == 3:
            # Update Radar Polygon
            for item in self.plot_lines: self.graph_widget.removeItem(item)
            self.plot_lines.clear()
            
            angles = np.linspace(0, 2*np.pi, NUM_GRAPH_SENSORS, endpoint=False)
            angles = np.append(angles, angles[0])
            
            vals = []
            # Auto-scale radar values 
            max_val = max(graph_values) if max(graph_values) > 0 else 1
            scale_factor = 100.0 / (max_val if max_val < 1000 else 1000) 
            
            for v in graph_values:
                vals.append(min(v * scale_factor, 100))
            vals.append(vals[0])
            
            x = vals * np.cos(angles)
            y = vals * np.sin(angles)
            
            pen = pg.mkPen(color='#3B82F6', width=2)
            poly = self.graph_widget.plot(x, y, pen=pen, fillLevel=0.2, brush=QColor(59, 130, 246, 100))
            self.plot_lines.append(poly)
            
        else:
            for i in range(NUM_GRAPH_SENSORS):
                self.plot_lines[i].setData(list(range(len(self.y_data[i]))), self.y_data[i])

    # --- INI DIA FUNGSI YANG HILANG TADI ---
    def _setup_graph_lines(self):
        self.graph_mode = 0
        self.refresh_graph_style()

    def reset(self):
        self.y_data = [[] for _ in range(NUM_GRAPH_SENSORS)]
        self.refresh_graph_style()