"""
Two-Factor Authentication Utilities
Supports TOTP, Email OTP, SMS OTP, and Biometric authentication
"""
import pyotp
import qrcode
import io
import base64
import secrets
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app.core.models import User
from app.utils.db_utils import db


def generate_totp_secret():
    """Generate a new TOTP secret key"""
    return pyotp.random_base32()


def generate_totp_uri(user_email, secret, issuer_name="Inventory App"):
    """Generate TOTP URI for QR code"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=user_email,
        issuer_name=issuer_name
    )


def generate_qr_code(uri):
    """Generate QR code image as base64 string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')  # Format must be a single format string, not a list
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"


def verify_totp(secret, token):
    """Verify TOTP token"""
    if not secret:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)  # Allow 1 time step tolerance


def generate_otp_code(length=6):
    """Generate a random OTP code"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def hash_otp_code(otp_code):
    """Hash OTP code for storage"""
    return generate_password_hash(otp_code)


def verify_otp_code(stored_hash, provided_code):
    """Verify OTP code against stored hash"""
    return check_password_hash(stored_hash, provided_code)


def set_user_otp(user, otp_code, expires_in_minutes=10):
    """Set OTP code for user with expiration"""
    user.otp_code = hash_otp_code(otp_code)
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    db.session.commit()
    return otp_code


def verify_user_otp(user, provided_code):
    """Verify user's OTP code"""
    if not user.otp_code or not user.otp_expires_at:
        return False
    
    if datetime.utcnow() > user.otp_expires_at:
        return False  # OTP expired
    
    if verify_otp_code(user.otp_code, provided_code):
        # Clear OTP after successful verification
        user.otp_code = None
        user.otp_expires_at = None
        db.session.commit()
        return True
    
    return False


def clear_user_otp(user):
    """Clear user's OTP code"""
    user.otp_code = None
    user.otp_expires_at = None
    db.session.commit()


def simulate_biometric_verification(biometric_data):
    """
    Simulate biometric verification
    In production, this would integrate with actual biometric hardware/API
    """
    # For simulation, accept any non-empty biometric_data
    # In real implementation, verify against stored biometric template
    if biometric_data and len(biometric_data) > 0:
        return True
    return False

