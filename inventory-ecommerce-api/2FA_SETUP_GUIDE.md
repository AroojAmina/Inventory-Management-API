# Two-Factor Authentication (2FA) Setup Guide

This guide explains how to use the enhanced authentication system with 2FA support.

## 🚀 New Features Added

1. **Two-Factor Authentication (2FA)**
   - TOTP (Google Authenticator)
   - Email OTP
   - SMS OTP (via Twilio)
   - Biometric Authentication (simulated)

2. **Enhanced Security**
   - Login attempt tracking
   - Account lockout after failed attempts
   - Security logging

3. **Role-Based Authorization**
   - Role assignment endpoint
   - Enhanced permission system

## 📋 Database Migration

After pulling these changes, create and run a migration:

```bash
flask db migrate -m "Add 2FA and login tracking"
flask db upgrade
```

## 🔧 Environment Variables

Add these to your `.env` file:

```env
# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Email Configuration (for Email OTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Twilio Configuration (for SMS OTP)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

**Note:** If email/SMS services are not configured, the system will still work in development mode (OTP codes will be printed to console).

## 📚 API Endpoints

### Authentication Endpoints

#### 1. Signup
```http
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "phone_number": "+1234567890"  // optional
}
```

#### 2. Login (Enhanced)
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response if 2FA required:**
```json
{
  "message": "Password verified. 2FA required.",
  "requires_2fa": true,
  "available_methods": ["totp", "email", "sms", "biometric"],
  "user_id": 1
}
```

**Response if no 2FA:**
```json
{
  "message": "Login successful",
  "access_token": "...",
  "refresh_token": "...",
  "requires_2fa": false
}
```

### TOTP (Google Authenticator) Endpoints

#### 3. Setup TOTP
```http
POST /api/auth/2fa/setup
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "TOTP setup successful. Scan QR code with Google Authenticator.",
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,...",
  "uri": "otpauth://totp/..."
}
```

#### 4. Enable TOTP
```http
POST /api/auth/2fa/enable
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "totp_code": "123456"
}
```

#### 5. Verify TOTP During Login
```http
POST /api/auth/2fa/verify-totp
Content-Type: application/json

{
  "user_id": 1,
  "totp_code": "123456"
}
```

### Email OTP Endpoints

#### 6. Send Email OTP
```http
POST /api/auth/2fa/send-email-code
Content-Type: application/json

{
  "user_id": 1
}
```

#### 7. Verify Email OTP
```http
POST /api/auth/2fa/verify-email-code
Content-Type: application/json

{
  "user_id": 1,
  "otp_code": "123456"
}
```

### SMS OTP Endpoints

#### 8. Send SMS OTP
```http
POST /api/auth/2fa/send-sms-code
Content-Type: application/json

{
  "user_id": 1
}
```

#### 9. Verify SMS OTP
```http
POST /api/auth/2fa/verify-sms-code
Content-Type: application/json

{
  "user_id": 1,
  "otp_code": "123456"
}
```

### Biometric Authentication Endpoints

#### 10. Enable Biometric
```http
POST /api/auth/2fa/enable-biometric
Authorization: Bearer <access_token>
```

#### 11. Verify Biometric
```http
POST /api/auth/2fa/verify-biometric
Content-Type: application/json

{
  "user_id": 1,
  "biometric_data": "simulated_biometric_data"
}
```

### Token Management

#### 12. Refresh Token
```http
POST /api/auth/token/refresh
Authorization: Bearer <refresh_token>
```

### Role Management

#### 13. Assign Role (Admin Only)
```http
POST /api/auth/roles/assign
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "user_id": 2,
  "role": "manager"  // Options: admin, manager, staff, customer
}
```

### Security Tracking

#### 14. Get Login Attempts
```http
GET /api/auth/login-attempts
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "login_attempts": [
    {
      "id": 1,
      "email": "user@example.com",
      "ip_address": "192.168.1.1",
      "success": true,
      "failure_reason": null,
      "timestamp": "2024-01-01T12:00:00"
    }
  ]
}
```

## 🔐 Security Features

### Account Lockout
- After **5 failed login attempts**, account is locked for **30 minutes**
- Lockout is automatically cleared after the time period
- Successful login resets the failed attempt counter

### Login Attempt Tracking
- All login attempts are logged with:
  - Email
  - IP address
  - User agent
  - Success/failure status
  - Failure reason
  - Timestamp

### 2FA Methods Priority
The system checks for 2FA in this order:
1. TOTP (if enabled)
2. SMS (if phone number exists)
3. Email (always available)
4. Biometric (if enabled)

## 🧪 Testing Flow

### Complete Login Flow with TOTP:

1. **Signup:**
   ```bash
   POST /api/auth/signup
   ```

2. **Login (get 2FA requirement):**
   ```bash
   POST /api/auth/login
   # Response: requires_2fa: true, user_id: 1
   ```

3. **Setup TOTP:**
   ```bash
   POST /api/auth/2fa/setup
   # Scan QR code with Google Authenticator
   ```

4. **Enable TOTP:**
   ```bash
   POST /api/auth/2fa/enable
   # Enter code from Google Authenticator
   ```

5. **Login with 2FA:**
   ```bash
   POST /api/auth/login
   # Get: requires_2fa: true
   
   POST /api/auth/2fa/verify-totp
   # Enter code from Google Authenticator
   # Get: access_token and refresh_token
   ```

## 📝 Notes

- OTP codes expire after **10 minutes**
- TOTP codes are valid for **30 seconds** (standard TOTP window)
- Account lockout duration: **30 minutes**
- Maximum failed attempts: **5**
- Admins can view all login attempts, regular users see only their own

## 🐛 Troubleshooting

### Email OTP not sending?
- Check SMTP configuration in `.env`
- In development, OTP codes are printed to console
- Check email spam folder

### SMS OTP not sending?
- Verify Twilio credentials in `.env`
- Check phone number format (must include country code)
- In development, OTP codes are printed to console

### TOTP not working?
- Ensure you scanned the QR code correctly
- Check that your device time is synchronized
- Try manual entry of the secret key

### Account locked?
- Wait 30 minutes for automatic unlock
- Or manually reset `account_locked_until` in database (admin only)

