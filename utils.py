import random
import string
from datetime import datetime, timedelta
import base64
from io import BytesIO
from PIL import Image
import re

def generate_otp():
    """Generate a 6-digit OTP"""
    otp = ''.join(random.choices(string.digits, k=6))
    return otp

def send_otp(phone_number, otp):
    """
    Simulate sending OTP to phone number
    In production, this would integrate with an SMS service
    """
    print(f"[SIMULATED SMS] Sending OTP {otp} to {phone_number}")
    # In production, you would use an SMS service like Twilio here
    return True

def is_valid_phone(phone):
    """Validate Indian phone number format"""
    # Regex for Indian phone numbers (10 digits, optionally starting with +91)
    pattern = r'^(\+91)?[6-9]\d{9}$'
    return bool(re.match(pattern, phone))

def normalize_phone(phone):
    """Normalize phone number to a standard format"""
    # Remove +91 prefix if present
    if phone.startswith('+91'):
        phone = phone[3:]
    return phone

def compress_image(image_data, max_size=(800, 800), quality=85):
    """Compress an image to reduce file size"""
    try:
        img = Image.open(BytesIO(image_data))
        img.thumbnail(max_size, Image.LANCZOS)
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"Error compressing image: {e}")
        return image_data

def get_issue_status_color(status):
    """Return Bootstrap color class based on issue status"""
    status_colors = {
        'not_resolved': 'danger',
        'ongoing': 'warning',
        'resolved': 'success'
    }
    return status_colors.get(status, 'secondary')

def calculate_stars(issue_count):
    """Calculate stars based on number of issues reported"""
    if issue_count >= 20:
        return 5
    elif issue_count >= 15:
        return 4
    elif issue_count >= 10:
        return 3
    elif issue_count >= 5:
        return 2
    elif issue_count >= 1:
        return 1
    return 0

def format_datetime(dt):
    """Format datetime for display"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime("%d %b %Y, %I:%M %p")
