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

        # --- HEADER (Title + Reset Button) ---
        header_layout = QHBoxLayout()
        
        title = QLabel("MONITOR DATA SENSOR (REAL-TIME)")
        title.setStyleSheet("color: #475569; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        
        # Tombol Ganti Style
        self.style_btn = QPushButton("🎨 Style")
        self.style_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.style_btn.setFixedWidth(60)
        self.style_btn.setStyleSheet("background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 4px;")
        self.style_btn.clicked.connect(self.toggle_graph_style)

        self.reset_btn = QPushButton("↺ Reset View")
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setToolTip("Kembalikan grafik ke posisi otomatis")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #E2E8F0;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        self.reset_btn.clicked.connect(self.reset_view)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.style_btn)
        header_layout.addWidget(self.reset_btn)
        
        container_layout.addLayout(header_layout)

        # --- PYQTGRAPH SETUP ---
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w') # 'w' = White background
        
        # Styling Axis (Sumbu) - Warna gelap untuk background terang
        styles = {'color': '#334155', 'font-size': '10px'}
        self.graph_widget.getAxis('left').setPen('#334155')
        self.graph_widget.getAxis('bottom').setPen('#334155')
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3) 
        
        # AKTIFKAN INTERAKSI MOUSE (Geser & Zoom)
        self.graph_widget.setMouseEnabled(x=True, y=True) 
        self.graph_widget.hideButtons() # Sembunyikan tombol 'A' bawaan yg jelek

        # Add Legend (Keterangan Warna)
        self.legend = self.graph_widget.addLegend(offset=(10, 10))
        self.legend.setBrush(QColor(255, 255, 255, 150)) 
        self.legend.setLabelTextColor("#000000") 

        container_layout.addWidget(self.graph_widget)
        layout.addWidget(self.container)

        # Data Storage
        self.y_data = [[] for _ in range(NUM_GRAPH_SENSORS)]
        self.plot_lines = []
        self.fill_items = [] # Store fill items
        self.is_filled_mode = False # Default: Line Mode
        
        self._setup_graph_lines()

    def reset_view(self):
        """Kembalikan grafik ke mode auto-scale"""
        self.graph_widget.enableAutoRange()

    def toggle_graph_style(self):
        """Ganti antara 3 Mode: Line -> Area -> Scatter"""
        
        # Cycle mode: 0 (Line) -> 1 (Area) -> 2 (Scatter) -> 0
        current_mode = getattr(self, 'graph_mode', 0)
        new_mode = (current_mode + 1) % 3
        self.graph_mode = new_mode
        
        # Clear old items (fills & scatter spots)
        self.graph_widget.clear()
        self.plot_lines = []
        self.fill_items = []
        
        # Setup ulang plot sesuai mode
        sensor_names = ["MQ-2", "MQ-3", "MQ-4", "MQ-6", "MQ-7", "MQ-8", "MQ-135", "QCM"]
        colors = [
            '#EF4444', '#3B82F6', '#10B981', '#F59E0B', 
            '#8B5CF6', '#06B6D4', '#F97316', '#EC4899'
        ]
        
        for i in range(NUM_GRAPH_SENSORS):
            color = colors[i % len(colors)]
            
            # MODE 0: LINE (Garis Tebal)
            if new_mode == 0:
                pen = pg.mkPen(color=color, width=3)
                line = self.graph_widget.plot([0], [0], pen=pen, name=sensor_names[i])
                self.plot_lines.append(line)
                self.style_btn.setText("📈 Line")

            # MODE 1: AREA (Isi Warna)
            elif new_mode == 1:
                pen = pg.mkPen(color=color, width=1)
                # Plot dummy baseline untuk fill
                base_curve = self.graph_widget.plot([0], [0], pen=None) 
                line = self.graph_widget.plot([0], [0], pen=pen, name=sensor_names[i])
                
                # Fill dengan transparansi
                fill = pg.FillBetweenItem(curve1=line, curve2=base_curve, brush=QColor(color + "40"))
                self.graph_widget.addItem(fill)
                self.plot_lines.append(line)
                self.style_btn.setText("⛰️ Area")

            # MODE 2: SCATTER (Titik-titik)
            elif new_mode == 2:
                # Pen None artinya tidak ada garis penghubung
                line = self.graph_widget.plot([0], [0], pen=None, symbol='o', symbolBrush=color, symbolSize=5, name=sensor_names[i])
                self.plot_lines.append(line)
                self.style_btn.setText("∴ Dots")
        
        # Restore data ke grafik baru
        # Kita harus repaint ulang data yang ada di self.y_data
        for i in range(NUM_GRAPH_SENSORS):
            if len(self.y_data[i]) > 0:
                self.plot_lines[i].setData(list(range(len(self.y_data[i]))), self.y_data[i])

    def _setup_graph_lines(self):
        # Inisialisasi awal (Mode 0)
        self.graph_mode = 0
        self.style_btn.setText("📈 Line")
        
        sensor_names = ["MQ-2", "MQ-3", "MQ-4", "MQ-6", "MQ-7", "MQ-8", "MQ-135", "QCM"]
        colors = [
            '#EF4444', '#3B82F6', '#10B981', '#F59E0B', 
            '#8B5CF6', '#06B6D4', '#F97316', '#EC4899'
        ]
        
        for i in range(NUM_GRAPH_SENSORS):
            pen = pg.mkPen(color=colors[i % len(colors)], width=3) 
            line = self.graph_widget.plot([0], [0], pen=pen, name=sensor_names[i])
            self.plot_lines.append(line)

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