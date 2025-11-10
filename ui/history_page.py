from PyQt6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QLabel, 
    QTableWidget, 
    QTableWidgetItem, 
    QPushButton, 
    QHeaderView
)
from PyQt6.QtCore import Qt

from database.database import create_connection, get_all_records

class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("Detection History")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #1E3A8A; /* Dark Blue */
            margin-bottom: 20px;
        """)
        layout.addWidget(title)

        # History Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["No", "Date and Time", "Result", "Action"])
        self.history_table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                gridline-color: #E5E7EB;
            }
            QHeaderView::section {
                background-color: #F3F4F6;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 14px;
                color: #374151; /* Dark Gray for header text */
            }
            QTableWidget::item {
                padding: 10px;
                color: #111827; /* Very Dark Gray/Black for item text */
            }
            QTableWidget::alternating-row-color {
                background-color: #F9FAFB;
            }
        """)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setShowGrid(False)
        self.history_table.verticalHeader().setVisible(False)
        
        # Make columns responsive
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.populate_table()
        layout.addWidget(self.history_table)

    def populate_table(self):
        conn = create_connection()
        if conn:
            records = get_all_records(conn)
            conn.close()

            self.history_table.setRowCount(len(records))
            for i, record in enumerate(records):
                # record is (id, timestamp, result)
                self.history_table.setItem(i, 0, QTableWidgetItem(str(record[0]))) # No (ID)
                self.history_table.setItem(i, 1, QTableWidgetItem(record[1])) # Date and Time
                self.history_table.setItem(i, 2, QTableWidgetItem(record[2])) # Result
                
                # Detail Button
                detail_button = QPushButton("Detail")
                detail_button.setStyleSheet("""
                    QPushButton {
                        background-color: #3B82F6;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 5px 10px;
                    }
                    QPushButton:hover {
                        background-color: #2563EB;
                    }
                """)
                # TODO: Connect this button to a detail view later
                self.history_table.setCellWidget(i, 3, detail_button)

                # Center align text in cells
                for j in range(3): # Only align text columns, not the button column
                    self.history_table.item(i, j).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            print("Error: Could not connect to database to populate history.")
