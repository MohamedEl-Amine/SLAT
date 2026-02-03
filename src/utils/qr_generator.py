"""
QR code generation utilities for SLAT.
"""

import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
from typing import Optional

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

def generate_qr_with_text(employee_id: str, name: str) -> bytes:
    """Generate QR code image with employee ID and name overlaid as bytes.
    Image size is approximately 6cm x 6cm at 300 DPI (708x708 pixels).
    """
    qr = qrcode.QRCode(version=1, box_size=33, border=5)
    qr.add_data(employee_id)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Convert to RGB for drawing
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)

    # Try to use a default font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()

    # Add employee ID at the top
    text_id = f"ID: {employee_id}"
    bbox_id = draw.textbbox((0, 0), text_id, font=font)
    text_width_id = bbox_id[2] - bbox_id[0]
    x_id = (img.width - text_width_id) // 2
    draw.text((x_id, 20), text_id, fill='black', font=font)

    # Add employee name at the bottom
    text_name = f"Name: {name}"
    bbox_name = draw.textbbox((0, 0), text_name, font=font)
    text_width_name = bbox_name[2] - bbox_name[0]
    x_name = (img.width - text_width_name) // 2
    draw.text((x_name, img.height - 70), text_name, fill='black', font=font)

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def decode_qr(image_bytes: bytes) -> Optional[str]:
    """Decode QR code from image bytes."""
    # This would require additional libraries like pyzbar
    # For now, placeholder
    pass