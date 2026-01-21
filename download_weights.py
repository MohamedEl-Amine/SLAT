"""
Download FaceNet pretrained weights for offline deployment
"""
import torch
from facenet_pytorch import InceptionResnetV1
import os

# Create models directory
os.makedirs("src/models", exist_ok=True)

# Load the pretrained model
print("Downloading pretrained weights...")
model = InceptionResnetV1(pretrained='vggface2').eval()

# Save the state dict
weights_path = "src/models/20180402-114759-vggface2.pt"
torch.save(model.state_dict(), weights_path)

print(f"✅ Weights saved to: {weights_path}")
print(f"File size: {os.path.getsize(weights_path) / (1024*1024):.2f} MB")
