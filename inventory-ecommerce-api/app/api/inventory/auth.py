"""
Enhanced Authentication API with 2FA Support
Includes: TOTP, Email OTP, SMS OTP, Biometric, and Login Attempt Tracking
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.core.models import User, LoginAttempt
from app.utils.db_utils import db
from app.schemas.user_schema import UserSchema
from marshmallow.exceptions import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.utils.two_factor_auth import (
    generate_totp_secret, generate_totp_uri, generate_qr_code, verify_totp,
    generate_otp_code, set_user_otp, verify_user_otp, clear_user_otp,
    simulate_biometric_verification
)
from app.utils.email_service import send_otp_email, send_welcome_email
from app.utils.sms_service import send_otp_sms

auth_bp = Blueprint("auth", __name__)
user_schema = UserSchema()

# Constants for login security
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


def log_login_attempt(email, success, failure_reason=None, user=None):
    """Log login attempt for security tracking"""
    try:
        attempt = LoginAttempt(
            user_id=user.id if user else None,
            email=email,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=success,
            failure_reason=failure_reason
        )
        db.session.add(attempt)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging login attempt: {str(e)}")


def handle_failed_login(user, email):
    """Handle failed login attempt - increment counter and lock account if needed"""
    if user:
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.account_locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            db.session.commit()
            return True, f"Account locked due to {MAX_FAILED_ATTEMPTS} failed attempts. Try again after {LOCKOUT_DURATION_MINUTES} minutes."
        
        db.session.commit()
        remaining = MAX_FAILED_ATTEMPTS - user.failed_login_attempts
        return False, f"Invalid credentials. {remaining} attempts remaining."
    
    return False, "Invalid email or password"


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """User registration endpoint"""
    data = request.get_json()
    try:
        user_data = user_schema.load(data)
        email = user_data.get("email")
        if not email:
            return {"error": "Email is required"}, 400
        if User.query.filter_by(email=email).first():
            return {"error": "Email already exists"}, 409

        user = User()
        user.email = email
        user.role = user_data.get("role", "customer")
        user.set_password(user_data["password"])
        user.phone_number = user_data.get("phone_number")
        db.session.add(user)
        db.session.commit()

        # Send welcome email
        send_welcome_email(email, user_data.get("name"))

        # Return JWT token after signup
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return {
            "message": "User created successfully",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 201
    except ValidationError as ve:
        return {"error": ve.messages}, 400
    except IntegrityError:
        db.session.rollback()
        return {"error": "Email already exists"}, 409
    except SQLAlchemyError as e:
        db.session.rollback()
        return {"error": str(e)}, 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Enhanced login endpoint with 2FA support
    First step: Verify email/password
    Returns 2FA requirement if enabled
    """
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return {"error": "Email and password are required"}, 400
    
    user = User.query.filter_by(email=email).first()
    
    # Check if account is locked
    if user and user.is_account_locked():
        log_login_attempt(email, False, "account_locked", user)
        return {
            "error": f"Account is locked. Try again after {user.account_locked_until.strftime('%Y-%m-%d %H:%M:%S')}"
        }, 423
    
    # Verify credentials
    if user and user.check_password(password) and user.is_active:
        # Check if 2FA is required
        requires_2fa = False
        two_fa_methods = []
        
        if user.is_totp_enabled:
            requires_2fa = True
            two_fa_methods.append("totp")
        
        if user.phone_number:
            requires_2fa = True
            two_fa_methods.append("sms")
        
        if user.email:
            requires_2fa = True
            two_fa_methods.append("email")
        
        if user.biometric_enabled:
            requires_2fa = True
            two_fa_methods.append("biometric")
        
        # Generate tokens (always return tokens on successful password verification)
        user.reset_failed_attempts()
        log_login_attempt(email, True, None, user)
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # If 2FA is required, return tokens along with 2FA requirement
        if requires_2fa:
            return {
                "message": "Password verified. 2FA required.",
                "requires_2fa": True,
                "available_methods": two_fa_methods,
                "user_id": user.id,
                "access_token": access_token,
                "refresh_token": refresh_token
            }, 200
        
        # No 2FA required - login fully successful
        return {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "requires_2fa": False
        }, 200
    
    # Failed login
    is_locked, message = handle_failed_login(user, email)
    log_login_attempt(email, False, "wrong_password", user)
    return {"error": message}, 401


@auth_bp.route("/2fa/setup", methods=["POST"])
@jwt_required()
def setup_totp():
    """Setup TOTP (Google Authenticator) for 2FA"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return {"error": "User not found"}, 404
        
        # Generate new secret
        secret = generate_totp_secret()
        user.totp_secret = secret
        db.session.commit()
        
        # Generate QR code
        uri = generate_totp_uri(user.email, secret)
        qr_code = generate_qr_code(uri)
        
        return {
            "message": "TOTP setup successful. Scan QR code with Google Authenticator.",
            "secret": secret,  # For manual entry if QR scan fails
            "qr_code": qr_code,
            "uri": uri
        }, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500


@auth_bp.route("/2fa/enable", methods=["POST"])
@jwt_required()
def enable_totp():
    """Enable TOTP after verification"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        data = request.get_json()
        totp_code = data.get("totp_code")
        
        if not user:
            return {"error": "User not found"}, 404
        
        if not user.totp_secret:
            return {"error": "TOTP not set up. Call /2fa/setup first"}, 400
        
        # Verify the TOTP code
        if verify_totp(user.totp_secret, totp_code):
            user.is_totp_enabled = True
            db.session.commit()
            return {"message": "TOTP enabled successfully"}, 200
        else:
            return {"error": "Invalid TOTP code"}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500


@auth_bp.route("/2fa/verify-totp", methods=["POST"])
def verify_totp_login():
    """Verify TOTP code during login"""
    data = request.get_json()
    user_id = data.get("user_id")
    totp_code = data.get("totp_code")
    
    if not user_id or not totp_code:
        return {"error": "user_id and totp_code are required"}, 400
    
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404
    
    if not user.is_totp_enabled or not user.totp_secret:
        return {"error": "TOTP not enabled for this user"}, 400
    
    if verify_totp(user.totp_secret, totp_code):
        user.reset_failed_attempts()
        log_login_attempt(user.email, True, None, user)
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return {
            "message": "2FA verified. Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 200
    else:
        log_login_attempt(user.email, False, "2fa_failed", user)
        return {"error": "Invalid TOTP code"}, 401


@auth_bp.route("/2fa/send-email-code", methods=["POST"])
def send_email_code():
    """Send OTP code via email"""
    data = request.get_json()
    user_id = data.get("user_id")
    
    if not user_id:
        return {"error": "user_id is required"}, 400
    
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404
    
    if not user.email:
        return {"error": "User email not found"}, 400
    
    # Generate and send OTP
    otp_code = generate_otp_code()
    set_user_otp(user, otp_code)
    
    if send_otp_email(user.email, otp_code):
        return {"message": "OTP code sent to your email"}, 200
    else:
        return {"error": "Failed to send email. Please try again."}, 500


@auth_bp.route("/2fa/verify-email-code", methods=["POST"])
def verify_email_code():
    """Verify email OTP code during login"""
    data = request.get_json()
    user_id = data.get("user_id")
    otp_code = data.get("otp_code")
    
    if not user_id or not otp_code:
        return {"error": "user_id and otp_code are required"}, 400
    
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404
    
    if verify_user_otp(user, otp_code):
        user.reset_failed_attempts()
        log_login_attempt(user.email, True, None, user)
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return {
            "message": "Email OTP verified. Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 200
    else:
        log_login_attempt(user.email, False, "2fa_failed", user)
        return {"error": "Invalid or expired OTP code"}, 401


@auth_bp.route("/2fa/send-sms-code", methods=["POST"])
def send_sms_code():
    """Send OTP code via SMS"""
    data = request.get_json()
    user_id = data.get("user_id")
    
    if not user_id:
        return {"error": "user_id is required"}, 400
    
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404
    
    if not user.phone_number:
        return {"error": "User phone number not found"}, 400
    
    # Generate and send OTP
    otp_code = generate_otp_code()
    set_user_otp(user, otp_code)
    
    if send_otp_sms(user.phone_number, otp_code):
        return {"message": "OTP code sent to your phone"}, 200
    else:
        return {"error": "Failed to send SMS. Please try again."}, 500


@auth_bp.route("/2fa/verify-sms-code", methods=["POST"])
def verify_sms_code():
    """Verify SMS OTP code during login"""
    data = request.get_json()
    user_id = data.get("user_id")
    otp_code = data.get("otp_code")
    
    if not user_id or not otp_code:
        return {"error": "user_id and otp_code are required"}, 400
    
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404
    
    if verify_user_otp(user, otp_code):
        user.reset_failed_attempts()
        log_login_attempt(user.email, True, None, user)
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return {
            "message": "SMS OTP verified. Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 200
    else:
        log_login_attempt(user.email, False, "2fa_failed", user)
        return {"error": "Invalid or expired OTP code"}, 401


@auth_bp.route("/2fa/verify-biometric", methods=["POST"])
def verify_biometric():
    """Simulate biometric verification during login"""
    data = request.get_json()
    user_id = data.get("user_id")
    biometric_data = data.get("biometric_data")
    
    if not user_id or not biometric_data:
        return {"error": "user_id and biometric_data are required"}, 400
    
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404
    
    if not user.biometric_enabled:
        return {"error": "Biometric authentication not enabled for this user"}, 400
    
    # Simulate biometric verification
    if simulate_biometric_verification(biometric_data):
        user.biometric_verified = True
        user.reset_failed_attempts()
        log_login_attempt(user.email, True, None, user)
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return {
            "message": "Biometric verification successful. Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 200
    else:
        log_login_attempt(user.email, False, "2fa_failed", user)
        return {"error": "Biometric verification failed"}, 401


@auth_bp.route("/2fa/enable-biometric", methods=["POST"])
@jwt_required()
def enable_biometric():
    """Enable biometric authentication for user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return {"error": "User not found"}, 404
        
        user.biometric_enabled = True
        db.session.commit()
        
        return {"message": "Biometric authentication enabled"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500


@auth_bp.route("/token/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return {"access_token": access_token}, 200


@auth_bp.route("/roles/assign", methods=["POST"])
@jwt_required()
def assign_role():
    """Assign role to user (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.role != "admin":
            return {"error": "Only admins can assign roles"}, 403
        
        data = request.get_json()
        user_id = data.get("user_id")
        new_role = data.get("role")
        
        if not user_id or not new_role:
            return {"error": "user_id and role are required"}, 400
        
        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}, 404
        
        # Validate role
        valid_roles = ["admin", "manager", "staff", "customer"]
        if new_role not in valid_roles:
            return {"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}, 400
        
        user.role = new_role
        db.session.commit()
        
        return {"message": f"Role '{new_role}' assigned successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500


@auth_bp.route("/login-attempts", methods=["GET"])
@jwt_required()
def get_login_attempts():
    """Get login attempts for current user (admin can see all)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return {"error": "User not found"}, 404
        
        # Admins can see all attempts, others see only their own
        if current_user.role == "admin":
            attempts = LoginAttempt.query.order_by(LoginAttempt.timestamp.desc()).limit(100).all()
        else:
            attempts = LoginAttempt.query.filter_by(user_id=current_user_id).order_by(LoginAttempt.timestamp.desc()).limit(50).all()
        
        attempts_data = [{
            "id": attempt.id,
            "email": attempt.email,
            "ip_address": attempt.ip_address,
            "success": attempt.success,
            "failure_reason": attempt.failure_reason,
            "timestamp": attempt.timestamp.isoformat() if attempt.timestamp else None
        } for attempt in attempts]
        
        return {"login_attempts": attempts_data}, 200
    except Exception as e:
        return {"error": str(e)}, 500
