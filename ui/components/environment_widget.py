from PyQt6.QtWidgets import QGroupBox, QVBoxLayout
from PyQt6.QtCore import Qt
import os
from .sensor_display import SensorDisplay

class EnvironmentWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Environment", parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 15, 5, 5)
        self.setMinimumHeight(160)
        
        base_path = os.path.abspath(os.path.dirname(__file__))
        assets_path = os.path.join(base_path, '..', '..', 'assets')

        self.temperature_display = SensorDisplay(os.path.join(assets_path, 'temperature.svg'), "°C", "Temperature")
        self.humidity_display = SensorDisplay(os.path.join(assets_path, 'humidity.svg'), "%", "Humidity")
        self.pressure_display = SensorDisplay(os.path.join(assets_path, 'pressure.svg'), "hPa", "Pressure")

        layout.addWidget(self.temperature_display, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(5)
        layout.addWidget(self.humidity_display, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(5)
        layout.addWidget(self.pressure_display, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self.setStyleSheet("""
            QGroupBox { 
                font-size: 14px; 
                font-weight: bold; 
                color: #1E3A8A; 
                margin-top: 8px; 
                border: 1px solid #E2E8F0; 
                border-radius: 6px; 
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                subcontrol-position: top center; 
                padding: 3px 8px; 
            }
        """)

    def update_values(self, temp, hum, press):
        self.temperature_display.set_value(temp)
        self.humidity_display.set_value(hum)
        self.pressure_display.set_value(press / 100) # Convert Pa to hPa

    def reset(self):
        self.temperature_display.reset()
        self.humidity_display.reset()
        self.pressure_display.reset()
