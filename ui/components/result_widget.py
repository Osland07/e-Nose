from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QDialog, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class VotingDetailDialog(QDialog):
    def __init__(self, details, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detail Voting Dewan Juri AI")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Hasil Analisa Per-Model:")
        lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl)
        
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Nama Model", "Keputusan", "Keyakinan"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setRowCount(len(details))
        table.setStyleSheet("QTableWidget { background-color: white; gridline-color: #ccc; }")
        
        for i, d in enumerate(details):
            table.setItem(i, 0, QTableWidgetItem(d['name']))
            
            res_item = QTableWidgetItem(d['label'])
            if "Terdeteksi" in d['label']: res_item.setForeground(Qt.GlobalColor.red)
            else: res_item.setForeground(Qt.GlobalColor.darkGreen)
            
            font = QFont()
            font.setBold(True)
            res_item.setFont(font)
            
            table.setItem(i, 1, res_item)
            table.setItem(i, 2, QTableWidgetItem(f"{d['conf']:.1f}%"))
            
        layout.addWidget(table)
        
        btn_close = QPushButton("Tutup")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

class ResultWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.latest_details = []
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        # --- PROGRESS BAR ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #E5E7EB;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 4px;
            }
        """)
        self.progress_bar.hide()
        
        # --- RESULT CARD ---
        self.result_card = QFrame()
        self.result_card.setObjectName("ResultCard")
        self.result_card.setMinimumHeight(140) # Agak tinggi dikit buat tombol detail
        card_layout = QVBoxLayout(self.result_card)
        
        self.status_label = QLabel("SISTEM READY")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; letter-spacing: 1px; color: rgba(255,255,255,0.8);")
        
        self.result_label = QLabel("--")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 24px; font-weight: 900; color: white;")
        self.result_label.setWordWrap(True)

        self.conf_label = QLabel("")
        self.conf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.conf_label.setStyleSheet("font-size: 12px; font-weight: normal; color: white;")

        card_layout.addStretch()
        card_layout.addWidget(self.status_label)
        card_layout.addWidget(self.result_label)
        card_layout.addWidget(self.conf_label)
        
        # Tombol Detail di dalam card
        self.btn_detail = QPushButton("🔍 Lihat Detail Voting")
        self.btn_detail.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_detail.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.2); 
                color: white; 
                border: 1px solid rgba(255,255,255,0.5); 
                border-radius: 15px; 
                padding: 5px 15px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.3);
            }
        """)
        self.btn_detail.hide()
        self.btn_detail.clicked.connect(self.show_voting_details)
        card_layout.addWidget(self.btn_detail, alignment=Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addStretch()

        self.layout.addWidget(self.result_card)
        self.layout.addWidget(self.progress_bar)
        
        self.set_idle_state()

    def show_voting_details(self):
        if self.latest_details:
            dlg = VotingDetailDialog(self.latest_details, self)
            dlg.exec()

    def set_idle_state(self):
        self._style_card("#6B7280") # Abu-abu
        self.status_label.setText("STATUS SISTEM")
        self.result_label.setText("MENUNGGU INPUT")
        self.conf_label.setText("Silakan tekan 'Mulai Deteksi'")
        self.progress_bar.hide()
        self.btn_detail.hide()

    def set_collecting_state(self, duration_s):
        self._style_card("#3B82F6") # Biru
        self.status_label.setText("SEDANG MENGANALISA...")
        self.result_label.setText("MENGAMBIL DATA")
        self.conf_label.setText(f"Sisa waktu: {duration_s} detik")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.btn_detail.hide()

    def update_countdown(self, remaining_ms):
        seconds = int(remaining_ms / 1000)
        self.conf_label.setText(f"Sisa waktu: {seconds} detik...")

    def set_result(self, label, confidence, details=None):
        self.latest_details = details if details else []
        
        if self.latest_details and len(self.latest_details) > 1:
            self.btn_detail.setText(f"🔍 Detail Voting ({len(details)} Model)")
            self.btn_detail.show()
        else:
            self.btn_detail.hide()

        # Logika Warna
        if "Tidak" in label or "Clean" in label or "Sapi" in label:
            color = "#10B981" # Hijau (Aman)
            icon = "✅"
        else:
            color = "#EF4444" # Merah (Terdeteksi)
            icon = "⚠️"

        self._style_card(color)
        self.status_label.setText("KEPUTUSAN FINAL")
        self.result_label.setText(f"{icon} {label.upper()}")
        self.conf_label.setText(f"Tingkat Keyakinan: {confidence:.0f}%")
        self.progress_bar.hide()

    def set_cancelled_state(self):
        self._style_card("#F59E0B") # Orange
        self.status_label.setText("DIBATALKAN")
        self.result_label.setText("PROSES STOP")
        self.conf_label.setText("Pengambilan data dihentikan user")
        self.progress_bar.hide()
        self.btn_detail.hide()
        
    def set_insufficient_data_state(self):
        self._style_card("#F59E0B") # Orange
        self.status_label.setText("ERROR")
        self.result_label.setText("DATA KURANG")
        self.conf_label.setText("Tidak cukup data untuk analisa")
        self.progress_bar.hide()
        self.btn_detail.hide()

    def set_progress_max(self, max_val):
        self.progress_bar.setMaximum(int(max_val))

    def set_progress_value(self, val):
        self.progress_bar.setValue(int(val))

    def reset(self):
        self.set_idle_state()
        
    def _style_card(self, color_hex):
        self.result_card.setStyleSheet(f"""
            QFrame#ResultCard {{
                background-color: {color_hex};
                border-radius: 15px;
            }}
        """)
