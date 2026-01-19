"""
QR code scanning utilities for SLAT.
"""

import cv2
from pyzbar.pyzbar import decode
from typing import Optional
import time

class QRScanner:
    def __init__(self):
        self.camera_index = 0

    def scan_frame(self, frame) -> Optional[str]:
        """
        Scan a single frame for QR codes.
        Returns decoded QR data or None if no QR found.
        """
        decoded_objects = decode(frame)
        
        for obj in decoded_objects:
            if obj.type == 'QRCODE':
                return obj.data.decode('utf-8')
        
        return None

    def scan_qr_code(self) -> Optional[str]:
        """
        Scan QR code from camera and return the decoded data.
        Returns None if no QR code found or camera error.
        """
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            return None

        start_time = time.time()
        timeout = 30  # 30 seconds timeout

        try:
            while time.time() - start_time < timeout:
                ret, frame = cap.read()
                if not ret:
                    continue

                # Decode QR codes in the frame
                decoded_objects = decode(frame)

                for obj in decoded_objects:
                    # Check if it's a QR code
                    if obj.type == 'QRCODE':
                        qr_data = obj.data.decode('utf-8')
                        cap.release()
                        cv2.destroyAllWindows()
                        return qr_data

                # Show the frame with instructions
                cv2.putText(frame, "Position QR code in frame", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, "Press 'q' to cancel", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                cv2.imshow('QR Code Scanner', frame)

                # Check for quit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()

        return None

    def test_camera(self) -> bool:
        """Test if camera is available."""
        cap = cv2.VideoCapture(self.camera_index)
        if cap.isOpened():
            cap.release()
            return True
        return False