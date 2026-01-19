"""
Face recognition utilities for SLAT.
"""

import cv2
import numpy as np
from typing import Optional, Tuple

class FaceRecognition:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.acceptance_threshold = 75.0  # Minimum confidence percentage for recognition
        self.face_size = (150, 150)  # Increased size for better accuracy

    def test_camera(self) -> bool:
        """Test if camera is available."""
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            return True
        return False

    def capture_face_for_enrollment(self) -> Optional[Tuple[np.ndarray, str]]:
        """Capture a face for enrollment with quality validation.
        Returns: (face_data, status_message) or (None, error_message)
        """
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None, "Aucune caméra détectée"

        captured_face = None
        message = "Positionnez votre visage face à la caméra"
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(100, 100)
            )

            # Validate detection
            if len(faces) == 0:
                message = "Aucun visage détecté"
                cv2.putText(frame, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif len(faces) > 1:
                message = "Plusieurs visages détectés - Une seule personne SVP"
                cv2.putText(frame, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                # Draw rectangles around all faces
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            elif len(faces) == 1:
                x, y, w, h = faces[0]
                
                # Validate face quality
                face_roi_gray = gray[y:y+h, x:x+w]
                face_roi_color = frame[y:y+h, x:x+w]
                
                # Check if face is frontal by detecting eyes
                eyes = self.eye_cascade.detectMultiScale(face_roi_gray, scaleFactor=1.1, minNeighbors=3)
                
                if len(eyes) < 2:
                    message = "Visage de face requis - Regardez la caméra"
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 165, 255), 2)
                    cv2.putText(frame, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                else:
                    # Good quality face detected
                    message = "Visage détecté - Appuyez sur ESPACE pour capturer"
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Draw eye indicators
                    for (ex, ey, ew, eh) in eyes[:2]:
                        cv2.circle(frame, (x+ex+ew//2, y+ey+eh//2), 5, (0, 255, 0), 2)

            cv2.imshow('Enregistrement facial - Q pour annuler', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' ') and len(faces) == 1:
                # Capture the face
                x, y, w, h = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                
                # Check quality again before capture
                eyes = self.eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=3)
                if len(eyes) >= 2:
                    # Resize to standard size and normalize
                    face_resized = cv2.resize(face_roi, self.face_size)
                    # Apply histogram equalization for better recognition
                    face_normalized = cv2.equalizeHist(face_resized)
                    captured_face = face_normalized
                    message = "Visage capturé avec succès"
                    break
                else:
                    message = "Qualité insuffisante - Veuillez regarder la caméra"
            elif key == ord('q') or key == 27:  # q or ESC
                message = "Capture annulée"
                break

        cap.release()
        cv2.destroyAllWindows()
        
        if captured_face is not None:
            return captured_face, "Succès"
        else:
            return None, message

    def capture_face_for_recognition(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Capture a face for recognition in real-time.
        Returns: (face_data, raw_frame) or (None, None)
        """
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None, None

        captured_face = None
        raw_frame = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

            if len(faces) == 1:
                x, y, w, h = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                face_resized = cv2.resize(face_roi, self.face_size)
                face_normalized = cv2.equalizeHist(face_resized)
                captured_face = face_normalized
                raw_frame = frame.copy()
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "Identification en cours...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            elif len(faces) > 1:
                cv2.putText(frame, "Plusieurs visages - Une seule personne SVP", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "Positionnez votre visage face a la camera", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

            cv2.imshow('Reconnaissance faciale - Q pour annuler', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' ') and captured_face is not None:
                break
            elif key == ord('q') or key == 27:
                break

        cap.release()
        cv2.destroyAllWindows()
        
        return captured_face, raw_frame

    def match_face(self, stored_face_bytes: bytes, captured_face: np.ndarray) -> float:
        """Compare stored face with captured face and return confidence percentage.
        Returns: Confidence percentage (0-100)
        """
        try:
            # Reconstruct stored face
            stored_face = np.frombuffer(stored_face_bytes, dtype=np.uint8).reshape(self.face_size)
            
            # Ensure both faces are normalized
            stored_normalized = cv2.equalizeHist(stored_face)
            captured_normalized = cv2.equalizeHist(captured_face)
            
            # Method 1: Correlation coefficient
            correlation = np.corrcoef(stored_normalized.ravel(), captured_normalized.ravel())[0, 1]
            
            # Method 2: Template matching
            result = cv2.matchTemplate(stored_normalized, captured_normalized, cv2.TM_CCOEFF_NORMED)
            template_score = result[0][0]
            
            # Method 3: Mean Squared Error (inverse similarity)
            mse = np.mean((stored_normalized.astype(float) - captured_normalized.astype(float)) ** 2)
            mse_similarity = 1.0 / (1.0 + mse / 1000.0)  # Normalize MSE
            
            # Combined confidence score (weighted average)
            confidence = (
                correlation * 0.4 +
                template_score * 0.4 +
                mse_similarity * 0.2
            ) * 100.0
            
            # Ensure confidence is between 0 and 100
            confidence = max(0.0, min(100.0, confidence))
            
            return confidence
            
        except Exception as e:
            print(f"Error in face matching: {e}")
            return 0.0

    def is_match_accepted(self, confidence: float) -> bool:
        """Determine if the confidence level meets the acceptance threshold."""
        return confidence >= self.acceptance_threshold

    def get_acceptance_threshold(self) -> float:
        """Get the current acceptance threshold."""
        return self.acceptance_threshold