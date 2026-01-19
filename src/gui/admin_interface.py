"""
Admin interface for SLAT - Configuration and management.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QTabWidget, QCheckBox, QMessageBox, 
                             QTimeEdit, QComboBox, QHeaderView, QFileDialog, QDialog, QFormLayout,
                             QGroupBox, QTextEdit, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QFont, QPixmap, QImage, QPixmap, QImage
import csv
from datetime import datetime
from io import BytesIO
import base64

class EmployeeProfileDialog(QDialog):
    def __init__(self, db, employee_id):
        super().__init__()
        self.db = db
        self.employee_id = employee_id
        self.employee = self.db.get_employee(employee_id)
        
        if not self.employee:
            QMessageBox.critical(self, "Erreur", "Employé introuvable.")
            self.reject()
            return
            
        self.setWindowTitle(f"Profil employé - {self.employee.name}")
        self.setFixedSize(800, 600)
        
        self.setup_ui()
        self.load_employee_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Employee Details Section
        details_group = QGroupBox("Détails employé")
        details_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.employee.name)
        details_layout.addRow("Nom :", self.name_edit)
        
        self.id_label = QLabel(self.employee.employee_id)
        details_layout.addRow("ID employé :", self.id_label)
        
        self.status_label = QLabel("Activé" if self.employee.enabled else "Désactivé")
        self.status_label.setStyleSheet("color: green;" if self.employee.enabled else "color: red;")
        details_layout.addRow("Statut :", self.status_label)
        
        self.created_label = QLabel(self.employee.created_at.strftime("%Y-%m-%d %H:%M") if self.employee.created_at else "N/A")
        details_layout.addRow("Créé :", self.created_label)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Identification Methods Section
        methods_group = QGroupBox("Méthodes d'identification")
        methods_layout = QVBoxLayout()
        
        # QR Code Section
        qr_layout = QHBoxLayout()
        qr_layout.addWidget(QLabel("Code QR :"))
        
        self.qr_status = QLabel("Non généré" if not self.employee.qr_code else "Généré")
        self.qr_status.setStyleSheet("color: red;" if not self.employee.qr_code else "color: green;")
        qr_layout.addWidget(self.qr_status)
        
        self.view_qr_btn = QPushButton("Voir QR")
        self.view_qr_btn.clicked.connect(self.view_qr)
        qr_layout.addWidget(self.view_qr_btn)
        
        methods_layout.addLayout(qr_layout)
        
        # Face Recognition Section
        face_layout = QHBoxLayout()
        face_layout.addWidget(QLabel("Reconnaissance faciale :"))
        
        self.face_status = QLabel("Non défini" if not self.employee.face_image else "Défini")
        self.face_status.setStyleSheet("color: red;" if not self.employee.face_image else "color: green;")
        face_layout.addWidget(self.face_status)
        
        self.set_face_btn = QPushButton("Définir visage")
        self.set_face_btn.clicked.connect(self.set_face)
        face_layout.addWidget(self.set_face_btn)
        
        methods_layout.addLayout(face_layout)
        
        methods_group.setLayout(methods_layout)
        layout.addWidget(methods_group)
        
        # Recent Attendance Section
        attendance_group = QGroupBox("Présences récentes (10 derniers enregistrements)")
        attendance_layout = QVBoxLayout()
        
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(4)
        self.attendance_table.setHorizontalHeaderLabels(["Action", "Heure", "Méthode", "Appareil"])
        self.attendance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.attendance_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table readonly
        attendance_layout.addWidget(self.attendance_table)
        
        attendance_group.setLayout(attendance_layout)
        layout.addWidget(attendance_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Sauvegarder modifications")
        self.save_btn.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_btn)
        
        self.toggle_status_btn = QPushButton("Désactiver" if self.employee.enabled else "Activer")
        self.toggle_status_btn.clicked.connect(self.toggle_status)
        button_layout.addWidget(self.toggle_status_btn)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def load_employee_data(self):
        # Load recent attendance logs
        logs = self.db.get_employee_logs(self.employee_id, limit=10)
        self.attendance_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            self.attendance_table.setItem(row, 0, QTableWidgetItem(log.action))
            self.attendance_table.setItem(row, 1, QTableWidgetItem(log.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
            self.attendance_table.setItem(row, 2, QTableWidgetItem(log.method_used))
            self.attendance_table.setItem(row, 3, QTableWidgetItem(log.device_id if log.device_id else "N/A"))
    
    def view_qr(self):
        # Generate QR code if it doesn't exist
        if not self.employee.qr_code:
            try:
                qr_bytes = self.db.generate_qr_code(self.employee_id)
                self.employee = self.db.get_employee(self.employee_id)  # Refresh data
                self.qr_status.setText("Généré")
                self.qr_status.setStyleSheet("color: green;")
                self.view_qr_btn.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de génération du code QR : {str(e)}")
                return
            
        # Regenerate QR code image from employee_id
        import qrcode
        from io import BytesIO
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.employee.employee_id)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to QPixmap
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_bytes = buffer.getvalue()
        
        qr_image = QImage()
        qr_image.loadFromData(qr_bytes)
        qr_pixmap = QPixmap.fromImage(qr_image)
        
        # Create a dialog to show the QR code
        qr_dialog = QDialog(self)
        qr_dialog.setWindowTitle(f"Code QR - {self.employee.name}")
        qr_dialog.setFixedSize(400, 450)
        
        layout = QVBoxLayout()
        
        qr_label = QLabel()
        qr_label.setPixmap(qr_pixmap.scaled(300, 300, Qt.KeepAspectRatio))
        layout.addWidget(qr_label, alignment=Qt.AlignCenter)
        
        # Employee info
        info_label = QLabel(f"Employee: {self.employee.name}\nID: {self.employee.employee_id}")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Save button
        save_btn = QPushButton("Save QR Image")
        save_btn.clicked.connect(lambda: self.save_qr_image(qr_pixmap))
        layout.addWidget(save_btn)
        
        qr_dialog.setLayout(layout)
        qr_dialog.exec_()
    
    def save_qr_image(self, qr_pixmap):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le code QR",
            f"QR_{self.employee.employee_id}.png",
            "PNG Files (*.png)"
        )
        
        if filename:
            qr_pixmap.save(filename, "PNG")
            QMessageBox.information(self, "Succès", f"Code QR enregistré dans {filename}")
    
    def set_face(self):
        """Capture and set face image for employee using camera."""
        from utils.face_recognition import FaceRecognition
        
        face_rec = FaceRecognition()
        
        # Test camera availability
        if not face_rec.test_camera():
            QMessageBox.critical(self, "Erreur", "Aucune caméra détectée.\n\nVeuillez vous assurer qu'une caméra est connectée.")
            return
        
        # Show instructions
        QMessageBox.information(self, "Enregistrement facial", 
                               "📷 Enregistrement facial\n\n"
                               "Instructions :\n"
                               "1. Positionnez votre visage face à la caméra\n"
                               "2. Assurez-vous d'être seul dans le cadre\n"
                               "3. Regardez directement la caméra\n"
                               "4. Appuyez sur ESPACE quand le cadre devient vert\n"
                               "5. Appuyez sur Q pour annuler\n\n"
                               "Note : L'ancien profil facial sera remplacé.",
                               QMessageBox.Ok)
        
        # Capture face with quality validation
        result = face_rec.capture_face_for_enrollment()
        
        if result is None:
            QMessageBox.warning(self, "Erreur", "Échec de la capture faciale.")
            return
            
        face_data, message = result
        
        if face_data is None:
            QMessageBox.warning(self, "Capture annulée", f"La capture faciale a été annulée.\n\n{message}")
            return
        
        try:
            # Convert numpy array to bytes for storage
            face_bytes = face_data.tobytes()
            
            # Store in database
            old_face_existed = self.employee.face_image is not None
            self.db.update_employee_face(self.employee_id, face_bytes)
            
            # Log the action
            action_type = "redéfini" if old_face_existed else "défini"
            print(f"Face {action_type} for employee {self.employee_id} - {self.employee.name}")
            
            # Refresh employee data
            self.employee = self.db.get_employee(self.employee_id)
            self.face_status.setText("Défini")
            self.face_status.setStyleSheet("color: green;")
            
            QMessageBox.information(self, "Succès", 
                                   f"✓ Visage {action_type} avec succès\n\n"
                                   f"Employé : {self.employee.name}\n"
                                   f"Le profil biométrique a été enregistré.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'enregistrement du visage : {str(e)}")
    
    def save_changes(self):
        new_name = self.name_edit.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Erreur", "Le nom ne peut pas être vide.")
            return
            
        if new_name != self.employee.name:
            success = self.db.update_employee_name(self.employee_id, new_name)
            if success:
                QMessageBox.information(self, "Succès", "Nom de l'employé mis à jour avec succès.")
                self.employee.name = new_name
                self.setWindowTitle(f"Profil employé - {new_name}")
            else:
                QMessageBox.critical(self, "Erreur", "Échec de mise à jour du nom de l'employé.")
    
    def toggle_status(self):
        new_status = not self.employee.enabled
        self.db.update_employee_status(self.employee_id, new_status)
        self.employee.enabled = new_status
        self.status_label.setText("Activé" if new_status else "Désactivé")
        self.status_label.setStyleSheet("color: green;" if new_status else "color: red;")
        self.toggle_status_btn.setText("Désactiver" if new_status else "Activer")
        QMessageBox.information(self, "Succès", f"Employé {'activé' if new_status else 'désactivé'}.")


class AdminInterface(QWidget):
    def __init__(self, db, public):
        super().__init__()
        self.db = db
        self.public = public
        self.setWindowTitle("SLAT - Panneau d'administration")
        self.setFixedSize(1000, 700)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Employee Management Tab
        self.employee_tab = QWidget()
        self.setup_employee_tab()
        self.tabs.addTab(self.employee_tab, "Gestion employés")

        # Settings Tab
        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Paramètres")

        # Logs Tab
        self.logs_tab = QWidget()
        self.setup_logs_tab()
        self.tabs.addTab(self.logs_tab, "Journaux présence")

        # Logout button
        logout_btn = QPushButton("Déconnexion")
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
        add_layout.addWidget(QLabel("ID employé :"))
        self.emp_id_input = QLineEdit()
        add_layout.addWidget(self.emp_id_input)

        add_layout.addWidget(QLabel("Nom :"))
        self.emp_name_input = QLineEdit()
        add_layout.addWidget(self.emp_name_input)

        add_btn = QPushButton("Ajouter employé")
        add_btn.clicked.connect(self.add_employee)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        # Employee List
        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(6)
        self.employee_table.setHorizontalHeaderLabels(["ID", "Nom", "Statut", "Code QR", "Visage", "Actions"])
        self.employee_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.employee_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table readonly
        layout.addWidget(self.employee_table)

    def setup_settings_tab(self):
        layout = QVBoxLayout()
        self.settings_tab.setLayout(layout)

        # Time Windows
        time_layout = QVBoxLayout()
        time_layout.addWidget(QLabel("Fenêtre matin :"))

        morning_layout = QHBoxLayout()
        morning_layout.addWidget(QLabel("Début :"))
        self.morning_start = QTimeEdit()
        self.morning_start.setTime(QTime.fromString(self.db.get_setting('morning_start'), 'hh:mm'))
        morning_layout.addWidget(self.morning_start)

        morning_layout.addWidget(QLabel("Fin :"))
        self.morning_end = QTimeEdit()
        self.morning_end.setTime(QTime.fromString(self.db.get_setting('morning_end'), 'hh:mm'))
        morning_layout.addWidget(self.morning_end)

        time_layout.addLayout(morning_layout)

        time_layout.addWidget(QLabel("Fenêtre après-midi :"))

        afternoon_layout = QHBoxLayout()
        afternoon_layout.addWidget(QLabel("Début :"))
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
        methods_layout.addWidget(QLabel("Méthodes d'identification globales (disponibles pour tous les employés) :"))

        self.card_enabled = QCheckBox("Entrée par carte d'employé / ID")
        self.card_enabled.setChecked(self.db.get_setting('card_enabled') == '1')
        methods_layout.addWidget(self.card_enabled)

        self.qr_enabled = QCheckBox("Numérisation de code QR")
        self.qr_enabled.setChecked(self.db.get_setting('qr_enabled') == '1')
        methods_layout.addWidget(self.qr_enabled)

        self.face_enabled = QCheckBox("Reconnaissance faciale")
        self.face_enabled.setChecked(self.db.get_setting('face_enabled') == '1')
        methods_layout.addWidget(self.face_enabled)

        layout.addLayout(methods_layout)

        save_btn = QPushButton("Enregistrer les paramètres")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

    def setup_logs_tab(self):
        layout = QVBoxLayout()
        self.logs_tab.setLayout(layout)

        # Logs Table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(6)
        self.logs_table.setHorizontalHeaderLabels(["ID Employé", "Nom", "Action", "Heure", "Méthode", "Appareil"])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table readonly
        layout.addWidget(self.logs_table)

        # Refresh and Export buttons
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Actualiser les journaux")
        refresh_btn.clicked.connect(self.load_logs)
        button_layout.addWidget(refresh_btn)

        export_btn = QPushButton("Exporter les journaux en CSV")
        export_btn.clicked.connect(self.export_logs)
        button_layout.addWidget(export_btn)

        layout.addLayout(button_layout)

    def add_employee(self):
        emp_id = self.emp_id_input.text().strip()
        name = self.emp_name_input.text().strip()
        
        if not emp_id or not name:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir l'ID et le nom.")
            return
        
        # Add to database
        success = self.db.add_employee(emp_id, name)
        if success:
            QMessageBox.information(self, "Succès", f"Employé {name} ajouté avec succès.")
            self.emp_id_input.clear()
            self.emp_name_input.clear()
            self.load_employees()
        else:
            QMessageBox.warning(self, "Erreur", f"L'ID employé {emp_id} existe déjà.")
            self.emp_name_input.clear()
            self.load_employees()

    def view_profile(self, employee_id):
        """Open employee profile dialog"""
        dialog = EmployeeProfileDialog(self.db, employee_id)
        dialog.exec_()
        # Refresh the table after dialog closes
        self.load_employees()

    def load_employees(self):
        """Load all employees into the table"""
        employees = self.db.get_all_employees()
        self.employee_table.setRowCount(len(employees))
        
        for row, emp in enumerate(employees):
            self.employee_table.setItem(row, 0, QTableWidgetItem(emp.employee_id))
            self.employee_table.setItem(row, 1, QTableWidgetItem(emp.name))
            self.employee_table.setItem(row, 2, QTableWidgetItem("Enabled" if emp.enabled else "Disabled"))
            self.employee_table.setItem(row, 3, QTableWidgetItem("✓" if emp.qr_code else "✗"))
            self.employee_table.setItem(row, 4, QTableWidgetItem("✓" if emp.face_image else "✗"))
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            # Profile button
            profile_btn = QPushButton("Profile")
            profile_btn.setToolTip("Voir/Modifier le profil employé")
            profile_btn.clicked.connect(lambda checked, eid=emp.employee_id: self.view_profile(eid))
            action_layout.addWidget(profile_btn)
            
            action_widget.setLayout(action_layout)
            self.employee_table.setCellWidget(row, 5, action_widget)
    
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
                QMessageBox.information(self, "Succès", f"Code QR généré et enregistré dans {filename}")
                self.load_employees()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de génération du code QR : {str(e)}")
    
    def set_face(self, employee_id):
        """Set face image for employee using camera"""
        from utils.face_recognition import FaceRecognition
        
        face_rec = FaceRecognition()
        
        # Get employee info
        emp = self.db.get_employee(employee_id)
        if not emp:
            QMessageBox.critical(self, "Erreur", "Employé introuvable.")
            return
        
        # Test camera
        if not face_rec.test_camera():
            QMessageBox.critical(self, "Erreur", "Aucune caméra détectée.")
            return
        
        # Show instructions
        QMessageBox.information(self, "Enregistrement facial", 
                               f"📷 Enregistrement facial pour {emp.name}\n\n"
                               "Instructions :\n"
                               "1. Positionnez-vous face à la caméra\n"
                               "2. Appuyez sur ESPACE pour capturer\n"
                               "3. Appuyez sur Q pour annuler",
                               QMessageBox.Ok)
        
        # Capture face
        result = face_rec.capture_face_for_enrollment()
        
        if result is None:
            QMessageBox.warning(self, "Erreur", "Échec de la capture faciale.")
            return
            
        face_data, message = result
        
        if face_data is None:
            QMessageBox.warning(self, "Capture annulée", f"Capture annulée.\n\n{message}")
            return
        
        try:
            face_bytes = face_data.tobytes()
            self.db.update_employee_face(employee_id, face_bytes)
            QMessageBox.information(self, "Succès", f"Image faciale définie pour {emp.name}")
            self.load_employees()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de définition de l'image faciale : {str(e)}")

    def toggle_employee(self, employee_id, new_status):
        """Enable or disable an employee"""
        self.db.update_employee_status(employee_id, new_status)
        self.load_employees()
        QMessageBox.information(self, "Succès", f"Employé {employee_id} {'activé' if new_status else 'désactivé'}.")

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

        QMessageBox.information(self, "Succès", "Paramètres enregistrés avec succès.")

    def export_logs(self):
        """Export logs to CSV file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Exporter les journaux", 
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
                
                QMessageBox.information(self, "Succès", f"Journaux exportés vers {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec d'exportation des journaux : {str(e)}")

    def logout(self):
        self.close()
        self.public.show()