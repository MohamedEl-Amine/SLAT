"""
Data models for SLAT.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Employee:
    id: Optional[int]
    employee_id: str
    name: str
    enabled: bool
    id_method: str  # 'card', 'qr', 'face'
    pin_hash: Optional[str]
    qr_code: Optional[str]
    face_embedding: Optional[bytes]  # Biometric embedding vector (not raw image)
    created_at: Optional[datetime]

@dataclass
class AttendanceRecord:
    id: Optional[int]
    employee_id: str
    action: str  # 'IN' or 'OUT'
    timestamp: datetime
    method_used: str
    device_id: Optional[str]
    photo: Optional[bytes]
    integrity_hash: Optional[str]

@dataclass
class Settings:
    morning_start: str
    morning_end: str
    afternoon_start: str
    afternoon_end: str
    admin_password: str
    face_enabled: bool
    qr_enabled: bool
    pin_required: bool