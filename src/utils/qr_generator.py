"""
QR code generation utilities for SLAT.
"""

import qrcode
from PIL import Image
import io

def generate_qr(data: str) -> bytes:
    """Generate QR code image as bytes."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def decode_qr(image_bytes: bytes) -> Optional[str]:
    """Decode QR code from image bytes."""
    # This would require additional libraries like pyzbar
    # For now, placeholder
    pass