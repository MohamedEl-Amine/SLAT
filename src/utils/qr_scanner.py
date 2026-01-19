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
        # Initialize camera with robust fallback
        cap = None
        for camera_index in [0, 1, 2]:
            try:
                cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                
                if cap.isOpened():
                    # Test if we can actually read frames
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        print(f"Camera initialized successfully on index {camera_index} for QR scanning")
                        break
                    else:
                        cap.release()
                        cap = None
                        continue
                else:
                    continue
                    
            except Exception as e:
                print(f"Failed to initialize camera {camera_index} for QR scanning: {e}")
                continue
        
        if cap is None or not cap.isOpened():
            return None

        start_time = time.time()
        timeout = 30  # 30 seconds timeout
        consecutive_failures = 0

        try:
            while time.time() - start_time < timeout:
                ret, frame = cap.read()
                if not ret or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures > 10:
                        break
                    continue
                
                consecutive_failures = 0

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
        """Test if camera is available with robust initialization."""
        # Try different camera indices
        for camera_index in [0, 1, 2]:
            try:
                cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                
                if cap.isOpened():
                    # Test if we can actually read frames
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        cap.release()
                        return True
                    else:
                        cap.release()
                        continue
                else:
                    continue
                    
            except Exception as e:
                print(f"Failed to test camera {camera_index}: {e}")
                continue
        
        return False