# Complete List of Registered Endpoints

## 🔍 How to Verify Endpoints Are Registered

### Method 1: Use the Routes Endpoint
After starting your Flask app, visit:
```
GET http://localhost:5000/api/routes
```

This will show all registered routes in JSON format.

### Method 2: Run Verification Script
```bash
cd inventory-ecommerce-api
python verify_endpoints.py
```

### Method 3: Check Flask Console
```python
from app import create_app
app = create_app()
with app.app_context():
    for rule in app.url_map.iter_rules():
        if 'auth' in rule.rule:
            print(rule.rule)
```

---

## 📋 All Authentication Endpoints

### Core Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/signup` | User registration | No |
| POST | `/api/auth/login` | User login (with 2FA support) | No |
| POST | `/api/auth/token/refresh` | Refresh access token | Yes (Refresh Token) |

### TOTP (Google Authenticator)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/2fa/setup` | Generate QR code for TOTP | Yes |
| POST | `/api/auth/2fa/enable` | Enable TOTP after verification | Yes |
| POST | `/api/auth/2fa/verify-totp` | Verify TOTP during login | No |

### Email OTP

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/2fa/send-email-code` | Send OTP to email | No |
| POST | `/api/auth/2fa/verify-email-code` | Verify email OTP | No |

### SMS OTP

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/2fa/send-sms-code` | Send OTP to phone | No |
| POST | `/api/auth/2fa/verify-sms-code` | Verify SMS OTP | No |

### Biometric

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/2fa/enable-biometric` | Enable biometric auth | Yes |
| POST | `/api/auth/2fa/verify-biometric` | Verify biometric | No |

### Role Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/roles/assign` | Assign role to user | Yes (Admin only) |

### Security Tracking

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/auth/login-attempts` | View login attempt history | Yes |

### Utility Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/healthcheck` | Health check | No |
| GET | `/api/routes` | List all registered routes | No |

---

## ✅ Verification Checklist

- [ ] Flask app is running (`python run.py`)
- [ ] Health check works: `GET http://localhost:5000/healthcheck`
- [ ] Routes endpoint works: `GET http://localhost:5000/api/routes`
- [ ] Signup endpoint works: `POST http://localhost:5000/api/auth/signup`
- [ ] Login endpoint works: `POST http://localhost:5000/api/auth/login`

---

## 🐛 If Endpoints Are Not Showing

1. **Restart Flask App:**
   ```bash
   # Stop the app (Ctrl+C)
   python run.py
   ```

2. **Check for Import Errors:**
   ```bash
   python -c "from app import create_app; app = create_app()"
   ```

3. **Verify Blueprint Registration:**
   - Check `app/__init__.py` line 63
   - Should have: `app.register_blueprint(auth_bp, url_prefix='/api/auth/')`

4. **Check for Syntax Errors:**
   ```bash
   python -m py_compile app/api/inventory/auth.py
   ```

5. **Run Verification Script:**
   ```bash
   python verify_endpoints.py
   ```

---

## 📝 Quick Test Commands

### Test Signup
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}'
```

### Test Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}'
```

### List All Routes
```bash
curl http://localhost:5000/api/routes
```

---

## 🔗 Full URL Examples

All endpoints use the base URL: `http://localhost:5000`

- Signup: `http://localhost:5000/api/auth/signup`
- Login: `http://localhost:5000/api/auth/login`
- Setup TOTP: `http://localhost:5000/api/auth/2fa/setup`
- Verify TOTP: `http://localhost:5000/api/auth/2fa/verify-totp`
- Send Email OTP: `http://localhost:5000/api/auth/2fa/send-email-code`
- Verify Email OTP: `http://localhost:5000/api/auth/2fa/verify-email-code`
- Send SMS OTP: `http://localhost:5000/api/auth/2fa/send-sms-code`
- Verify SMS OTP: `http://localhost:5000/api/auth/2fa/verify-sms-code`
- Enable Biometric: `http://localhost:5000/api/auth/2fa/enable-biometric`
- Verify Biometric: `http://localhost:5000/api/auth/2fa/verify-biometric`
- Refresh Token: `http://localhost:5000/api/auth/token/refresh`
- Assign Role: `http://localhost:5000/api/auth/roles/assign`
- Login Attempts: `http://localhost:5000/api/auth/login-attempts`

---

All endpoints are registered when the Flask app starts. If you see 404 errors, make sure:
1. The app is running
2. You're using the correct URL (including `/api/auth/` prefix)
3. The HTTP method is correct (POST, GET, etc.)


