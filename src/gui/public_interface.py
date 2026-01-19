"""
Interface publique pour SLAT - Enregistrement de présence des employés.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QMessageBox, QInputDialog, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap
import datetime
import socket
import os
from database import Database
from utils.qr_scanner import QRScanner

class PublicInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.qr_scanner = QRScanner()
        self.setWindowTitle("SLAT - Terminal de Présence")
        self.showFullScreen()
        self.current_method = None
        self.f11_press_count = 0
        self.f11_reset_timer = QTimer()
        self.f11_reset_timer.timeout.connect(self.reset_f11_count)

        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 240, 245))
        self.setPalette(palette)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(50, 50, 50, 50)
        self.layout.setSpacing(20)
        self.setLayout(self.layout)

        # Add top spacer
        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Society logo and name
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        
        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'logo.png')
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio))
            logo_layout.addWidget(logo_label)
        
        # Society name
        society_label = QLabel("Facility Plus")
        society_label.setFont(QFont("Arial", 24, QFont.Bold))
        society_label.setAlignment(Qt.AlignCenter)
        society_label.setStyleSheet("color: #2C3E50; padding: 10px;")
        logo_layout.addWidget(society_label)
        
        self.layout.addLayout(logo_layout)

        # Current date and time display
        self.datetime_label = QLabel()
        self.datetime_label.setFont(QFont("Arial", 18))
        self.datetime_label.setAlignment(Qt.AlignCenter)
        self.datetime_label.setStyleSheet("color: #333333;")
        self.layout.addWidget(self.datetime_label)

        # Update time every second
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_datetime)
        self.time_timer.start(1000)
        self.update_datetime()

        # Title
        title = QLabel("TERMINAL DE PRÉSENCE LOCAL SÉCURISÉ")
        title.setFont(QFont("Arial", 36, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2C3E50; padding: 20px;")
        self.layout.addWidget(title)

        # Subtitle with developer info
        subtitle = QLabel("SLAT - Développé par Innovista Dev")
        subtitle.setFont(QFont("Arial", 16))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #7F8C8D; padding: 5px;")
        self.layout.addWidget(subtitle)

        # Current window info
        self.window_info_label = QLabel()
        self.window_info_label.setFont(QFont("Arial", 16))
        self.window_info_label.setAlignment(Qt.AlignCenter)
        self.window_info_label.setStyleSheet("color: #7F8C8D; padding: 10px;")
        self.layout.addWidget(self.window_info_label)
        self.update_window_info()

        # Window info update timer
        self.window_timer = QTimer()
        self.window_timer.timeout.connect(self.update_window_info)
        self.window_timer.start(60000)  # Update every minute

        self.setup_method_buttons()

    def is_within_time_window(self):
        """Check if current time is within allowed attendance windows."""
        now = datetime.datetime.now()
        current_time = now.time()
        
        morning_start_str = self.db.get_setting('morning_start')
        morning_end_str = self.db.get_setting('morning_end')
        afternoon_start_str = self.db.get_setting('afternoon_start')
        afternoon_end_str = self.db.get_setting('afternoon_end')
        
        try:
            morning_start = datetime.datetime.strptime(morning_start_str, '%H:%M').time()
            morning_end = datetime.datetime.strptime(morning_end_str, '%H:%M').time()
            afternoon_start = datetime.datetime.strptime(afternoon_start_str, '%H:%M').time()
            afternoon_end = datetime.datetime.strptime(afternoon_end_str, '%H:%M').time()
            
            return (morning_start <= current_time <= morning_end) or (afternoon_start <= current_time <= afternoon_end)
        except:
            return False  # If settings are invalid, assume outside window

    def setup_method_buttons(self):
        """Setup method selection buttons, only if within time window."""
        # Remove existing method buttons if they exist
        if hasattr(self, 'method_label') and self.method_label:
            self.layout.removeWidget(self.method_label)
            self.method_label.deleteLater()
        if hasattr(self, 'buttons_layout'):
            # Remove all widgets from buttons_layout
            while self.buttons_layout.count():
                item = self.buttons_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.layout.removeItem(self.buttons_layout)
            self.buttons_layout.deleteLater()

        # Check if within time window
        if not self.is_within_time_window():
            # Show message instead of buttons
            self.method_label = QLabel("⏰ Présence non disponible en ce moment\n\nVeuillez revenir pendant les heures d'ouverture.")
            self.method_label.setFont(QFont("Arial", 20))
            self.method_label.setAlignment(Qt.AlignCenter)
            self.method_label.setStyleSheet("color: #E74C3C; padding: 20px;")
            self.layout.addWidget(self.method_label)
            return

        # Method selection buttons
        self.method_label = QLabel("Sélectionnez la méthode d'identification :")
        self.method_label.setFont(QFont("Arial", 20))
        self.method_label.setAlignment(Qt.AlignCenter)
        self.method_label.setStyleSheet("color: #34495E; padding: 10px;")
        self.layout.addWidget(self.method_label)

        # Buttons layout
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(20)
        
        # Check which methods are enabled
        card_enabled = self.db.get_setting('card_enabled') == '1'
        qr_enabled = self.db.get_setting('qr_enabled') == '1'
        face_enabled = self.db.get_setting('face_enabled') == '1'
        
        # Employee ID Button
        if card_enabled:
            self.id_btn = QPushButton("📇\nID Employé")
            self.id_btn.setFont(QFont("Arial", 18, QFont.Bold))
            self.id_btn.setMinimumSize(200, 150)
            self.id_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border-radius: 15px;
                    padding: 20px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
                QPushButton:pressed {
                    background-color: #21618C;
                }
            """)
            self.id_btn.clicked.connect(self.show_id_input)
            self.buttons_layout.addWidget(self.id_btn)
        
        # QR Code Button
        if qr_enabled:
            self.qr_btn = QPushButton("📱\nCode QR")
            self.qr_btn.setFont(QFont("Arial", 18, QFont.Bold))
            self.qr_btn.setMinimumSize(200, 150)
            self.qr_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2ECC71;
                    color: white;
                    border-radius: 15px;
                    padding: 20px;
                }
                QPushButton:hover {
                    background-color: #27AE60;
                }
                QPushButton:pressed {
                    background-color: #1E8449;
                }
            """)
            self.qr_btn.clicked.connect(self.show_qr_scanner)
            self.buttons_layout.addWidget(self.qr_btn)
        
        # Face Recognition Button
        if face_enabled:
            self.face_btn = QPushButton("👤\nScan Visage")
            self.face_btn.setFont(QFont("Arial", 18, QFont.Bold))
            self.face_btn.setMinimumSize(200, 150)
            self.face_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9B59B6;
                    color: white;
                    border-radius: 15px;
                    padding: 20px;
                }
                QPushButton:hover {
                    background-color: #8E44AD;
                }
                QPushButton:pressed {
                    background-color: #7D3C98;
                }
            """)
            self.face_btn.clicked.connect(self.show_face_scanner)
            self.buttons_layout.addWidget(self.face_btn)
        
        self.layout.addLayout(self.buttons_layout)

        # Input area (hidden initially)
        self.input_container = QWidget()
        self.input_layout = QVBoxLayout()
        self.input_container.setLayout(self.input_layout)
        
        # Instruction label
        self.instruction_label = QLabel("")
        self.instruction_label.setFont(QFont("Arial", 18))
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet("color: #34495E; padding: 10px;")
        self.input_layout.addWidget(self.instruction_label)
        
        # Input field with styling
        self.id_input = QLineEdit()
        self.id_input.setFont(QFont("Arial", 28))
        self.id_input.setAlignment(Qt.AlignCenter)
        self.id_input.setPlaceholderText("Entrez l'ID employé")
        self.id_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 3px solid #3498DB;
                border-radius: 10px;
                background-color: white;
                min-height: 60px;
                max-width: 600px;
            }
            QLineEdit:focus {
                border: 3px solid #2980B9;
                background-color: #F8F9FA;
            }
        """)
        self.id_input.setMaxLength(20)
        self.id_input.returnPressed.connect(self.process_attendance)
        self.input_layout.addWidget(self.id_input, 0, Qt.AlignCenter)
        
        # Submit and Back buttons
        self.button_row = QHBoxLayout()
        
        self.submit_btn = QPushButton("✓ Valider")
        self.submit_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.submit_btn.setMinimumSize(150, 50)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.submit_btn.clicked.connect(self.process_attendance)
        self.button_row.addWidget(self.submit_btn)
        
        self.back_btn = QPushButton("← Retour")
        self.back_btn.setFont(QFont("Arial", 16))
        self.back_btn.setMinimumSize(150, 50)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        self.back_btn.clicked.connect(self.show_method_selection)
        self.button_row.addWidget(self.back_btn)
        
        self.input_layout.addLayout(self.button_row)
        
        self.input_container.hide()
        self.layout.addWidget(self.input_container)

        # Status message with styling
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Arial", 22, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(100)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                border-radius: 10px;
                background-color: transparent;
            }
        """)
        self.layout.addWidget(self.status_label)

        # Add bottom spacer
        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Footer hint
        footer = QLabel("Veuillez ne pas partager vos identifiants de connexion avec d'autres.")
        footer.setFont(QFont("Arial", 10))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #95A5A6;")
        self.layout.addWidget(footer)

        # Admin access (hidden)
        self.f11_press_count = 0
        self.f11_reset_timer = QTimer()
        self.f11_reset_timer.setSingleShot(True)
        self.f11_reset_timer.timeout.connect(self.reset_f11_count)

        # Initialize idle timer to clear messages and input
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self.reset_interface)
        self.idle_timer.setSingleShot(True)

        # Track last attendance time to prevent duplicates
        self.last_attendance = {}
    
    def show_method_selection(self):
        """Show method selection buttons and hide input."""
        self.input_container.hide()
        self.setup_method_buttons()  # Ensure buttons are properly set up
        self.status_label.setText("")
        self.current_method = None
    
    def show_id_input(self):
        """Show ID input field."""
        self.current_method = "ID"
        self.method_label.hide()
        for i in range(self.buttons_layout.count()):
            widget = self.buttons_layout.itemAt(i).widget()
            if widget:
                widget.hide()
        self.instruction_label.setText("Entrez votre ID employé :")
        self.id_input.clear()
        self.id_input.setPlaceholderText("Entrez l'ID employé")
        self.input_container.show()
        self.id_input.setFocus()
    
    def show_qr_scanner(self):
        """Scan QR code and process attendance."""
        self.current_method = "QR"
        
        # Check if camera is available
        if not self.qr_scanner.test_camera():
            QMessageBox.critical(self, "Erreur de caméra", 
                               "❌ Aucune caméra détectée.\n\n"
                               "Veuillez vous assurer qu'une caméra est connectée et réessayez.",
                               QMessageBox.Ok)
            self.show_method_selection()
            return
        
        # Show scanning message
        QMessageBox.information(self, "Scanner QR", 
                               "📱 Scanner de code QR\n\n"
                               "Placez votre code QR devant la caméra.\n"
                               "Le scanner le détectera et le traitera automatiquement.\n\n"
                               "Appuyez sur 'q' dans la fenêtre de caméra pour annuler.",
                               QMessageBox.Ok)
        
        # Scan QR code
        qr_data = self.qr_scanner.scan_qr_code()
        
        if qr_data:
            # Process the scanned QR data as employee ID
            self.process_qr_attendance(qr_data)
        else:
            # No QR code found or cancelled
            QMessageBox.warning(self, "Scan annulé", 
                               "⚠ Le scan du code QR a été annulé ou aucun code n'a été détecté.\n\n"
                               "Veuillez réessayer ou utiliser une autre méthode.",
                               QMessageBox.Ok)
            self.show_method_selection()
    
    def process_qr_attendance(self, employee_id):
        """Process attendance for scanned QR code."""
        try:
            if not employee_id:
                QMessageBox.warning(self, "Code QR invalide", 
                                   "⚠ Le code QR scanné ne contient pas de données valides.",
                                   QMessageBox.Ok)
                self.show_method_selection()
                return

            # Check if employee exists and enabled
            emp = self.db.get_employee(employee_id)
            if not emp:
                QMessageBox.critical(self, "Non trouvé", 
                                    f"✗ ID employé '{employee_id}' introuvable.\n\n"
                                    "Veuillez vérifier votre code QR ou contacter l'administrateur.",
                                    QMessageBox.Ok)
                self.show_method_selection()
                return
            
            if not emp.enabled:
                QMessageBox.critical(self, "Compte désactivé", 
                                    "✗ Votre compte a été désactivé.\n\n"
                                    "Veuillez contacter l'administrateur.",
                                    QMessageBox.Ok)
                self.show_method_selection()
                return

            # Check for recent attendance (prevent duplicate within same window)
            recent_logs = self.db.get_employee_logs(employee_id)
            if recent_logs:
                last_log = recent_logs[0]  # Most recent log
                last_timestamp = last_log.timestamp
                last_action = last_log.action  # 'IN' or 'OUT'
                last_time_str = last_timestamp.strftime("%H:%M")
                time_diff = datetime.datetime.now() - last_timestamp
                
                # If last attendance was within 5 minutes, prevent duplicate
                if time_diff.total_seconds() < 300:  # 5 minutes
                    QMessageBox.warning(self, "Doublon détecté", 
                                       f"⚠ Vous avez déjà pointé {last_action} à {last_time_str}.\n\n"
                                       "Veuillez attendre au moins 5 minutes avant de pointer à nouveau.",
                                       QMessageBox.Ok)
                    self.show_method_selection()
                    return

            # Determine attendance window and action
            now = datetime.datetime.now()
            current_time = now.time()
            current_str = now.strftime("%H:%M")
            
            morning_start_str = self.db.get_setting('morning_start')
            morning_end_str = self.db.get_setting('morning_end')
            afternoon_start_str = self.db.get_setting('afternoon_start')
            afternoon_end_str = self.db.get_setting('afternoon_end')

            morning_start = datetime.datetime.strptime(morning_start_str, '%H:%M').time()
            morning_end = datetime.datetime.strptime(morning_end_str, '%H:%M').time()
            afternoon_start = datetime.datetime.strptime(afternoon_start_str, '%H:%M').time()
            afternoon_end = datetime.datetime.strptime(afternoon_end_str, '%H:%M').time()

            action = None
            window_name = ""
            if morning_start <= current_time <= morning_end:
                action = "IN"
                window_name = "ARRIVÉE"
            elif afternoon_start <= current_time <= afternoon_end:
                action = "OUT"
                window_name = "DÉPART"
            else:
                # Show when next window opens
                if current_time < morning_start:
                    next_window = f"La arrivée du matin ouvre à {morning_start_str}"
                elif current_time < afternoon_start:
                    next_window = f"Le départ de l'après-midi ouvre à {afternoon_start_str}"
                else:
                    next_window = f"Prochaine arrivée demain à {morning_start_str}"
                
                QMessageBox.warning(self, "Hors fenêtre", 
                                   f"⚠ Présence non autorisée à cette heure.\n\n{next_window}",
                                   QMessageBox.Ok)
                self.show_method_selection()
                return

            # Record attendance
            device_id = socket.gethostname()
            self.db.record_attendance(employee_id, action, 'qr', device_id)
            
            # Show success message
            QMessageBox.information(self, "Succès", 
                                   f"✓ {window_name} RÉUSSIE\n\n"
                                   f"{emp.name}\n"
                                   f"Time: {current_str}\n"
                                   f"Method: QR Code",
                                   QMessageBox.Ok)
            self.show_method_selection()
            
        except Exception as e:
            import traceback
            error_msg = f"System Error:\n{str(e)}"
            print(f"Error in process_qr_attendance: {traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"✗ {error_msg}", QMessageBox.Ok)
            self.show_method_selection()
    
    def show_face_scanner(self):
        """Show face recognition (placeholder for now)."""
        self.current_method = "FACE"
        QMessageBox.information(self, "Face Recognition", 
                               "Face recognition scanning will be implemented.\n\n"
                               "For now, employees can enter their ID manually.",
                               QMessageBox.Ok)
        self.show_id_input()

    def update_datetime(self):
        """Update the current date and time display."""
        now = QDateTime.currentDateTime()
        self.datetime_label.setText(now.toString("dddd, MMMM d, yyyy | HH:mm:ss"))

    def update_window_info(self):
        """Update the current attendance window information."""
        now = datetime.datetime.now()
        current_time = now.time()
        
        morning_start_str = self.db.get_setting('morning_start')
        morning_end_str = self.db.get_setting('morning_end')
        afternoon_start_str = self.db.get_setting('afternoon_start')
        afternoon_end_str = self.db.get_setting('afternoon_end')

        morning_start = datetime.datetime.strptime(morning_start_str, '%H:%M').time()
        morning_end = datetime.datetime.strptime(morning_end_str, '%H:%M').time()
        afternoon_start = datetime.datetime.strptime(afternoon_start_str, '%H:%M').time()
        afternoon_end = datetime.datetime.strptime(afternoon_end_str, '%H:%M').time()

        if morning_start <= current_time <= morning_end:
            self.window_info_label.setText(f"✓ Fenêtre ARRIVÉE Active  ({morning_start_str} - {morning_end_str})")
            self.window_info_label.setStyleSheet("color: #27AE60; font-weight: bold; padding: 10px; font-size: 18px;")
        elif afternoon_start <= current_time <= afternoon_end:
            self.window_info_label.setText(f"✓ Fenêtre DÉPART Active  ({afternoon_start_str} - {afternoon_end_str})")
            self.window_info_label.setStyleSheet("color: #E67E22; font-weight: bold; padding: 10px; font-size: 18px;")
        else:
            # Show next window
            if current_time < morning_start:
                self.window_info_label.setText(f"Prochaine fenêtre : ARRIVÉE à {morning_start_str}")
            elif current_time < afternoon_start:
                self.window_info_label.setText(f"Prochaine fenêtre : DÉPART à {afternoon_start_str}")
            else:
                self.window_info_label.setText(f"Prochaine fenêtre : ARRIVÉE demain à {morning_start_str}")
            self.window_info_label.setStyleSheet("color: #E74C3C; padding: 10px; font-size: 16px;")
        
        # Update method buttons visibility based on time window
        self.setup_method_buttons()

    def keyPressEvent(self, event):
        """Handle keyboard events."""
        if event.key() == Qt.Key_F11:  # Hidden key for admin
            self.f11_press_count += 1
            self.f11_reset_timer.start(2000)  # Reset count after 2 seconds of no presses
            
            if self.f11_press_count >= 5:
                self.reset_f11_count()
                self.show_admin_prompt()
        elif event.key() == Qt.Key_Escape:
            # Allow ESC to clear input and return to method selection
            self.reset_interface()
        else:
            super().keyPressEvent(event)

    def reset_f11_count(self):
        """Reset the F11 press count."""
        self.f11_press_count = 0
        self.f11_reset_timer.stop()

    def show_admin_prompt(self):
        """Prompt for admin password."""
        password, ok = QInputDialog.getText(self, 'Admin Access', 'Enter admin password:', QLineEdit.Password)
        if ok and password:
            admin_pass_hash = self.db.get_setting('admin_password')
            if self.db.verify_password(password, admin_pass_hash):
                self.open_admin()
            else:
                QMessageBox.warning(self, 'Access Denied', 'Incorrect password.')

    def open_admin(self):
        """Open the admin interface."""
        from gui.admin_interface import AdminInterface
        self.admin_window = AdminInterface(self.db, self)
        self.admin_window.show()
        self.hide()

    def process_attendance(self):
        """Process attendance for employee ID."""
        try:
            employee_id = self.id_input.text().strip()
            if not employee_id:
                QMessageBox.warning(self, "Input Required", 
                                   "⚠ Please enter your Employee ID.",
                                   QMessageBox.Ok)
                self.id_input.setFocus()
                return

            # Check if employee exists and enabled
            emp = self.db.get_employee(employee_id)
            if not emp:
                QMessageBox.critical(self, "Not Found", 
                                    f"✗ Employee ID '{employee_id}' not found.\n\n"
                                    "Please check your ID and try again.",
                                    QMessageBox.Ok)
                self.id_input.clear()
                self.id_input.setFocus()
                return
            
            if not emp.enabled:
                QMessageBox.critical(self, "Account Disabled", 
                                    "✗ Your account has been disabled.\n\n"
                                    "Please contact the administrator.",
                                    QMessageBox.Ok)
                self.reset_interface()
                return

            # Check for recent attendance (prevent duplicate within same window)
            recent_logs = self.db.get_employee_logs(employee_id)
            if recent_logs:
                last_log = recent_logs[0]  # Most recent log
                last_timestamp = last_log.timestamp
                last_action = last_log.action  # 'IN' or 'OUT'
                last_time_str = last_timestamp.strftime("%H:%M")
                time_diff = datetime.datetime.now() - last_timestamp
                
                # If last attendance was within 5 minutes, prevent duplicate
                if time_diff.total_seconds() < 300:  # 5 minutes
                    QMessageBox.warning(self, "Duplicate Detected", 
                                       f"⚠ You already checked {last_action} at {last_time_str}.\n\n"
                                       "Please wait at least 5 minutes before checking again.",
                                       QMessageBox.Ok)
                    self.reset_interface()
                    return

            # Determine attendance window and action
            now = datetime.datetime.now()
            current_time = now.time()
            current_str = now.strftime("%H:%M")
            
            morning_start_str = self.db.get_setting('morning_start')
            morning_end_str = self.db.get_setting('morning_end')
            afternoon_start_str = self.db.get_setting('afternoon_start')
            afternoon_end_str = self.db.get_setting('afternoon_end')

            morning_start = datetime.datetime.strptime(morning_start_str, '%H:%M').time()
            morning_end = datetime.datetime.strptime(morning_end_str, '%H:%M').time()
            afternoon_start = datetime.datetime.strptime(afternoon_start_str, '%H:%M').time()
            afternoon_end = datetime.datetime.strptime(afternoon_end_str, '%H:%M').time()

            action = None
            window_name = ""
            if morning_start <= current_time <= morning_end:
                action = "IN"
                window_name = "CHECK IN"
            elif afternoon_start <= current_time <= afternoon_end:
                action = "OUT"
                window_name = "CHECK OUT"
            else:
                # Show when next window opens
                if current_time < morning_start:
                    next_window = f"Morning check-in opens at {morning_start_str}"
                elif current_time < afternoon_start:
                    next_window = f"Afternoon check-out opens at {afternoon_start_str}"
                else:
                    next_window = f"Next check-in tomorrow at {morning_start_str}"
                
                QMessageBox.warning(self, "Outside Window", 
                                   f"⚠ Attendance not allowed at this time.\n\n{next_window}",
                                   QMessageBox.Ok)
                self.reset_interface()
                return

            # Record attendance
            device_id = socket.gethostname()
            self.db.record_attendance(employee_id, action, 'card', device_id)
            
            # Show success message
            QMessageBox.information(self, "Success", 
                                   f"✓ {window_name} SUCCESSFUL\n\n"
                                   f"{emp.name}\n"
                                   f"Time: {current_str}",
                                   QMessageBox.Ok)
            self.reset_interface()
            
        except Exception as e:
            import traceback
            error_msg = f"System Error:\n{str(e)}"
            print(f"Error in process_attendance: {traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"✗ {error_msg}", QMessageBox.Ok)
            self.reset_interface()

    def reset_interface(self):
        """Reset the interface to initial state."""
        self.id_input.clear()
        self.status_label.setText("")
        self.show_method_selection()
        self.update_window_info()
