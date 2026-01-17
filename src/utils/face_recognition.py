"""
Face recognition utilities for SLAT.
"""

import cv2
import numpy as np
from typing import Optional

class FaceRecognition:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def capture_face(self) -> Optional[np.ndarray]:
        """Capture a single face template from camera."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 1:
                x, y, w, h = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                face_resized = cv2.resize(face_roi, (100, 100))
                cap.release()
                cv2.destroyAllWindows()
                return face_resized

            cv2.imshow('Capture Face - Press SPACE when ready', frame)
            if cv2.waitKey(1) & 0xFF == ord(' '):
                break

        cap.release()
        cv2.destroyAllWindows()
        return None

    def recognize_face(self, stored_face: bytes, captured_face: np.ndarray) -> bool:
        """Compare stored face with captured face."""
        stored = np.frombuffer(stored_face, dtype=np.uint8).reshape(100, 100)
        similarity = np.corrcoef(stored.ravel(), captured_face.ravel())[0, 1]
        return similarity > 0.8  # Threshold