from PyQt6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout,
    QLabel, 
    QTableWidget, 
    QTableWidgetItem, 
    QPushButton, 
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QApplication,
    QStyle,
    QComboBox,
    QLineEdit,
    QGroupBox
)
from PyQt6.QtCore import Qt
import pandas as pd
import math

from database.database import create_connection, get_all_records, get_record_by_id, delete_record_by_id, get_paginated_records, get_record_count
from .detail_page import DetailPage

class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()

        self.records_per_page = 15
        self.current_page = 1
        self.total_pages = 1
        
        self._init_ui()
        # The first populate_table is now triggered by apply_filters_and_search
        # to ensure a consistent load.
        self.apply_filters_and_search()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        top_bar_layout = QHBoxLayout()
        title = QLabel("Detection History")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E3A8A;")
        
        top_bar_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        top_bar_layout.addStretch()
        layout.addLayout(top_bar_layout)
        
        controls_group = QGroupBox("Filter and Search")
        controls_layout = QHBoxLayout(controls_group)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Terdeteksi Daging Babi", "Tidak Terdeteksi"])
        self.filter_combo.currentTextChanged.connect(self.apply_filters_and_search)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by ID, date, result...")
        self.search_input.textChanged.connect(self.apply_filters_and_search)

        controls_layout.addWidget(QLabel("Filter by Result:"))
        controls_layout.addWidget(self.filter_combo)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(QLabel("Search:"))
        controls_layout.addWidget(self.search_input, 1)
        
        layout.addWidget(controls_group)
        layout.addSpacing(10)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["No", "Date and Time", "Result", "Action"])
        self.history_table.setStyleSheet("""
            QTableWidget { font-size: 14px; border: 1px solid #D1D5DB; border-radius: 8px; gridline-color: #E5E7EB; }
            QHeaderView::section { background-color: #F3F4F6; padding: 10px; border: none; font-weight: bold; font-size: 14px; color: #374151; }
            QTableWidget::item { padding: 10px; color: #111827; }
            QTableWidget::alternating-row-color { background-color: #F9FAFB; }
        """)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setShowGrid(False)
        self.history_table.verticalHeader().setVisible(False)
        
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.history_table.setColumnWidth(3, 120)

        layout.addWidget(self.history_table)

        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("← Previous")
        self.prev_button.clicked.connect(self.prev_page)
        self.page_label = QLabel("Page 1 of 1")
        self.next_button = QPushButton("Next →")
        self.next_button.clicked.connect(self.next_page)

        pagination_layout.addStretch()
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addStretch()

        layout.addLayout(pagination_layout)

    def apply_filters_and_search(self):
        self.current_page = 1
        self.populate_table()

    def populate_table(self):
        filter_text = self.filter_combo.currentText()
        search_query = self.search_input.text()

        conn = create_connection()
        if not conn:
            QMessageBox.warning(self, "Database Error", "Could not connect to the database.")
            return

        total_records = get_record_count(conn, filter_text, search_query)
        self.total_pages = math.ceil(total_records / self.records_per_page) if total_records > 0 else 1
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        if self.current_page < 1:
            self.current_page = 1

        offset = (self.current_page - 1) * self.records_per_page
        records = get_paginated_records(conn, offset, self.records_per_page, filter_text, search_query)
        conn.close()

        self.history_table.setRowCount(0) # Clear table before populating
        self.history_table.setRowCount(len(records))
        for i, record in enumerate(records):
            record_id = record[0]
            
            self.history_table.setItem(i, 0, QTableWidgetItem(str(record_id)))
            self.history_table.setItem(i, 1, QTableWidgetItem(record[1]))
            self.history_table.setItem(i, 2, QTableWidgetItem(record[2]))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)

            style = self.style()
            detail_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)
            delete_icon = style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
            export_icon = style.standardIcon(QStyle.StandardPixmap.SP_ArrowDown)

            detail_button = QPushButton(detail_icon, "")
            delete_button = QPushButton(delete_icon, "")
            export_button = QPushButton(export_icon, "")

            self._set_icon_button_style(detail_button, "Lihat Detail")
            self._set_icon_button_style(delete_button, "Hapus Record")
            self._set_icon_button_style(export_button, "Ekspor Record")

            detail_button.clicked.connect(lambda checked, rec_id=record_id: self.show_record_detail(rec_id))
            delete_button.clicked.connect(lambda checked, rec_id=record_id: self.delete_record_confirmation(rec_id))
            export_button.clicked.connect(lambda checked, rec_id=record_id: self.export_single_record(rec_id))
            
            actions_layout.addWidget(detail_button)
            actions_layout.addWidget(delete_button)
            actions_layout.addWidget(export_button)
            actions_layout.addStretch()

            self.history_table.setCellWidget(i, 3, actions_widget)
            self.history_table.setRowHeight(i, 40) # Set row height for icons

            for j in range(3):
                self.history_table.item(i, j).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.update_pagination_ui()

    def update_pagination_ui(self):
        if self.total_pages <= 1:
            self.page_label.setText("Page 1 of 1")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
        else:
            self.page_label.setText(f"Page {self.current_page} of {self.total_pages}")
            self.prev_button.setEnabled(self.current_page > 1)
            self.next_button.setEnabled(self.current_page < self.total_pages)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.populate_table()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.populate_table()
            
    def _set_icon_button_style(self, button, tooltip):
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; padding: 4px; border-radius: 15px; }
            QPushButton:hover { background-color: #E5E7EB; }
        """)
        button.setFixedSize(30, 30)
        
    def show_record_detail(self, record_id):
        try:
            detail_dialog = DetailPage(record_id, self)
            detail_dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Tidak dapat membuka halaman detail: {e}")

    def delete_record_confirmation(self, record_id):
        reply = QMessageBox.question(self, 'Konfirmasi Hapus',
                                     f"Anda yakin ingin menghapus record dengan ID {record_id}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.delete_record(record_id)

    def delete_record(self, record_id):
        conn = create_connection()
        if not conn:
            QMessageBox.warning(self, "Error Database", "Tidak dapat terhubung ke database untuk menghapus.")
            return

        try:
            rows_affected = delete_record_by_id(conn, record_id)
            conn.close()
            if rows_affected > 0:
                self.apply_filters_and_search()
            else:
                QMessageBox.warning(self, "Hapus Gagal", f"Record dengan ID {record_id} tidak ditemukan atau gagal dihapus.")
        except Exception as e:
            QMessageBox.critical(self, "Error Hapus", f"Terjadi kesalahan saat menghapus data: {e}")

    def export_single_record(self, record_id):
        conn = create_connection()
        if not conn:
            QMessageBox.warning(self, "Error Database", "Tidak dapat terhubung ke database untuk mengekspor.")
            return

        record = get_record_by_id(conn, record_id)
        conn.close()

        if not record:
            QMessageBox.warning(self, "Record Tidak Ditemukan", f"Record dengan ID {record_id} tidak ditemukan untuk diekspor.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, f"Simpan Record {record_id} ke CSV", f"record_{record_id}.csv", "CSV Files (*.csv)")

        if path:
            try:
                # Use pandas to write the single record
                df = pd.DataFrame([record], columns=['ID', 'Timestamp', 'Result', 'RawData'])
                df.to_csv(path, index=False, encoding='utf-8')
                QMessageBox.information(self, "Ekspor Berhasil", f"Record {record_id} berhasil diekspor ke {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error Ekspor", f"Terjadi kesalahan saat mengekspor record: {e}")
