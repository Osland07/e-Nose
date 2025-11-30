from PyQt6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QPoint

class ToastNotification(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedWidth(350)
        self.setFixedHeight(50)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #334155; 
                color: white; 
                font-weight: bold; 
                font-size: 14px;
                border-radius: 25px;
                padding: 10px;
                border: 1px solid #475569;
            }
        """)
        self.hide()
        
        # Efek Transparansi
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Animasi
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(500) # 0.5 detik fade in/out
        
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)

    def show_message(self, message, type="info"):
        # Ganti warna berdasarkan tipe
        if type == "success": color = "#10B981" # Green
        elif type == "error": color = "#EF4444" # Red
        elif type == "warning": color = "#F59E0B" # Orange
        else: color = "#334155" # Dark Slate
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}; 
                color: white; 
                font-weight: bold; 
                font-size: 13px;
                border-radius: 10px;
                padding: 5px 20px;
            }}
        """)
        
        self.setText(message)
        
        # Posisi di tengah bawah
        parent_rect = self.parent().rect()
        x = (parent_rect.width() - self.width()) // 2
        y = parent_rect.height() - 100
        self.move(x, y)
        
        self.raise_()
        self.show()
        self.fade_in()
        self.timer.start(3000) # Muncul selama 3 detik

    def fade_in(self):
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.start()

    def fade_out(self):
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self.anim.finished.connect(self.hide)
        self.anim.start()
