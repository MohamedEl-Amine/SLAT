"""
Admin interface for SLAT - Configuration and management.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QTabWidget, QCheckBox, QMessageBox, 
                             QTimeEdit, QComboBox, QHeaderView, QFileDialog)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QFont
import csv
from datetime import datetime

class AdminInterface(QWidget):
    def __init__(self, db, public):
        super().__init__()
        self.db = db
        self.public = public
        self.setWindowTitle("SLAT - Admin Panel")
        self.setFixedSize(1000, 700)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Employee Management Tab
        self.employee_tab = QWidget()
        self.setup_employee_tab()
        self.tabs.addTab(self.employee_tab, "Employee Management")

        # Settings Tab
        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Settings")

        # Logs Tab
        self.logs_tab = QWidget()
        self.setup_logs_tab()
        self.tabs.addTab(self.logs_tab, "Attendance Logs")

        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        self.layout.addWidget(logout_btn)

        # Load initial data
        self.load_employees()
        self.load_logs()

    def setup_employee_tab(self):
        layout = QVBoxLayout()
        self.employee_tab.setLayout(layout)

        # Add Employee Section
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Employee ID:"))
        self.emp_id_input = QLineEdit()
        add_layout.addWidget(self.emp_id_input)

        add_layout.addWidget(QLabel("Name:"))
        self.emp_name_input = QLineEdit()
        add_layout.addWidget(self.emp_name_input)

        add_btn = QPushButton("Add Employee")
        add_btn.clicked.connect(self.add_employee)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        # Employee List
        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(5)
        self.employee_table.setHorizontalHeaderLabels(["ID", "Name", "QR Code", "Face", "Actions"])
        self.employee_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.employee_table)

    def setup_settings_tab(self):
        layout = QVBoxLayout()
        self.settings_tab.setLayout(layout)

        # Time Windows
        time_layout = QVBoxLayout()
        time_layout.addWidget(QLabel("Morning Window:"))

        morning_layout = QHBoxLayout()
        morning_layout.addWidget(QLabel("Start:"))
        self.morning_start = QTimeEdit()
        self.morning_start.setTime(QTime.fromString(self.db.get_setting('morning_start'), 'hh:mm'))
        morning_layout.addWidget(self.morning_start)

        morning_layout.addWidget(QLabel("End:"))
        self.morning_end = QTimeEdit()
        self.morning_end.setTime(QTime.fromString(self.db.get_setting('morning_end'), 'hh:mm'))
        morning_layout.addWidget(self.morning_end)

        time_layout.addLayout(morning_layout)

        time_layout.addWidget(QLabel("Afternoon Window:"))

        afternoon_layout = QHBoxLayout()
        afternoon_layout.addWidget(QLabel("Start:"))
        self.afternoon_start = QTimeEdit()
        self.afternoon_start.setTime(QTime.fromString(self.db.get_setting('afternoon_start'), 'hh:mm'))
        afternoon_layout.addWidget(self.afternoon_start)

        afternoon_layout.addWidget(QLabel("End:"))
        self.afternoon_end = QTimeEdit()
        self.afternoon_end.setTime(QTime.fromString(self.db.get_setting('afternoon_end'), 'hh:mm'))
        afternoon_layout.addWidget(self.afternoon_end)

        time_layout.addLayout(afternoon_layout)

        layout.addLayout(time_layout)

        # Identification Methods
        methods_layout = QVBoxLayout()
        methods_layout.addWidget(QLabel("Global Identification Methods (Available to all employees):"))

        self.card_enabled = QCheckBox("Employee ID / Card Entry")
        self.card_enabled.setChecked(self.db.get_setting('card_enabled') == '1')
        methods_layout.addWidget(self.card_enabled)

        self.qr_enabled = QCheckBox("QR Code Scanning")
        self.qr_enabled.setChecked(self.db.get_setting('qr_enabled') == '1')
        methods_layout.addWidget(self.qr_enabled)

        self.face_enabled = QCheckBox("Face Recognition")
        self.face_enabled.setChecked(self.db.get_setting('face_enabled') == '1')
        methods_layout.addWidget(self.face_enabled)

        layout.addLayout(methods_layout)

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

    def setup_logs_tab(self):
        layout = QVBoxLayout()
        self.logs_tab.setLayout(layout)

        # Logs Table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(6)
        self.logs_table.setHorizontalHeaderLabels(["Employee ID", "Name", "Action", "Time", "Method", "Device"])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.logs_table)

        # Refresh and Export buttons
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Logs")
        refresh_btn.clicked.connect(self.load_logs)
        button_layout.addWidget(refresh_btn)

        export_btn = QPushButton("Export Logs to CSV")
        export_btn.clicked.connect(self.export_logs)
        button_layout.addWidget(export_btn)

        layout.addLayout(button_layout)

    def add_employee(self):
        emp_id = self.emp_id_input.text().strip()
        name = self.emp_name_input.text().strip()
        
        if not emp_id or not name:
            QMessageBox.warning(self, "Error", "Please enter both ID and name.")
            return
        
        # Add to database
        success = self.db.add_employee(emp_id, name)
        if success:
            QMessageBox.information(self, "Success", f"Employee {name} added successfully.")
            self.emp_id_input.clear()
            self.emp_name_input.clear()
            self.load_employees()
        else:
            QMessageBox.warning(self, "Error", f"Employee ID {emp_id} already exists.")
            self.emp_name_input.clear()
            self.load_employees()

    def load_employees(self):
        """Load all employees into the table"""
        employees = self.db.get_all_employees()
        self.employee_table.setRowCount(len(employees))
        
        for row, emp in enumerate(employees):
            self.employee_table.setItem(row, 0, QTableWidgetItem(emp.employee_id))
            self.employee_table.setItem(row, 1, QTableWidgetItem(emp.name))
            self.employee_table.setItem(row, 2, QTableWidgetItem("✓" if emp.qr_code else "✗"))
            self.employee_table.setItem(row, 3, QTableWidgetItem("✓" if emp.face_image else "✗"))
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            # Generate QR button
            qr_btn = QPushButton("QR")
            qr_btn.setToolTip("Generate QR Code")
            qr_btn.clicked.connect(lambda checked, eid=emp.employee_id: self.generate_qr(eid))
            action_layout.addWidget(qr_btn)
            
            # Face button
            face_btn = QPushButton("Face")
            face_btn.setToolTip("Set Face Image")
            face_btn.clicked.connect(lambda checked, eid=emp.employee_id: self.set_face(eid))
            action_layout.addWidget(face_btn)
            
            # Enable/Disable button
            toggle_btn = QPushButton("Disable" if emp.enabled else "Enable")
            toggle_btn.clicked.connect(lambda checked, eid=emp.employee_id, enabled=emp.enabled: self.toggle_employee(eid, not enabled))
            action_layout.addWidget(toggle_btn)
            
            action_widget.setLayout(action_layout)
            self.employee_table.setCellWidget(row, 4, action_widget)
    
    def generate_qr(self, employee_id):
        """Generate and save QR code for employee"""
        try:
            qr_bytes = self.db.generate_qr_code(employee_id)
            
            # Save QR code image
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save QR Code",
                f"QR_{employee_id}.png",
                "PNG Files (*.png)"
            )
            
            if filename:
                with open(filename, 'wb') as f:
                    f.write(qr_bytes)
                QMessageBox.information(self, "Success", f"QR code generated and saved to {filename}")
                self.load_employees()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate QR code: {str(e)}")
    
    def set_face(self, employee_id):
        """Set face image for employee"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Face Image",
            "",
            "Image Files (*.png *.jpg *.jpeg)"
        )
        
        if filename:
            try:
                with open(filename, 'rb') as f:
                    face_data = f.read()
                self.db.update_employee_face(employee_id, face_data)
                QMessageBox.information(self, "Success", f"Face image set for {employee_id}")
                self.load_employees()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set face image: {str(e)}")

    def toggle_employee(self, employee_id, new_status):
        """Enable or disable an employee"""
        self.db.update_employee_status(employee_id, new_status)
        self.load_employees()
        QMessageBox.information(self, "Success", f"Employee {employee_id} {'enabled' if new_status else 'disabled'}.")

    def load_logs(self):
        """Load attendance logs into the table"""
        logs = self.db.get_all_logs(limit=100)
        self.logs_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            # log structure: id, employee_id, action, timestamp, method_used, device_id, photo, integrity_hash
            emp = self.db.get_employee(log[1])
            emp_name = emp.name if emp else "Unknown"
            
            self.logs_table.setItem(row, 0, QTableWidgetItem(log[1]))  # employee_id
            self.logs_table.setItem(row, 1, QTableWidgetItem(emp_name))  # name
            self.logs_table.setItem(row, 2, QTableWidgetItem(log[2]))  # action
            self.logs_table.setItem(row, 3, QTableWidgetItem(str(log[3])))  # timestamp
            self.logs_table.setItem(row, 4, QTableWidgetItem(log[4]))  # method_used
            self.logs_table.setItem(row, 5, QTableWidgetItem(log[5] if log[5] else "N/A"))  # device_id

    def save_settings(self):
        # Save time windows
        self.db.update_setting('morning_start', self.morning_start.time().toString('HH:mm'))
        self.db.update_setting('morning_end', self.morning_end.time().toString('HH:mm'))
        self.db.update_setting('afternoon_start', self.afternoon_start.time().toString('HH:mm'))
        self.db.update_setting('afternoon_end', self.afternoon_end.time().toString('HH:mm'))

        # Save identification method settings
        self.db.update_setting('card_enabled', '1' if self.card_enabled.isChecked() else '0')
        self.db.update_setting('qr_enabled', '1' if self.qr_enabled.isChecked() else '0')
        self.db.update_setting('face_enabled', '1' if self.face_enabled.isChecked() else '0')

        QMessageBox.information(self, "Success", "Settings saved successfully.")

    def export_logs(self):
        """Export logs to CSV file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Logs", 
            f"attendance_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                logs = self.db.get_all_logs()
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Employee ID', 'Name', 'Action', 'Timestamp', 'Method', 'Device ID', 'Integrity Hash'])
                    
                    for log in logs:
                        emp = self.db.get_employee(log[1])
                        emp_name = emp.name if emp else "Unknown"
                        writer.writerow([
                            log[1],  # employee_id
                            emp_name,
                            log[2],  # action
                            log[3],  # timestamp
                            log[4],  # method_used
                            log[5] if log[5] else "N/A",  # device_id
                            log[7]   # integrity_hash
                        ])
                
                QMessageBox.information(self, "Success", f"Logs exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export logs: {str(e)}")

    def logout(self):
        self.close()
        self.public.show()