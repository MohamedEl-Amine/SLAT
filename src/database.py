"""
Database module for SLAT using SQLite.
Handles all database operations.
"""

import sqlite3
import os
from datetime import datetime
from cryptography.fernet import Fernet
import hashlib
from models import Employee, AttendanceRecord

class Employee:
    def __init__(self, id, employee_id, name, enabled, qr_code, face_image, created_at):
        self.id = id
        self.employee_id = employee_id
        self.name = name
        self.enabled = enabled
        self.qr_code = qr_code
        self.face_image = face_image
        self.created_at = created_at

class Database:
    def __init__(self, db_path="data/slat.db"):
        self.db_path = db_path
        self.key_path = "data/key.key"
        self._ensure_data_dir()
        self.cipher = self._load_or_create_key()
        self._create_tables()

    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _load_or_create_key(self):
        if os.path.exists(self.key_path):
            with open(self.key_path, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(key)
        return Fernet(key)

    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Employees table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY,
                    employee_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    qr_code TEXT,
                    face_image BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Attendance logs table (append-only)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance_logs (
                    id INTEGER PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    action TEXT NOT NULL,  -- 'IN' or 'OUT'
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    method_used TEXT NOT NULL,
                    device_id TEXT,
                    photo BLOB,
                    integrity_hash TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
                )
            ''')

            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            # Insert default settings
            default_settings = [
                ('morning_start', '08:30'),
                ('morning_end', '09:00'),
                ('afternoon_start', '16:00'),
                ('afternoon_end', '16:30'),
                ('admin_password', hashlib.sha256('admin'.encode()).hexdigest()),
                ('card_enabled', '1'),
                ('qr_enabled', '0'),
                ('face_enabled', '0'),
                ('attendance_mode', 'qr')  # qr, face, or card
            ]

            for key, value in default_settings:
                cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))

            conn.commit()

    def get_setting(self, key):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else None

    def update_setting(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
            conn.commit()

    def get_employee(self, employee_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM employees WHERE employee_id = ?', (employee_id,))
            row = cursor.fetchone()
            if row:
                created_at = datetime.fromisoformat(row[6]) if row[6] else None
                return Employee(id=row[0], employee_id=row[1], name=row[2], enabled=bool(row[3]), qr_code=row[4], face_image=row[5], created_at=created_at)
            return None
    
    def get_employee_by_qr(self, qr_code):
        """Get employee by QR code"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM employees WHERE qr_code = ?', (qr_code,))
            row = cursor.fetchone()
            if row:
                created_at = datetime.fromisoformat(row[6]) if row[6] else None
                return Employee(id=row[0], employee_id=row[1], name=row[2], enabled=bool(row[3]), qr_code=row[4], face_image=row[5], created_at=created_at)
            return None

    def record_attendance(self, employee_id, action, method_used, device_id, photo=None):
        timestamp = datetime.now()
        hash_input = f"{employee_id}{action}{timestamp}{method_used}".encode()
        integrity_hash = hashlib.sha256(hash_input).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO attendance_logs (employee_id, action, timestamp, method_used, device_id, photo, integrity_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (employee_id, action, timestamp, method_used, device_id, photo, integrity_hash))
            conn.commit()

    def add_employee(self, employee_id, name, qr_code=None, face_image=None):
        """Add a new employee to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO employees (employee_id, name, enabled, qr_code, face_image)
                    VALUES (?, ?, 1, ?, ?)
                ''', (employee_id, name, qr_code, face_image))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def update_employee_qr(self, employee_id, qr_code):
        """Update employee QR code"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE employees SET qr_code = ? WHERE employee_id = ?', (qr_code, employee_id))
            conn.commit()
    
    def update_employee_face(self, employee_id, face_image):
        """Update employee face image"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE employees SET face_image = ? WHERE employee_id = ?', (face_image, employee_id))
            conn.commit()
    
    def generate_qr_code(self, employee_id):
        """Generate QR code for employee"""
        import qrcode
        from io import BytesIO
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(employee_id)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_bytes = buffer.getvalue()
        
        # Update employee with QR code data
        self.update_employee_qr(employee_id, employee_id)  # Store employee_id as qr_code
        
        return qr_bytes

    def get_all_employees(self):
        """Get all employees"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM employees ORDER BY name')
            rows = cursor.fetchall()
            employees = []
            for row in rows:
                created_at = datetime.fromisoformat(row[6]) if row[6] else None
                employees.append(Employee(
                    id=row[0], 
                    employee_id=row[1], 
                    name=row[2], 
                    enabled=bool(row[3]), 
                    qr_code=row[4], 
                    face_image=row[5], 
                    created_at=created_at
                ))
            return employees

    def update_employee_status(self, employee_id, enabled):
        """Enable or disable an employee"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE employees SET enabled = ? WHERE employee_id = ?', (int(enabled), employee_id))
            conn.commit()

    def update_employee_name(self, employee_id, new_name):
        """Update employee name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE employees SET name = ? WHERE employee_id = ?', (new_name, employee_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_logs(self, limit=None):
        """Get all attendance logs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM attendance_logs ORDER BY timestamp DESC'
            if limit:
                query += f' LIMIT {limit}'
            cursor.execute(query)
            return cursor.fetchall()

    def get_employee_logs(self, employee_id, limit=None):
        """Get attendance logs for specific employee"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM attendance_logs WHERE employee_id = ? ORDER BY timestamp DESC'
            if limit:
                query += f' LIMIT {limit}'
            cursor.execute(query, (employee_id,))
            rows = cursor.fetchall()
            
            # Convert to AttendanceRecord objects
            records = []
            for row in rows:
                records.append(AttendanceRecord(
                    id=row[0],
                    employee_id=row[1],
                    action=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    method_used=row[4],
                    device_id=row[5],
                    photo=row[6],
                    integrity_hash=row[7]
                ))
            return records

    def hash_password(self, password):
        """Hash a password"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password, hashed):
        """Verify a password against a hash"""
        return hashlib.sha256(password.encode()).hexdigest() == hashed