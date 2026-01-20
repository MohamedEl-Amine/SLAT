"""
Face recognition utilities for SLAT.
Compliant with Mandatory Face Recognition Architecture specifications.
Uses InsightFace's built-in RetinaFace detector and ArcFace recognition.
"""

import cv2
import numpy as np
import insightface
from typing import Optional, Tuple, List
import os

class FaceRecognition:
    def __init__(self):
        # Initialize InsightFace model with RetinaFace detector and ArcFace recognition
        self.face_model = insightface.app.FaceAnalysis(name='buffalo_l')
        self.face_model.prepare(ctx_id=-1, det_size=(640, 640))  # ctx_id=-1 for CPU

        # Similarity threshold for ArcFace (calibrated for biometric matching)
        # Lower values are more strict, higher values are more lenient
        self.similarity_threshold = 0.4  # Cosine similarity threshold

        # Face detection confidence threshold
        self.detection_threshold = 0.8

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
        """Capture face for enrollment and return embedding vector.
        Returns: (embedding_vector, status_message) or (None, error_message)
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

        best_embedding = None
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

            # Detect faces using InsightFace (RetinaFace + ArcFace)
            faces = self.face_model.get(frame)

            status = ""
            color = (255, 255, 255)

            if len(faces) == 0:
                status = "Aucun visage - Approchez-vous"
                color = (0, 0, 255)
                countdown = 0

            elif len(faces) > 1:
                status = "Trop de visages détectés"
                color = (0, 0, 255)
                countdown = 0
                # Draw all detected faces
                for face in faces:
                    x1, y1, x2, y2 = face.bbox.astype(int)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            else:
                face = faces[0]
                bbox = face.bbox.astype(int)
                confidence = face.det_score

                if confidence >= self.detection_threshold:
                    color = (0, 255, 0)
                    status = f"BON - Maintien position ({countdown}/20)"
                    countdown += 1

                    # Update best embedding
                    if confidence > best_quality:
                        best_quality = confidence
                        best_embedding = face.embedding

                    # Auto-capture after 20 frames (~0.7s)
                    if countdown >= 20:
                        status = "CAPTURE RÉUSSIE!"
                        x1, y1, x2, y2 = bbox
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                        cv2.putText(frame, status, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                        cv2.imshow('Enregistrement - Q pour quitter', frame)
                        cv2.waitKey(1000)
                        break
                else:
                    color = (0, 165, 255)
                    status = "Restez immobile"
                    countdown = max(0, countdown - 1)

                # Draw face box
                x1, y1, x2, y2 = bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

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
            elif key == ord(' ') and best_embedding is not None:
                break

        cap.release()
        cv2.destroyAllWindows()

        if best_embedding is not None:
            return best_embedding, "Succès"
        else:
            return None, "Échec de capture"

    def capture_face_for_recognition(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Capture a face for recognition and return embedding vector and raw frame.
        Returns: (embedding_vector, raw_frame) or (None, None)
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

        captured_embedding = None
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

            # Detect faces using InsightFace (RetinaFace + ArcFace)
            faces = self.face_model.get(frame)

            if len(faces) == 1:
                face = faces[0]
                bbox = face.bbox.astype(int)
                confidence = face.det_score

                if confidence >= self.detection_threshold:
                    captured_embedding = face.embedding
                    raw_frame = frame.copy()

                    x1, y1, x2, y2 = bbox
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, "Identification en cours...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "Visage détecté mais faible confiance", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

            elif len(faces) > 1:
                cv2.putText(frame, "Plusieurs visages - Une seule personne SVP", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "Positionnez votre visage face à la caméra", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

            cv2.imshow('Reconnaissance faciale - Q pour annuler', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord(' ') and captured_embedding is not None:
                break
            elif key == ord('q') or key == 27:
                break

        cap.release()
        cv2.destroyAllWindows()

        return captured_embedding, raw_frame

    def match_face(self, stored_embedding_bytes: bytes, captured_embedding: np.ndarray) -> float:
        """Compare stored embedding with captured embedding and return confidence percentage.
        Returns: Confidence percentage (0-100) derived from biometric similarity score
        """
        try:
            # Reconstruct stored embedding
            stored_embedding = np.frombuffer(stored_embedding_bytes, dtype=np.float32)

            # Calculate cosine similarity between embeddings
            similarity = np.dot(stored_embedding, captured_embedding) / (
                np.linalg.norm(stored_embedding) * np.linalg.norm(captured_embedding)
            )

            # Convert similarity to confidence percentage
            # Using a calibrated mapping: similarity 0.4 -> 0%, similarity 0.8 -> 100%
            # This provides a monotonic mapping from similarity to percentage
            if similarity <= self.similarity_threshold:
                confidence = 0.0
            else:
                # Linear mapping from threshold to 1.0
                confidence = ((similarity - self.similarity_threshold) /
                            (1.0 - self.similarity_threshold)) * 100.0

            # Ensure confidence is between 0 and 100
            confidence = max(0.0, min(100.0, confidence))

            return confidence

        except Exception as e:
            print(f"Error in face matching: {e}")
            return 0.0

    def is_match_accepted(self, confidence: float) -> bool:
        """Determine if the confidence level meets the acceptance threshold."""
        return confidence > 0.0  # Any confidence above 0% is considered a match

    def get_acceptance_threshold(self) -> float:
        """Get the current similarity threshold."""
        return self.similarity_threshold