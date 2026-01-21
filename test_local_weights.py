"""
Test that face recognition loads from local weights
"""
import sys
sys.path.insert(0, 'src')

from utils.face_recognition import FaceRecognition

print("Testing FaceRecognition initialization with local weights...")
try:
    face_rec = FaceRecognition()
    print("✅ Successfully initialized FaceRecognition with local weights!")
    print(f"Device: {face_rec.device}")
    print(f"Model loaded: {type(face_rec.recognition_model)}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
