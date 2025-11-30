from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette

class StatCard(QFrame):
    """Widget Kartu tunggal untuk menampilkan satu nilai sensor (misal: Suhu)"""
    def __init__(self, title, unit, color_hex, icon_char=""):
        super().__init__()
        self.unit = unit
        self.setObjectName("StatCard")
        
        # Styling Kartu
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background-color: {color_hex};
                border-radius: 12px;
                border: 1px solid {color_hex};
            }}
            QLabel {{ color: white; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header (Title + Icon)
        header_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; opacity: 0.8;")
        
        icon_label = QLabel(icon_char) # Bisa diganti icon SVG nanti
        icon_label.setStyleSheet("font-size: 16px;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        
        # Value
        self.value_label = QLabel(f"0 {unit}")
        self.value_label.setStyleSheet("font-size: 22px; font-weight: 800;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(f"{value:.1f} {self.unit}")

class EnvironmentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self) # Stack Horizontal untuk ditaruh di atas grafik
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # 3 Kartu dengan warna berbeda (Gradient feel)
        # Suhu (Orange/Warm), Kelembaban (Blue/Cool), Tekanan (Teal/Neutral)
        self.card_temp = StatCard("TEMPERATUR", "°C", "#F59E0B", "🌡") 
        self.card_hum = StatCard("KELEMBABAN", "%", "#3B82F6", "💧")
        self.card_pres = StatCard("TEKANAN", "hPa", "#10B981", "⏲")
        
        layout.addWidget(self.card_temp)
        layout.addWidget(self.card_hum)
        layout.addWidget(self.card_pres)
        
    def update_values(self, t, h, p):
        self.card_temp.set_value(t)
        self.card_hum.set_value(h)
        self.card_pres.set_value(p)

    def reset(self):
        self.update_values(0, 0, 0)