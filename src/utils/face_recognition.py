"""
Face recognition utilities for SLAT.
Compliant with Mandatory Face Recognition Architecture specifications.
Uses MTCNN for detection and FaceNet for recognition.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List
import os
import sys
from mtcnn import MTCNN
from facenet_pytorch import InceptionResnetV1
import torch
from PIL import Image

def resource_path(rel_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, rel_path)

class FaceRecognition:
    def __init__(self):
        # Initialize MTCNN detector
        self.detector = MTCNN(min_face_size=80)
        
        # Initialize FaceNet recognition model (pre-trained on VGGFace2)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model from local weights (offline deployment)
        weights_path = resource_path("models/20180402-114759-vggface2.pt")
        self.recognition_model = InceptionResnetV1(pretrained=None).eval()
        
        # Load state dict and remove unexpected keys
        state_dict = torch.load(weights_path, map_location=self.device)
        # Remove logits layers (only needed for training)
        state_dict = {k: v for k, v in state_dict.items() if not k.startswith('logits')}
        self.recognition_model.load_state_dict(state_dict, strict=False)
        self.recognition_model = self.recognition_model.to(self.device)
        
        # Similarity threshold for FaceNet (cosine similarity)
        self.similarity_threshold = 0.5  # Calibrated for FaceNet embeddings
        
        # Face detection confidence threshold
        self.detection_threshold = 0.85  # Lowered for better detection
        
        print(f"Initialized MTCNN detector and FaceNet model on {self.device}")

    def _detect_faces(self, frame: np.ndarray) -> List[dict]:
        """Detect faces using MTCNN.
        Returns: List of face dictionaries with bbox, confidence, and landmarks
        """
        try:
            # Convert BGR to RGB for MTCNN
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            detections = self.detector.detect_faces(rgb_frame)
            
            faces = []
            for detection in detections:
                confidence = detection['confidence']
                if confidence >= self.detection_threshold:
                    x, y, w, h = detection['box']
                    # Convert to x1, y1, x2, y2 format
                    bbox = [x, y, x + w, y + h]
                    faces.append({
                        'bbox': bbox,
                        'confidence': confidence,
                        'keypoints': detection['keypoints']
                    })
            
            return faces
        
        except Exception as e:
            print(f"Error in MTCNN face detection: {e}")
            return []

    def _extract_embedding(self, frame: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """Extract FaceNet embedding from a detected face.
        Args:
            frame: Image frame (BGR)
            bbox: Bounding box [x1, y1, x2, y2]
        Returns: 512-dimensional embedding vector or None
        """
        try:
            x1, y1, x2, y2 = bbox
            
            # Ensure coordinates are within frame bounds
            h, w = frame.shape[:2]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            
            # Crop and preprocess face
            face = frame[y1:y2, x1:x2]
            if face.size == 0:
                return None
            
            # Convert BGR to RGB
            face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            
            # Resize to 160x160 (FaceNet input size)
            face_resized = cv2.resize(face_rgb, (160, 160))
            
            # Convert to tensor and normalize
            face_tensor = torch.from_numpy(face_resized).permute(2, 0, 1).float()
            face_tensor = (face_tensor - 127.5) / 128.0
            face_tensor = face_tensor.unsqueeze(0).to(self.device)
            
            # Extract embedding
            with torch.no_grad():
                embedding = self.recognition_model(face_tensor)
            
            # Convert to numpy and normalize
            embedding = embedding.cpu().numpy().flatten()
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
        
        except Exception as e:
            print(f"Error extracting embedding: {e}")
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

            # Detect faces using MTCNN
            faces = self._detect_faces(frame)

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
                for face_info in faces:
                    bbox = face_info['bbox']
                    x1, y1, x2, y2 = [int(v) for v in bbox]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            else:
                face_info = faces[0]
                bbox = face_info['bbox']
                confidence = face_info['confidence']

                if confidence >= self.detection_threshold:
                    color = (0, 255, 0)
                    status = f"BON - Maintien position ({countdown}/20)"
                    countdown += 1

                    # Extract embedding from this frame
                    current_embedding = self._extract_embedding(frame, [int(v) for v in bbox])
                    
                    # Update best embedding
                    if current_embedding is not None and confidence > best_quality:
                        best_quality = confidence
                        best_embedding = current_embedding

                    # Auto-capture after 20 frames (~0.7s)
                    if countdown >= 20:
                        status = "CAPTURE RÉUSSIE!"
                        x1, y1, x2, y2 = [int(v) for v in bbox]
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
                x1, y1, x2, y2 = [int(v) for v in bbox]
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

    def detect_and_extract_face(self, frame: np.ndarray) -> Optional[Tuple[np.ndarray, dict]]:
        """Detect a single face in the frame and extract its embedding.
        Args:
            frame: Input frame from camera
        Returns: (embedding_vector, face_info) or (None, None)
            face_info contains: {'bbox': [x1, y1, x2, y2], 'confidence': float}
        """
        try:
            # Detect faces using MTCNN
            faces = self._detect_faces(frame)
            
            if len(faces) != 1:
                return None, None
            
            face_info = faces[0]
            bbox = face_info['bbox']
            confidence = face_info['confidence']
            
            if confidence < self.detection_threshold:
                return None, None
            
            # Extract embedding
            embedding = self._extract_embedding(frame, [int(v) for v in bbox])
            
            if embedding is None:
                return None, None
            
            return embedding, face_info
        
        except Exception as e:
            print(f"Error in detect_and_extract_face: {e}")
            return None, None

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

            # Detect faces using MTCNN
            faces = self._detect_faces(frame)

            if len(faces) == 1:
                face_info = faces[0]
                bbox = face_info['bbox']
                confidence = face_info['confidence']

                if confidence >= self.detection_threshold:
                    # Extract embedding
                    captured_embedding = self._extract_embedding(frame, [int(v) for v in bbox])
                    
                    if captured_embedding is not None:
                        raw_frame = frame.copy()
                        
                        x1, y1, x2, y2 = [int(v) for v in bbox]
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

            # Normalize both embeddings
            stored_embedding = stored_embedding / np.linalg.norm(stored_embedding)
            captured_embedding = captured_embedding / np.linalg.norm(captured_embedding)

            # Calculate cosine similarity between embeddings
            similarity = np.dot(stored_embedding, captured_embedding)

            # Convert similarity to confidence percentage
            # FaceNet embeddings typically range from 0.3 to 1.0 for matches
            # Threshold of 0.6 is a good balance
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