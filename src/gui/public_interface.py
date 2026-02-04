"""
Interface publique pour SLAT - Terminal de présence passif.
Le mode est défini par l'admin, la caméra est toujours active, pas d'interaction utilisateur.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QSpacerItem, QSizePolicy, QInputDialog)
from PyQt5.QtCore import Qt, QTimer, QDateTime, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QImage, QPainter, QPen
import datetime
import os
import cv2
import numpy as np
import hashlib
import winsound
from pathlib import Path
from database import Database
from utils.qr_scanner import QRScanner
from utils.face_recognition import FaceRecognition

class PublicInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        # Initialize face recognizer only if face recognition is enabled
        if self.db.get_setting('face_enabled') == '1':
            self.face_recognizer = FaceRecognition()
        else:
            self.face_recognizer = None
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
        self.current_frame = None  # Store current frame for photo capture
        
        # Camera lifecycle management (session-based)
        self.camera_active = False  # Is camera currently active
        self.camera_session_timer = QTimer()  # Timer for 2-minute camera timeout
        self.camera_session_timer.timeout.connect(self.on_camera_session_timeout)
        self.camera_session_duration = 120  # 2 minutes in seconds
        self.camera_session_remaining = 0  # Remaining seconds
        
        # Countdown display timer (updates every second)
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_camera_countdown)
        self.countdown_timer.setInterval(1000)  # Update every second
        
        # Create photos directory
        self.photos_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'photos')
        os.makedirs(self.photos_dir, exist_ok=True)
        
        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 240, 245))
        self.setPalette(palette)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 15, 20, 15)
        self.layout.setSpacing(10)
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

    def play_sound(self, sound_type):
        """Play a beep sound for different events"""
        try:
            if sound_type == "start":
                winsound.Beep(600, 300)  # Medium tone for start
            elif sound_type == "in":
                # Arrival: ascending tones
                winsound.Beep(600, 150)
                winsound.Beep(800, 150)
            elif sound_type == "out":
                # Departure: descending tones
                winsound.Beep(800, 150)
                winsound.Beep(600, 150)
            elif sound_type == "error":
                winsound.Beep(400, 500)  # Low tone for error
            elif sound_type == "scan":
                winsound.Beep(700, 150)  # Quick beep for scan detection
        except Exception as e:
            print(f"Sound error: {e}")

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
            logo_label.setPixmap(logo_pixmap.scaled(60, 60, Qt.KeepAspectRatio))
            logo_layout.addWidget(logo_label)
        
        # Society name
        society_label = QLabel("Facility Plus")
        society_label.setFont(QFont("Arial", 18, QFont.Bold))
        society_label.setAlignment(Qt.AlignCenter)
        society_label.setStyleSheet("color: #2C3E50; padding: 10px;")
        logo_layout.addWidget(society_label)
        
        self.layout.addLayout(logo_layout)

        # Current date and time display
        self.datetime_label = QLabel()
        self.datetime_label.setFont(QFont("Arial", 13))
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
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2C3E50; padding: 15px;")
        self.layout.addWidget(title)

        # Current window info
        self.window_info_label = QLabel()
        self.window_info_label.setFont(QFont("Arial", 12))
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
        # Horizontal split layout
        self.main_container = QWidget()
        self.main_layout = QHBoxLayout()
        self.main_container.setLayout(self.main_layout)
        
        # Left side: Camera/Input area
        self.left_container = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_container.setLayout(self.left_layout)
        
        # Mode indicator
        self.mode_label = QLabel()
        self.mode_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("color: #3498DB; padding: 10px;")
        self.left_layout.addWidget(self.mode_label)
        
        # Add spacer
        self.left_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Camera display label
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setFixedSize(480, 360)
        self.camera_label.setScaledContents(False)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 3px solid #3498DB;
                border-radius: 10px;
                background-color: #2C3E50;
            }
        """)
        self.camera_label.hide()
        self.left_layout.addWidget(self.camera_label, 0, Qt.AlignCenter)
        
        # Camera session countdown display
        self.camera_countdown_label = QLabel()
        self.camera_countdown_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.camera_countdown_label.setAlignment(Qt.AlignCenter)
        self.camera_countdown_label.setStyleSheet("color: #E67E22; padding: 5px;")
        self.camera_countdown_label.hide()
        self.left_layout.addWidget(self.camera_countdown_label, 0, Qt.AlignCenter)
        
        # Camera activation instruction
        self.camera_instruction_label = QLabel()
        self.camera_instruction_label.setFont(QFont("Arial", 14))
        self.camera_instruction_label.setAlignment(Qt.AlignCenter)
        self.camera_instruction_label.setStyleSheet("color: #3498DB; padding: 10px;")
        self.camera_instruction_label.hide()
        self.left_layout.addWidget(self.camera_instruction_label, 0, Qt.AlignCenter)
        
        # ID input area (for card mode)
        self.id_container = QWidget()
        self.id_layout = QVBoxLayout()
        self.id_container.setLayout(self.id_layout)
        
        instruction = QLabel("Entrez votre ID employé")
        instruction.setFont(QFont("Arial", 14))
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet("color: #34495E; padding: 10px;")
        self.id_layout.addWidget(instruction)
        
        self.id_input = QLineEdit()
        self.id_input.setFont(QFont("Arial", 20))
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
        self.left_layout.addWidget(self.id_container, 0, Qt.AlignCenter)
        
        # Method switcher button (for enabled methods)
        self.method_switcher = QPushButton("⟳ Changer de méthode (TAB)")
        self.method_switcher.setFont(QFont("Arial", 14))
        self.method_switcher.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                min-width: 250px;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        self.method_switcher.clicked.connect(self.switch_to_next_method)
        self.left_layout.addWidget(self.method_switcher, 0, Qt.AlignCenter)
        
        # Add spacer
        self.left_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.main_layout.addWidget(self.left_container)
        
        self.layout.addWidget(self.main_container)

    def setup_status_area(self):
        """Setup status feedback area"""
        # Right side: Status/Response area
        self.status_container = QWidget()
        self.status_layout = QVBoxLayout()
        self.status_container.setLayout(self.status_layout)
        self.status_container.setMinimumWidth(400)
        
        # Add top spacer
        self.status_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Employee photo (larger for side display)
        self.employee_photo = QLabel()
        self.employee_photo.setAlignment(Qt.AlignCenter)
        self.employee_photo.setFixedSize(150, 150)
        self.employee_photo.setStyleSheet("""
            QLabel {
                border: 3px solid #BDC3C7;
                border-radius: 75px;
                background-color: white;
            }
        """)
        self.employee_photo.hide()
        self.status_layout.addWidget(self.employee_photo, 0, Qt.AlignCenter)
        
        # Employee name
        self.employee_name_label = QLabel()
        self.employee_name_label.setFont(QFont("Arial", 22, QFont.Bold))
        self.employee_name_label.setAlignment(Qt.AlignCenter)
        self.employee_name_label.setStyleSheet("color: #2C3E50; padding: 15px;")
        self.employee_name_label.hide()
        self.employee_name_label.setWordWrap(True)
        self.status_layout.addWidget(self.employee_name_label)
        
        # Status message
        self.status_label = QLabel()
        self.status_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(150)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                border-radius: 10px;
            }
        """)
        self.status_layout.addWidget(self.status_label)
        
        # Add bottom spacer
        self.status_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Add to main horizontal layout
        self.main_layout.addWidget(self.status_container)

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
        
        # Play start sound
        self.play_sound("start")
        
        # Update method switcher visibility based on enabled methods
        enabled_methods = self.get_enabled_methods()
        if len(enabled_methods) > 1:
            self.method_switcher.show()
        else:
            self.method_switcher.hide()
        
        if mode == 'qr':
            self.start_qr_mode()
        elif mode == 'face':
            self.start_face_mode()
        else:  # card
            self.start_card_mode()

    def get_enabled_methods(self):
        """Get list of enabled methods"""
        enabled = []
        if self.db.get_setting('qr_enabled') == '1':
            enabled.append('qr')
        if self.db.get_setting('face_enabled') == '1':
            enabled.append('face')
        if self.db.get_setting('card_enabled') == '1':
            enabled.append('card')
        return enabled

    def switch_to_next_method(self):
        """Switch to the next enabled method"""
        enabled_methods = self.get_enabled_methods()
        
        if len(enabled_methods) <= 1:
            return  # No other methods to switch to
        
        current_mode = self.db.get_setting('attendance_mode')
        
        try:
            current_index = enabled_methods.index(current_mode)
            next_index = (current_index + 1) % len(enabled_methods)
            next_mode = enabled_methods[next_index]
        except ValueError:
            # Current mode not in enabled list, start with first enabled
            next_mode = enabled_methods[0]
        
        # Stop current mode
        self.stop_current_mode()
        
        # Update setting and start new mode
        self.db.update_setting('attendance_mode', next_mode)
        self.start_attendance_mode()
        
        # Show notification
        mode_names = {'qr': 'Scan QR', 'face': 'Reconnaissance Faciale', 'card': 'Carte ID'}
        self.show_status(f"✓ Mode changé: {mode_names.get(next_mode, next_mode)}", "info", auto_clear=True)

    def stop_current_mode(self):
        """Stop camera and timers for current mode"""
        # Use the deactivate_camera method to properly clean up
        if self.camera_active:
            self.deactivate_camera()
        
        # Additional cleanup
        if self.camera:
            self.camera.release()
            self.camera = None
        if self.camera_timer.isActive():
            self.camera_timer.stop()
        
        # Hide camera-related UI elements
        self.camera_instruction_label.hide()
        self.camera_countdown_label.hide()
        
        self.clear_status()

    def initialize_camera(self):
        """Initialize camera with fallback options"""
        # Try different camera indices
        for camera_index in [0, 1, 2]:
            try:
                self.camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)  # Use DirectShow backend
                
                if self.camera.isOpened():
                    # Test if we can actually read frames
                    ret, test_frame = self.camera.read()
                    if ret and test_frame is not None:
                        print(f"Camera initialized successfully on index {camera_index}")
                        return True
                    else:
                        self.camera.release()
                        continue
                else:
                    continue
                    
            except Exception as e:
                print(f"Failed to initialize camera {camera_index}: {e}")
                continue
        
        # If all cameras failed, show error
        self.camera = None
        return False

    def start_qr_mode(self):
        """Start QR scanning mode"""
        self.mode_label.setText("🔲 MODE SCAN QR")
        self.camera_label.hide()  # Don't show camera until activated
        self.id_container.hide()
        
        # Check if we're in a working window
        if self.is_in_working_window():
            # Show instruction to activate camera
            self.camera_instruction_label.setText(
                "⌨️ Appuyez sur ESPACE ou ENTRÉE pour activer la caméra\n\n"
                "⏱️ La caméra restera active pendant 2 minutes\n"
                "📱 Chaque scan prolonge de 2 minutes"
            )
            self.camera_instruction_label.show()
            self.show_status("⌨️ Appuyez sur ESPACE ou ENTRÉE pour démarrer", "info")
        else:
            # Outside working window
            self.camera_instruction_label.setText(
                "⏰ Caméra désactivée en dehors des fenêtres horaires\n\n"
                "Plages actives:\n" +
                self.get_working_windows_text()
            )
            self.camera_instruction_label.show()
            self.show_status("⏰ Hors fenêtre horaire", "error")

    def start_face_mode(self):
        """Start face recognition mode"""
        self.mode_label.setText("👤 MODE RECONNAISSANCE FACIALE")
        self.camera_label.hide()  # Don't show camera until activated
        self.id_container.hide()
        
        # Check if we're in a working window
        if self.is_in_working_window():
            # Show instruction to activate camera
            self.camera_instruction_label.setText(
                "⌨️ Appuyez sur ESPACE ou ENTRÉE pour activer la caméra\n\n"
                "⏱️ La caméra restera active pendant 2 minutes\n"
                "👤 Chaque reconnaissance prolonge de 2 minutes"
            )
            self.camera_instruction_label.show()
            self.show_status("⌨️ Appuyez sur ESPACE ou ENTRÉE pour démarrer", "info")
        else:
            # Outside working window
            self.camera_instruction_label.setText(
                "⏰ Caméra désactivée en dehors des fenêtres horaires\n\n"
                "Plages actives:\n" +
                self.get_working_windows_text()
            )
            self.camera_instruction_label.show()
            self.show_status("⏰ Hors fenêtre horaire", "error")

    def start_card_mode(self):
        """Start ID card input mode"""
        self.mode_label.setText("🔢 MODE CARTE ID")
        self.camera_label.hide()
        self.id_container.show()
        self.id_input.setFocus()

    def process_camera_frame(self):
        """Process camera frames for QR or Face detection"""
        if not self.camera or not self.camera.isOpened():
            # Try to reinitialize camera
            if self.initialize_camera():
                self.show_status("📷 Caméra reconnectée", "info", auto_clear=True)
            else:
                # Show error message on camera label
                error_pixmap = QPixmap(640, 480)
                error_pixmap.fill(Qt.black)
                painter = QPainter(error_pixmap)
                painter.setPen(QPen(Qt.white, 2))
                painter.setFont(QFont("Arial", 16))
                painter.drawText(error_pixmap.rect(), Qt.AlignCenter, 
                               "❌ ERREUR CAMÉRA\n\nVérifiez la connexion\n\nUtilisez le mode Carte ID")
                painter.end()
                self.camera_label.setPixmap(error_pixmap)
                return
        
        try:
            ret, frame = self.camera.read()
            if not ret or frame is None:
                # Camera read failed, try to reinitialize
                self.camera.release()
                self.camera = None
                print("Camera read failed, attempting to reinitialize...")
                if self.initialize_camera():
                    self.show_status("📷 Caméra reconnectée", "info", auto_clear=True)
                return
        except Exception as e:
            print(f"Camera read error: {e}")
            # Try to reinitialize
            if self.camera:
                self.camera.release()
            self.camera = None
            if self.initialize_camera():
                self.show_status("📷 Caméra reconnectée après erreur", "info", auto_clear=True)
            return
        
        # Store current frame for photo capture
        self.current_frame = frame.copy()
        
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
            # Play scan sound
            self.play_sound("scan")
            
            # Draw detection box
            cv2.putText(frame, "QR DETECTE", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            self.display_frame(frame)
            
            # Process attendance
            self.last_scan_time = datetime.datetime.now()
            self.process_qr_attendance(qr_data, frame)
        else:
            # Draw instruction
            cv2.putText(frame, "Presentez votre code QR", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            self.display_frame(frame)

    def process_face_frame(self, frame):
        """Detect and process faces using MTCNN and FaceNet"""
        if self.face_recognizer is None:
            return
        # Detect and extract face from the current frame
        result = self.face_recognizer.detect_and_extract_face(frame)
        
        if result[0] is not None:
            captured_embedding, face_info = result
            bbox = face_info['bbox']
            x1, y1, x2, y2 = [int(v) for v in bbox]
            
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
            
            # Draw face box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Process the result
            if best_match and self.face_recognizer.is_match_accepted(best_confidence):
                status = f"{best_match.name} - {best_confidence:.1f}%"
                color = (0, 255, 0)  # Green
                cv2.putText(frame, status, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Check cooldown before processing attendance
                current_time = datetime.datetime.now()
                if self.last_scan_time is None or (current_time - self.last_scan_time).seconds >= 3:
                    self.last_scan_time = current_time
                    self.handle_successful_face_recognition(best_match, best_confidence, frame.copy())
            else:
                # Show frame with status
                if best_match:
                    status = f"Confiance insuffisante: {best_confidence:.1f}%"
                    color = (0, 165, 255)  # Orange
                else:
                    status = "Non reconnu"
                    color = (0, 0, 255)  # Red
                
                cv2.putText(frame, status, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
            # No face detected or low confidence
            cv2.putText(frame, "Positionnez votre visage face à la caméra", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
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

    def process_qr_attendance(self, qr_data, frame=None):
        """Process QR code attendance"""
        employee = self.db.get_employee_by_qr(qr_data)
        
        if not employee:
            self.play_sound("error")
            self.show_status("❌ Code QR non reconnu", "error", auto_clear=True)
            return
        
        if not employee.enabled:
            self.play_sound("error")
            self.show_status(f"❌ {employee.name}\nCompte désactivé", "error", auto_clear=True)
            return
        
        # Check window and record
        self.record_attendance(employee, frame=frame)
        
        # Extend camera session on successful scan
        if self.camera_active:
            self.extend_camera_session()

    def handle_successful_face_recognition(self, employee, confidence, frame):
        """Handle successful face recognition"""
        # Play scan sound
        self.play_sound("scan")
        
        # Draw success indicators on frame
        # Note: Since we don't have face coordinates from the embedding approach,
        # we'll just show the result without drawing rectangles
        cv2.putText(frame, f"Reconnu: {employee.name}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Confiance: {confidence:.1f}%", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        self.display_frame(frame)
        
        # Process attendance
        self.last_scan_time = datetime.datetime.now()
        self.process_face_attendance(employee.employee_id, confidence, frame)

    def process_face_attendance(self, employee_id, confidence, frame=None):
        """Process face recognition attendance"""
        employee = self.db.get_employee(employee_id)
        
        if not employee:
            self.play_sound("error")
            self.show_status("❌ Employé non trouvé", "error", auto_clear=True)
            return
        
        if not employee.enabled:
            self.play_sound("error")
            self.show_status(f"❌ {employee.name}\nCompte désactivé", "error", auto_clear=True)
            return
        
        # Check window and record
        self.record_attendance(employee, extra_info=f"Confiance: {confidence:.0f}%", frame=frame, confidence=confidence)
        
        # Extend camera session on successful recognition
        if self.camera_active:
            self.extend_camera_session()

    def process_id_input(self):
        """Process ID card input"""
        employee_id = self.id_input.text().strip()
        self.id_input.clear()
        
        if not employee_id:
            return
        
        employee = self.db.get_employee(employee_id)
        
        if not employee:
            self.play_sound("error")
            self.show_status("❌ ID employé non trouvé", "error", auto_clear=True)
            return
        
        if not employee.enabled:
            self.play_sound("error")
            self.show_status(f"❌ {employee.name}\nCompte désactivé", "error", auto_clear=True)
            return
        
        # Check window and record (use current frame from camera)
        self.record_attendance(employee, frame=self.current_frame)

    def save_checkpoint_photo(self, employee_id, action, frame):
        """Save a photo of the checkpoint"""
        if frame is None:
            return None
        
        try:
            # Create employee directory
            employee_dir = os.path.join(self.photos_dir, str(employee_id))
            os.makedirs(employee_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            action_name = "arrival" if action == "IN" else "departure"
            filename = f"{timestamp}_{action_name}.jpg"
            filepath = os.path.join(employee_dir, filename)
            
            # Save the photo
            cv2.imwrite(filepath, frame)
            print(f"Checkpoint photo saved: {filepath}")
            return filepath
        
        except Exception as e:
            print(f"Error saving checkpoint photo: {e}")
            return None
    
    def record_attendance(self, employee, extra_info="", frame=None, confidence=None):
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
            self.play_sound("error")
            self.show_status("❌ Hors fenêtre horaire", "error", auto_clear=True)
            return

        # Check for duplicate
        is_duplicate, dup_message = self.check_duplicate_attendance(employee.employee_id, action)
        if is_duplicate:
            self.play_sound("error")
            self.show_status(f"❌ {employee.name}\n{dup_message}", "error", auto_clear=True)
            return

        # Play success sound based on action
        if action == "IN":
            self.play_sound("in")
        elif action == "OUT":
            self.play_sound("out")

        # Save checkpoint photo
        photo_path = self.save_checkpoint_photo(employee.employee_id, action, frame)
        
        # Record attendance with full audit trail
        mode = self.db.get_setting('attendance_mode')
        record_id = self.db.record_attendance(
            employee.employee_id, 
            action, 
            mode.upper(), 
            "TERMINAL-01",
            photo_path=photo_path,
            confidence=confidence
        )
        
        # Show success
        success_msg = f"✓ {window_name}\n{now.strftime('%H:%M:%S')}"
        if extra_info:
            success_msg += f"\n{extra_info}"
        if photo_path:
            success_msg += "\n📷 Photo enregistrée"
        
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
        """Show employee info (no photo display per compliance specs)"""
        # Hide photo display since raw face images are not stored per compliance
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
        
        # SECURITY: Force-close camera if we're outside working window
        if self.camera_active and not self.is_in_working_window():
            print("⚠️ Working window ended - Force closing camera for security")
            self.deactivate_camera()
            self.show_status("⏰ Fenêtre horaire terminée - Caméra désactivée", "error", auto_clear=True)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_F11:
            self.f11_press_count += 1
            if self.f11_press_count == 1:
                self.f11_reset_timer.start(2000)
            elif self.f11_press_count >= 5:
                # Show password dialog before opening admin
                self.open_admin_with_password()
                self.f11_press_count = 0
                self.f11_reset_timer.stop()
        elif event.key() == Qt.Key_Tab:
            # Switch to next enabled method
            self.switch_to_next_method()
            event.accept()
        elif event.key() == Qt.Key_Space or event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Activate camera if in QR or Face mode and within working window
            mode = self.db.get_setting('attendance_mode')
            if mode in ['qr', 'face'] and not self.camera_active:
                if self.is_in_working_window():
                    self.activate_camera()
                else:
                    self.show_status("⏰ Hors fenêtre horaire - Caméra désactivée", "error", auto_clear=True)
            event.accept()
        elif event.key() == Qt.Key_Escape:
            pass  # Ignore escape
    
    def open_admin_with_password(self):
        """Open admin interface with password protection"""
        # Get stored admin password (default: admin)
        stored_password = self.db.get_setting('admin_password')
        if not stored_password:
            # Set default password
            stored_password = hashlib.sha256('admin'.encode()).hexdigest()
            self.db.update_setting('admin_password', stored_password)
        
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            password, ok = QInputDialog.getText(
                self,
                "Accès Administrateur",
                f"Entrez le mot de passe administrateur:\n(Tentative {attempts + 1}/{max_attempts})",
                QLineEdit.Password
            )
            
            if not ok:
                # User cancelled
                return
            
            # Hash the entered password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            if hashed_password == stored_password:
                # Correct password - open admin interface
                from gui.admin_interface import AdminInterface
                self.admin_window = AdminInterface(self.db, self)
                self.admin_window.show()
                self.hide()
                return
            else:
                attempts += 1
                if attempts < max_attempts:
                    QMessageBox.warning(
                        self,
                        "Erreur",
                        f"❌ Mot de passe incorrect!\n\nTentatives restantes: {max_attempts - attempts}"
                    )
        
        # 3 failed attempts - take photo and deny access
        QMessageBox.critical(
            self,
            "Accès refusé",
            "⚠️ Accès refusé!\n\n📸 Une photo a été prise pour des raisons de sécurité."
        )
        self.capture_intruder_photo()

    def reset_f11_count(self):
        """Reset F11 press counter"""
        self.f11_press_count = 0
        self.f11_reset_timer.stop()
    
    def capture_intruder_photo(self):
        """Capture photo of person attempting unauthorized admin access"""
        temp_camera = None
        camera_was_active = self.camera_active
        
        try:
            # Use existing camera if active, otherwise temporarily activate
            if self.camera is not None and self.camera.isOpened():
                temp_camera = self.camera
            else:
                # Temporarily activate camera for security photo
                print("📸 Temporarily activating camera for security photo")
                for camera_index in [0, 1, 2]:
                    try:
                        temp_camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                        if temp_camera.isOpened():
                            ret, test_frame = temp_camera.read()
                            if ret and test_frame is not None:
                                break
                            else:
                                temp_camera.release()
                                temp_camera = None
                    except Exception as e:
                        print(f"Camera {camera_index} failed: {e}")
                        continue
            
            if temp_camera is None or not temp_camera.isOpened():
                print("⚠️ Camera not available for intruder photo")
                return
            
            # Capture frame from camera
            ret, frame = temp_camera.read()
            if not ret or frame is None:
                print("⚠️ Failed to capture intruder photo")
                return
            
            # Create security photos directory
            security_dir = Path("data/security_photos")
            security_dir.mkdir(parents=True, exist_ok=True)
            
            # Save photo with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            photo_path = security_dir / f"intruder_{timestamp}.jpg"
            
            cv2.imwrite(str(photo_path), frame)
            print(f"📸 Intruder photo saved: {photo_path}")
            
            # Log the security event
            log_path = security_dir / "security_log.txt"
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Failed admin access attempt - Photo: {photo_path.name}\n")
            
        except Exception as e:
            print(f"⚠️ Error capturing intruder photo: {e}")
        finally:
            # Clean up temporary camera if we created one
            if not camera_was_active and temp_camera is not None and temp_camera != self.camera:
                temp_camera.release()
                print("📸 Temporary camera released")

    def is_in_working_window(self):
        """Check if current time is within working windows"""
        now = datetime.datetime.now()
        current_time = now.time()
        
        morning_start = datetime.datetime.strptime(self.db.get_setting('morning_start'), '%H:%M').time()
        morning_end = datetime.datetime.strptime(self.db.get_setting('morning_end'), '%H:%M').time()
        afternoon_start = datetime.datetime.strptime(self.db.get_setting('afternoon_start'), '%H:%M').time()
        afternoon_end = datetime.datetime.strptime(self.db.get_setting('afternoon_end'), '%H:%M').time()
        
        in_morning = morning_start <= current_time <= morning_end
        in_afternoon = afternoon_start <= current_time <= afternoon_end
        
        return in_morning or in_afternoon
    
    def get_working_windows_text(self):
        """Get formatted text of working windows"""
        morning_start = self.db.get_setting('morning_start')
        morning_end = self.db.get_setting('morning_end')
        afternoon_start = self.db.get_setting('afternoon_start')
        afternoon_end = self.db.get_setting('afternoon_end')
        
        return f"Matin: {morning_start} - {morning_end}\nAprès-midi: {afternoon_start} - {afternoon_end}"
    
    def activate_camera(self):
        """Activate camera and start session timer"""
        # Check if already active
        if self.camera_active:
            return
        
        # Initialize camera
        if self.initialize_camera():
            self.camera_active = True
            self.camera_label.show()
            self.camera_instruction_label.hide()
            
            # Start camera frame processing
            self.camera_timer.start(30)  # ~33 FPS
            
            # Start session timer (2 minutes)
            self.camera_session_remaining = self.camera_session_duration
            self.camera_session_timer.start(self.camera_session_duration * 1000)  # milliseconds
            
            # Start countdown display timer
            self.countdown_timer.start()
            self.update_camera_countdown()
            self.camera_countdown_label.show()
            
            mode = self.db.get_setting('attendance_mode')
            msg = "📷 Caméra activée - Présentez votre QR code" if mode == 'qr' else "📷 Caméra activée - Regardez la caméra"
            self.show_status(msg, "info", auto_clear=True)
        else:
            self.show_status("❌ Erreur caméra - Vérifiez la connexion\n\nUtilisez le mode Carte ID", "error")
    
    def deactivate_camera(self):
        """Deactivate camera and stop timers"""
        if not self.camera_active:
            return
        
        # Stop camera
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Stop timers
        if self.camera_timer.isActive():
            self.camera_timer.stop()
        if self.camera_session_timer.isActive():
            self.camera_session_timer.stop()
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()
        
        # Update UI
        self.camera_active = False
        self.camera_label.hide()
        self.camera_countdown_label.hide()
        
        # Show reactivation instructions if still in working window
        if self.is_in_working_window():
            mode = self.db.get_setting('attendance_mode')
            if mode in ['qr', 'face']:
                self.camera_instruction_label.setText(
                    "⏱️ Session caméra expirée\n\n"
                    "⌨️ Appuyez sur ESPACE ou ENTRÉE pour réactiver"
                )
                self.camera_instruction_label.show()
                self.show_status("⏱️ Caméra désactivée - Appuyez sur ESPACE pour réactiver", "info")
    
    def extend_camera_session(self):
        """Extend camera session by 2 minutes after successful scan"""
        if not self.camera_active:
            return
        
        # Reset session timer
        self.camera_session_remaining = self.camera_session_duration
        self.camera_session_timer.stop()
        self.camera_session_timer.start(self.camera_session_duration * 1000)
        
        # Update countdown display
        self.update_camera_countdown()
        
        print("📷 Session caméra prolongée de 2 minutes")
    
    def on_camera_session_timeout(self):
        """Handle camera session timeout"""
        print("⏱️ Session caméra expirée")
        self.deactivate_camera()
    
    def update_camera_countdown(self):
        """Update camera countdown display"""
        if not self.camera_active:
            return
        
        # SECURITY CHECK: Verify we're still in working window
        if not self.is_in_working_window():
            print("⚠️ Working window ended during countdown - Force closing camera")
            self.deactivate_camera()
            self.show_status("⏰ Fenêtre horaire terminée - Caméra désactivée", "error", auto_clear=True)
            return
        
        # Decrease remaining time
        if self.camera_session_remaining > 0:
            self.camera_session_remaining -= 1
        
        # Format time as MM:SS
        minutes = self.camera_session_remaining // 60
        seconds = self.camera_session_remaining % 60
        
        # Update label with color based on remaining time
        if self.camera_session_remaining > 60:
            color = "#27AE60"  # Green
            icon = "✓"
        elif self.camera_session_remaining > 30:
            color = "#E67E22"  # Orange
            icon = "⚠"
        else:
            color = "#E74C3C"  # Red
            icon = "⏰"
        
        self.camera_countdown_label.setText(f"{icon} Session: {minutes:02d}:{seconds:02d}")
        self.camera_countdown_label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 5px;")

    def closeEvent(self, event):
        """Cleanup on close"""
        if self.camera:
            self.camera.release()
        event.accept()
