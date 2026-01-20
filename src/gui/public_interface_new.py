"""
Interface publique pour SLAT - Terminal de présence passif.
Le mode est défini par l'admin, la caméra est toujours active, pas d'interaction utilisateur.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QDateTime, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QImage
import datetime
import os
import cv2
import numpy as np
from database import Database
from utils.qr_scanner import QRScanner
from utils import face_recognition

class PublicInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setWindowTitle("SLAT - Terminal de Présence")
        self.showFullScreen()
        self.f11_press_count = 0
        self.f11_reset_timer = QTimer()
        self.f11_reset_timer.timeout.connect(self.reset_f11_count)
        
        # Camera and scanning state
        self.camera = None
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.process_camera_frame)
        self.last_scan_time = None
        self.scan_cooldown = 3  # seconds between scans
        
        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 240, 245))
        self.setPalette(palette)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)
        self.setLayout(self.layout)

        # Top section: Logo, title, time
        self.setup_header()
        
        # Middle section: Camera feed or ID input
        self.setup_main_area()
        
        # Bottom section: Status feedback
        self.setup_status_area()
        
        # Footer
        self.setup_footer()

        # Start the appropriate mode
        self.start_attendance_mode()

    def setup_header(self):
        """Setup header with logo, title, and time"""
        # Society logo and name
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        
        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'logo.png')
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio))
            logo_layout.addWidget(logo_label)
        
        # Society name
        society_label = QLabel("Facility Plus")
        society_label.setFont(QFont("Arial", 22, QFont.Bold))
        society_label.setAlignment(Qt.AlignCenter)
        society_label.setStyleSheet("color: #2C3E50; padding: 10px;")
        logo_layout.addWidget(society_label)
        
        self.layout.addLayout(logo_layout)

        # Current date and time display
        self.datetime_label = QLabel()
        self.datetime_label.setFont(QFont("Arial", 16))
        self.datetime_label.setAlignment(Qt.AlignCenter)
        self.datetime_label.setStyleSheet("color: #333333;")
        self.layout.addWidget(self.datetime_label)

        # Update time every second
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_datetime)
        self.time_timer.start(1000)
        self.update_datetime()

        # Title
        title = QLabel("TERMINAL DE PRÉSENCE")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2C3E50; padding: 15px;")
        self.layout.addWidget(title)

        # Current window info
        self.window_info_label = QLabel()
        self.window_info_label.setFont(QFont("Arial", 14))
        self.window_info_label.setAlignment(Qt.AlignCenter)
        self.window_info_label.setStyleSheet("color: #7F8C8D; padding: 5px;")
        self.layout.addWidget(self.window_info_label)
        self.update_window_info()

        # Window info update timer
        self.window_timer = QTimer()
        self.window_timer.timeout.connect(self.update_window_info)
        self.window_timer.start(60000)

    def setup_main_area(self):
        """Setup main area for camera or ID input"""
        self.main_container = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_container.setLayout(self.main_layout)
        
        # Mode indicator
        self.mode_label = QLabel()
        self.mode_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("color: #3498DB; padding: 10px;")
        self.main_layout.addWidget(self.mode_label)
        
        # Camera display label
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setMaximumSize(800, 600)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 3px solid #3498DB;
                border-radius: 10px;
                background-color: #2C3E50;
            }
        """)
        self.camera_label.hide()
        self.main_layout.addWidget(self.camera_label, 0, Qt.AlignCenter)
        
        # ID input area (for card mode)
        self.id_container = QWidget()
        self.id_layout = QVBoxLayout()
        self.id_container.setLayout(self.id_layout)
        
        instruction = QLabel("Entrez votre ID employé")
        instruction.setFont(QFont("Arial", 16))
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet("color: #34495E; padding: 10px;")
        self.id_layout.addWidget(instruction)
        
        self.id_input = QLineEdit()
        self.id_input.setFont(QFont("Arial", 24))
        self.id_input.setAlignment(Qt.AlignCenter)
        self.id_input.setPlaceholderText("ID Employé")
        self.id_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 3px solid #3498DB;
                border-radius: 10px;
                background-color: white;
                min-height: 60px;
                max-width: 500px;
            }
            QLineEdit:focus {
                border: 3px solid #2980B9;
            }
        """)
        self.id_input.setMaxLength(20)
        self.id_input.returnPressed.connect(self.process_id_input)
        self.id_layout.addWidget(self.id_input, 0, Qt.AlignCenter)
        
        self.id_container.hide()
        self.main_layout.addWidget(self.id_container)
        
        self.layout.addWidget(self.main_container)

    def setup_status_area(self):
        """Setup status feedback area"""
        self.status_container = QWidget()
        self.status_layout = QVBoxLayout()
        self.status_container.setLayout(self.status_layout)
        
        # Employee photo
        self.employee_photo = QLabel()
        self.employee_photo.setAlignment(Qt.AlignCenter)
        self.employee_photo.setFixedSize(120, 120)
        self.employee_photo.setStyleSheet("""
            QLabel {
                border: 2px solid #BDC3C7;
                border-radius: 60px;
                background-color: white;
            }
        """)
        self.employee_photo.hide()
        self.status_layout.addWidget(self.employee_photo, 0, Qt.AlignCenter)
        
        # Employee name
        self.employee_name_label = QLabel()
        self.employee_name_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.employee_name_label.setAlignment(Qt.AlignCenter)
        self.employee_name_label.setStyleSheet("color: #2C3E50; padding: 5px;")
        self.employee_name_label.hide()
        self.status_layout.addWidget(self.employee_name_label)
        
        # Status message
        self.status_label = QLabel()
        self.status_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(80)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                border-radius: 10px;
            }
        """)
        self.status_layout.addWidget(self.status_label)
        
        self.layout.addWidget(self.status_container)

    def setup_footer(self):
        """Setup footer"""
        self.layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        footer = QLabel("Développé par Innovista Dev")
        footer.setFont(QFont("Arial", 10))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #95A5A6; padding: 5px;")
        self.layout.addWidget(footer)

    def start_attendance_mode(self):
        """Start the terminal in the configured mode"""
        mode = self.db.get_setting('attendance_mode')
        
        if mode == 'qr':
            self.start_qr_mode()
        elif mode == 'face':
            self.start_face_mode()
        else:  # card
            self.start_card_mode()

    def start_qr_mode(self):
        """Start QR scanning mode"""
        self.mode_label.setText("🔲 MODE SCAN QR")
        self.camera_label.show()
        self.id_container.hide()
        
        # Start camera
        self.camera = cv2.VideoCapture(0)
        if self.camera.isOpened():
            self.camera_timer.start(30)  # ~33 FPS
        else:
            self.show_status("❌ Erreur caméra", "error")

    def start_face_mode(self):
        """Start face recognition mode"""
        self.mode_label.setText("👤 MODE RECONNAISSANCE FACIALE")
        self.camera_label.show()
        self.id_container.hide()
        
        # Start camera
        self.camera = cv2.VideoCapture(0)
        if self.camera.isOpened():
            self.camera_timer.start(30)
        else:
            self.show_status("❌ Erreur caméra", "error")

    def start_card_mode(self):
        """Start ID card input mode"""
        self.mode_label.setText("🔢 MODE CARTE ID")
        self.camera_label.hide()
        self.id_container.show()
        self.id_input.setFocus()

    def process_camera_frame(self):
        """Process camera frames for QR or Face detection"""
        if not self.camera or not self.camera.isOpened():
            return
        
        ret, frame = self.camera.read()
        if not ret:
            return
        
        # Check cooldown
        if self.last_scan_time:
            elapsed = (datetime.datetime.now() - self.last_scan_time).total_seconds()
            if elapsed < self.scan_cooldown:
                # Just display frame
                self.display_frame(frame)
                return
        
        mode = self.db.get_setting('attendance_mode')
        
        if mode == 'qr':
            self.process_qr_frame(frame)
        elif mode == 'face':
            self.process_face_frame(frame)

    def process_qr_frame(self, frame):
        """Detect and process QR codes"""
        # Try to decode QR
        qr_scanner = QRScanner()
        qr_data = qr_scanner.scan_frame(frame)
        
        if qr_data:
            # Draw detection box
            cv2.putText(frame, "QR DETECTE", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            self.display_frame(frame)
            
            # Process attendance
            self.last_scan_time = datetime.datetime.now()
            self.process_qr_attendance(qr_data)
        else:
            # Draw instruction
            cv2.putText(frame, "Presentez votre code QR", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            self.display_frame(frame)

    def process_face_frame(self, frame):
        """Detect and process faces using RetinaFace and ArcFace"""
        # Use the FaceRecognition class for consistent processing
        captured_embedding, raw_frame = self.face_recognizer.capture_face_for_recognition()
        
        if captured_embedding is not None and raw_frame is not None:
            # Get all employees with faces
            all_employees = self.db.get_all_employees()
            best_match = None
            best_confidence = 0
            
            for emp in all_employees:
                if emp.face_embedding:
                    try:
                        confidence = self.face_recognizer.match_face(emp.face_embedding, captured_embedding)
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = emp
                    except Exception as e:
                        print(f"Error matching face for {emp.name}: {e}")
                        continue
            
            # Process the result
            if best_match and self.face_recognizer.is_match_accepted(best_confidence):
                self.handle_successful_face_recognition(best_match, best_confidence, raw_frame)
            else:
                # Show frame with status
                if best_match:
                    status = f"Confiance insuffisante: {best_confidence:.1f}%"
                    color = (0, 165, 255)  # Orange
                else:
                    status = "Aucun employé reconnu"
                    color = (0, 0, 255)  # Red
                
                cv2.putText(raw_frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                self.display_frame(raw_frame)
        else:
            # No face detected or captured
            cv2.putText(frame, "Positionnez votre visage face à la caméra", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            self.display_frame(frame)
            if len(faces) == 0:
                cv2.putText(frame, "Aucun visage detecte", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            else:
                cv2.putText(frame, "Plusieurs visages detectes", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            
            self.display_frame(frame)

    def display_frame(self, frame):
        """Display camera frame in label"""
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        # Scale to fit label
        scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.camera_label.setPixmap(scaled_pixmap)

    def process_qr_attendance(self, qr_data):
        """Process QR code attendance"""
        employee = self.db.get_employee_by_qr(qr_data)
        
        if not employee:
            self.show_status("❌ Code QR non reconnu", "error", auto_clear=True)
            return
        
        if not employee.enabled:
            self.show_status(f"❌ {employee.name}\nCompte désactivé", "error", auto_clear=True)
            return
        
        # Check window and record
        self.record_attendance(employee)

    def handle_successful_face_recognition(self, employee, confidence, frame):
        """Handle successful face recognition"""
        # Draw success indicators on frame
        cv2.putText(frame, f"Reconnu: {employee.name}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Confiance: {confidence:.1f}%", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        self.display_frame(frame)
        
        # Process attendance
        self.last_scan_time = datetime.datetime.now()
        self.process_face_attendance(employee.employee_id, confidence)

    def process_face_attendance(self, employee_id, confidence):
        """Process face recognition attendance"""
        employee = self.db.get_employee(employee_id)
        
        if not employee:
            self.show_status("❌ Employé non trouvé", "error", auto_clear=True)
            return
        
        if not employee.enabled:
            self.show_status(f"❌ {employee.name}\nCompte désactivé", "error", auto_clear=True)
            return
        
        # Check window and record
        self.record_attendance(employee, extra_info=f"Confiance: {confidence:.0f}%")

    def process_id_input(self):
        """Process ID card input"""
        employee_id = self.id_input.text().strip()
        self.id_input.clear()
        
        if not employee_id:
            return
        
        employee = self.db.get_employee(employee_id)
        
        if not employee:
            self.show_status("❌ ID employé non trouvé", "error", auto_clear=True)
            return
        
        if not employee.enabled:
            self.show_status(f"❌ {employee.name}\nCompte désactivé", "error", auto_clear=True)
            return
        
        # Check window and record
        self.record_attendance(employee)

    def record_attendance(self, employee, extra_info=""):
        """Record attendance for employee"""
        now = datetime.datetime.now()
        current_time = now.time()
        
        morning_start = datetime.datetime.strptime(self.db.get_setting('morning_start'), '%H:%M').time()
        morning_end = datetime.datetime.strptime(self.db.get_setting('morning_end'), '%H:%M').time()
        afternoon_start = datetime.datetime.strptime(self.db.get_setting('afternoon_start'), '%H:%M').time()
        afternoon_end = datetime.datetime.strptime(self.db.get_setting('afternoon_end'), '%H:%M').time()

        action = None
        window_name = ""
        
        if morning_start <= current_time <= morning_end:
            action = "IN"
            window_name = "ARRIVÉE"
        elif afternoon_start <= current_time <= afternoon_end:
            action = "OUT"
            window_name = "DÉPART"
        else:
            self.show_status("❌ Hors fenêtre horaire", "error", auto_clear=True)
            return

        # Check for duplicate
        is_duplicate, dup_message = self.check_duplicate_attendance(employee.employee_id, action)
        if is_duplicate:
            self.show_status(f"❌ {employee.name}\n{dup_message}", "error", auto_clear=True)
            return

        # Record attendance
        self.db.add_attendance(employee.employee_id, action)
        
        # Show success
        success_msg = f"✓ {window_name}\n{now.strftime('%H:%M:%S')}"
        if extra_info:
            success_msg += f"\n{extra_info}"
        
        self.show_employee_info(employee, success_msg, "success", auto_clear=True)

    def check_duplicate_attendance(self, employee_id, action):
        """Check if employee already checked in/out in same window"""
        now = datetime.datetime.now()
        current_time = now.time()
        today = now.date()
        
        morning_start = datetime.datetime.strptime(self.db.get_setting('morning_start'), '%H:%M').time()
        afternoon_start = datetime.datetime.strptime(self.db.get_setting('afternoon_start'), '%H:%M').time()
        
        is_morning_window = current_time < afternoon_start
        
        recent_logs = self.db.get_employee_logs(employee_id)
        
        for log in recent_logs:
            log_date = log.timestamp.date()
            log_time = log.timestamp.time()
            log_action = log.action
            
            if log_date != today:
                continue
            
            log_is_morning = log_time < afternoon_start
            
            if is_morning_window == log_is_morning and log_action == action:
                window = "matin" if is_morning_window else "après-midi"
                action_fr = "arrivée" if action == "IN" else "départ"
                return True, f"Déjà pointé {action_fr} ce {window}"
        
        return False, ""

    def show_employee_info(self, employee, message, status_type, auto_clear=False):
        """Show employee info with photo"""
        # Show photo if available
        if employee.face_image:
            face_array = np.frombuffer(employee.face_image, dtype=np.uint8).reshape(150, 150)
            # Convert to RGB for display
            face_rgb = cv2.cvtColor(face_array, cv2.COLOR_GRAY2RGB) if len(face_array.shape) == 2 else face_array
            h, w = face_rgb.shape[:2]
            bytes_per_line = 3 * w
            qt_image = QImage(face_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.employee_photo.setPixmap(scaled_pixmap)
            self.employee_photo.show()
        else:
            self.employee_photo.hide()
        
        # Show name
        self.employee_name_label.setText(employee.name)
        self.employee_name_label.show()
        
        # Show status
        self.show_status(message, status_type, auto_clear=auto_clear)

    def show_status(self, message, status_type="info", auto_clear=False):
        """Show status message"""
        self.status_label.setText(message)
        
        if status_type == "success":
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #D5F4E6;
                    color: #27AE60;
                    padding: 15px;
                    border-radius: 10px;
                    border: 2px solid #27AE60;
                }
            """)
        elif status_type == "error":
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #FADBD8;
                    color: #E74C3C;
                    padding: 15px;
                    border-radius: 10px;
                    border: 2px solid #E74C3C;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #D6EAF8;
                    color: #2980B9;
                    padding: 15px;
                    border-radius: 10px;
                    border: 2px solid #2980B9;
                }
            """)
        
        if auto_clear:
            QTimer.singleShot(3000, self.clear_status)

    def clear_status(self):
        """Clear status display"""
        self.status_label.clear()
        self.status_label.setStyleSheet("QLabel { background-color: transparent; }")
        self.employee_name_label.hide()
        self.employee_photo.hide()

    def update_datetime(self):
        """Update date and time display"""
        now = QDateTime.currentDateTime()
        self.datetime_label.setText(now.toString("dddd d MMMM yyyy - HH:mm:ss"))

    def update_window_info(self):
        """Update current window information"""
        now = datetime.datetime.now()
        current_time = now.time()
        
        morning_start = self.db.get_setting('morning_start')
        morning_end = self.db.get_setting('morning_end')
        afternoon_start = self.db.get_setting('afternoon_start')
        afternoon_end = self.db.get_setting('afternoon_end')

        morning_start_time = datetime.datetime.strptime(morning_start, '%H:%M').time()
        morning_end_time = datetime.datetime.strptime(morning_end, '%H:%M').time()
        afternoon_start_time = datetime.datetime.strptime(afternoon_start, '%H:%M').time()
        afternoon_end_time = datetime.datetime.strptime(afternoon_end, '%H:%M').time()

        if morning_start_time <= current_time <= morning_end_time:
            self.window_info_label.setText(f"🔔 Fenêtre ARRIVÉE active ({morning_start} - {morning_end})")
            self.window_info_label.setStyleSheet("color: #27AE60; font-weight: bold; padding: 5px;")
        elif afternoon_start_time <= current_time <= afternoon_end_time:
            self.window_info_label.setText(f"🔔 Fenêtre DÉPART active ({afternoon_start} - {afternoon_end})")
            self.window_info_label.setStyleSheet("color: #E67E22; font-weight: bold; padding: 5px;")
        else:
            self.window_info_label.setText("⏰ Aucune fenêtre active")
            self.window_info_label.setStyleSheet("color: #95A5A6; padding: 5px;")

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_F11:
            self.f11_press_count += 1
            if self.f11_press_count == 1:
                self.f11_reset_timer.start(2000)
            elif self.f11_press_count >= 5:
                from gui.admin_interface import AdminInterface
                self.admin_window = AdminInterface(self.db)
                self.admin_window.show()
                self.close()
                self.f11_press_count = 0
                self.f11_reset_timer.stop()
        elif event.key() == Qt.Key_Escape:
            pass  # Ignore escape

    def reset_f11_count(self):
        """Reset F11 press counter"""
        self.f11_press_count = 0
        self.f11_reset_timer.stop()

    def closeEvent(self, event):
        """Cleanup on close"""
        if self.camera:
            self.camera.release()
        event.accept()
