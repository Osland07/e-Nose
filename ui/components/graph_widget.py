from PyQt6.QtWidgets import QGroupBox, QVBoxLayout
import pyqtgraph as pg

# --- Configuration ---
NUM_GRAPH_SENSORS = 7
MAX_DATA_POINTS = 200

class GraphWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Grafik Sensor Gas", parent)
        
        self.graph_widget = pg.PlotWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.graph_widget)

        self.y_data = [[] for _ in range(NUM_GRAPH_SENSORS)]
        self.plot_lines = []
        
        self._setup_styles()
        self._setup_graph_lines()

    def _setup_styles(self):
        self.setStyleSheet("""
            QGroupBox { 
                font-size: 18px; 
                font-weight: bold; 
                color: #1E3A8A; 
                margin-top: 10px; 
                border: 1px solid #D1D5DB; 
                border-radius: 8px; 
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                subcontrol-position: top left; 
                padding: 0 10px; 
            }
        """)
        self.graph_widget.setBackground('w')
        self.graph_widget.setTitle("Data Sensor Real-time", color="#1E3A8A", size="16pt")
        styles = {'color':'#1E3A8A', 'font-size':'12pt'}
        self.graph_widget.setLabel('left', 'Nilai Sensor', **styles)
        self.graph_widget.setLabel('bottom', 'Waktu (sampel)', **styles)
        self.graph_widget.addLegend()
        self.graph_widget.showGrid(x=True, y=True)

    def _setup_graph_lines(self):
        sensor_names = ["MQ-2", "MQ-3", "MQ-4", "MQ-6", "MQ-7", "MQ-8", "MQ-135"]
        colors = ['#E53935', '#1E88E5', '#43A047', '#FDD835', '#FB8C00', '#8E24AA', '#00897B']
        for i in range(NUM_GRAPH_SENSORS):
            pen = pg.mkPen(color=colors[i % len(colors)], width=2)
            self.plot_lines.append(self.graph_widget.plot([0], [0], pen=pen, name=sensor_names[i]))

    def update_plot(self, graph_values):
        if len(graph_values) != NUM_GRAPH_SENSORS:
            return

        for i in range(NUM_GRAPH_SENSORS):
            self.y_data[i].append(graph_values[i])
            if len(self.y_data[i]) > MAX_DATA_POINTS:
                self.y_data[i].pop(0)
            
            self.plot_lines[i].setData(list(range(len(self.y_data[i]))), self.y_data[i])

    def reset(self):
        self.y_data = [[] for _ in range(NUM_GRAPH_SENSORS)]
        for i in range(NUM_GRAPH_SENSORS):
            self.plot_lines[i].setData([0], [0])

