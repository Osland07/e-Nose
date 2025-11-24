from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class SensorDisplay(QWidget):
    """A widget to display a single sensor reading with an icon, value, and unit."""
    def __init__(self, icon_path: str, unit: str, title: str):
        super().__init__()
        self.setMinimumWidth(110)
        self.setMaximumWidth(150)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        container = QWidget()
        container.setObjectName("sensorCard")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(4, 4, 4, 4)
        container_layout.setSpacing(4)

        icon_label = QLabel()
        icon_label.setPixmap(QIcon(icon_path).pixmap(24, 24))
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_layout = QVBoxLayout()
        value_layout.setSpacing(0)
        
        self.value_label = QLabel("--")
        self.value_label.setObjectName("sensorValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        unit_label = QLabel(unit)
        unit_label.setObjectName("sensorUnit")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_layout.addWidget(self.value_label)
        value_layout.addWidget(unit_label)

        container_layout.addWidget(icon_label)
        container_layout.addLayout(value_layout, 1)

        title_label = QLabel(title)
        title_label.setObjectName("sensorTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(container)
        main_layout.addWidget(title_label)

        self.setStyleSheet("""
            #sensorCard { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; }
            #sensorValue { font-size: 18px; font-weight: bold; color: #1E3A8A; }
            #sensorUnit { font-size: 10px; color: #64748B; }
            #sensorTitle { font-size: 10px; font-weight: 500; color: #334155; }
        """)

    def set_value(self, value: float, precision: int = 2):
        self.value_label.setText(f"{value:.{precision}f}")

    def reset(self):
        self.value_label.setText("--")
