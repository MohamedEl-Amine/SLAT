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

    def capture_face_for_enrollment(self) -> Optional[Tuple[np.ndarray, str]]:
        """Fast and reliable face enrollment with automatic capture.
        Returns: (face_data, status_message) or (None, error_message)
        """
        # Initialize camera
        cap = None
        for camera_index in [0, 1, 2]:
            try:
                cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        break
                cap.release()
                cap = None
            except:
                continue
        
        if cap is None:
            return None, "Aucune caméra détectée"

        # Optimize settings
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        best_face = None
        best_quality = 0
        countdown = 0
        frame_skip = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_skip += 1
            
            # Process every 2nd frame for performance
            if frame_skip % 2 != 0:
                cv2.imshow('Enregistrement - Q pour quitter', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Simple, fast detection
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,      # Faster, less sensitive
                minNeighbors=7,        # Stricter to avoid false positives
                minSize=(100, 100),
                maxSize=(400, 400)     # Limit max size
            )
            
            status = ""
            color = (255, 255, 255)
            
            if len(faces) == 0:
                status = "Aucun visage - Approchez-vous"
                color = (0, 0, 255)
                countdown = 0
                
            elif len(faces) > 1:
                status = "Trop de visages detectes"
                color = (0, 0, 255)
                countdown = 0
                # Draw all detected faces
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    
            else:
                x, y, w, h = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                
                # Simple quality check - sharpness only
                laplacian = cv2.Laplacian(face_roi, cv2.CV_64F).var()
                
                if laplacian > 80:
                    quality = min(100, int(laplacian / 2))
                    color = (0, 255, 0)
                    status = f"BON - Maintien position ({countdown}/20)"
                    countdown += 1
                    
                    # Update best
                    if quality > best_quality:
                        best_quality = quality
                        best_face = cv2.resize(face_roi, self.face_size)
                        best_face = cv2.equalizeHist(best_face)
                    
                    # Auto-capture after 20 frames (~0.7s)
                    if countdown >= 20:
                        status = "CAPTURE REUSSIE!"
                        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                        cv2.putText(frame, status, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                        cv2.imshow('Enregistrement - Q pour quitter', frame)
                        cv2.waitKey(1000)
                        break
                else:
                    color = (0, 165, 255)
                    status = "Restez immobile"
                    countdown = max(0, countdown - 1)
                
                # Draw face box
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                
                # Progress bar
                if countdown > 0:
                    bar_w = int((countdown / 20) * 400)
                    cv2.rectangle(frame, (120, 60), (520, 80), (50, 50, 50), -1)
                    cv2.rectangle(frame, (120, 60), (120 + bar_w, 80), color, -1)
            
            # Display status
            cv2.putText(frame, status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            cv2.imshow('Enregistrement - Q pour quitter', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' ') and best_face is not None:
                break

        cap.release()
        cv2.destroyAllWindows()
        
        if best_face is not None:
            return best_face, "Succès"
        else:
            return None, "Échec de capture"

    def capture_face_for_recognition(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Capture a face for recognition in real-time.
        Returns: (face_data, raw_frame) or (None, None)
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
                        print(f"Camera initialized successfully on index {camera_index} for recognition")
                        break
                    else:
                        cap.release()
                        cap = None
                        continue
                else:
                    continue
                    
            except Exception as e:
                print(f"Failed to initialize camera {camera_index} for recognition: {e}")
                continue
        
        if cap is None or not cap.isOpened():
            return None, None

        captured_face = None
        raw_frame = None
        consecutive_failures = 0
        
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                consecutive_failures += 1
                if consecutive_failures > 5:
                    cap.release()
                    return None, None
                continue
            
            consecutive_failures = 0

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