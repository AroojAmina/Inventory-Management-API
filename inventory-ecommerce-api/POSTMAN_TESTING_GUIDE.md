# Postman Testing Guide for 2FA Authentication API

This guide will help you test all authentication endpoints using Postman.

## 📋 Table of Contents
1. [Postman Setup](#postman-setup)
2. [Environment Variables](#environment-variables)
3. [Testing Flow](#testing-flow)
4. [Endpoint Examples](#endpoint-examples)

---

## 🔧 Postman Setup

### Step 1: Create a New Collection
1. Open Postman
2. Click **"New"** → **"Collection"**
3. Name it: **"Inventory API - Authentication"**

### Step 2: Set Up Environment Variables
1. Click the **gear icon** (⚙️) in the top right
2. Click **"Add"** to create a new environment
3. Name it: **"Inventory API Local"**
4. Add these variables:

| Variable Name | Initial Value | Current Value |
|--------------|---------------|---------------|
| `base_url` | `http://localhost:5000` | `http://localhost:5000` |
| `access_token` | (leave empty) | (leave empty) |
| `refresh_token` | (leave empty) | (leave empty) |
| `user_id` | (leave empty) | (leave empty) |
| `test_email` | `test@example.com` | `test@example.com` |
| `test_password` | `Test123!@#` | `Test123!@#` |

5. Click **"Save"**
6. Select your environment from the dropdown in the top right

---

## 🧪 Testing Flow

### Complete Testing Sequence:

1. **Signup** → Get tokens
2. **Login** → Check if 2FA is required
3. **Setup TOTP** → Get QR code
4. **Enable TOTP** → Activate 2FA
5. **Login with 2FA** → Full flow
6. **Test Email OTP** → Alternative 2FA
7. **Test SMS OTP** → Alternative 2FA
8. **Refresh Token** → Token management
9. **View Login Attempts** → Security tracking

---

## 📝 Endpoint Examples

### 1. Signup (User Registration)

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/signup`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body (raw JSON):**
  ```json
  {
    "email": "{{test_email}}",
    "password": "{{test_password}}",
    "phone_number": "+1234567890"
  }
  ```

**Expected Response (201):**
```json
{
  "message": "User created successfully",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Postman Script (to save tokens):**
Add this in the **Tests** tab:
```javascript
if (pm.response.code === 201) {
    var jsonData = pm.response.json();
    pm.environment.set("access_token", jsonData.access_token);
    pm.environment.set("refresh_token", jsonData.refresh_token);
    pm.environment.set("user_id", jsonData.user_id || "1");
}
```

---

### 2. Login (Check 2FA Requirement)

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/login`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body (raw JSON):**
  ```json
  {
    "email": "{{test_email}}",
    "password": "{{test_password}}"
  }
  ```

**Expected Response (200) - If 2FA Required:**
```json
{
  "message": "Password verified. 2FA required.",
  "requires_2fa": true,
  "available_methods": ["totp", "email", "sms"],
  "user_id": 1
}
```

**Expected Response (200) - If No 2FA:**
```json
{
  "message": "Login successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "requires_2fa": false
}
```

**Postman Script:**
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    if (jsonData.requires_2fa) {
        pm.environment.set("user_id", jsonData.user_id);
        console.log("2FA Required! Available methods:", jsonData.available_methods);
    } else {
        pm.environment.set("access_token", jsonData.access_token);
        pm.environment.set("refresh_token", jsonData.refresh_token);
    }
}
```

---

### 3. Setup TOTP (Generate QR Code)

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/2fa/setup`
- **Headers:**
  ```
  Authorization: Bearer {{access_token}}
  Content-Type: application/json
  ```

**Expected Response (200):**
```json
{
  "message": "TOTP setup successful. Scan QR code with Google Authenticator.",
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "uri": "otpauth://totp/Inventory%20App:test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Inventory%20App"
}
```

**Postman Script (to save secret):**
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("totp_secret", jsonData.secret);
    console.log("QR Code URI:", jsonData.uri);
    console.log("Secret (for manual entry):", jsonData.secret);
}
```

**To View QR Code:**
1. Copy the `qr_code` value (base64 string)
2. Go to: https://base64.guru/converter/decode/image
3. Paste the base64 string (without `data:image/png;base64,` prefix)
4. Download and scan with Google Authenticator

---

### 4. Enable TOTP (Activate 2FA)

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/2fa/enable`
- **Headers:**
  ```
  Authorization: Bearer {{access_token}}
  Content-Type: application/json
  ```
- **Body (raw JSON):**
  ```json
  {
    "totp_code": "123456"
  }
  ```
  > **Note:** Get the 6-digit code from Google Authenticator app

**Expected Response (200):**
```json
{
  "message": "TOTP enabled successfully"
}
```

---

### 5. Verify TOTP During Login

**Step 1: Login First**
- Use the **Login** endpoint (step 2)
- You'll get: `requires_2fa: true` and `user_id`

**Step 2: Verify TOTP**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/2fa/verify-totp`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body (raw JSON):**
  ```json
  {
    "user_id": "{{user_id}}",
    "totp_code": "123456"
  }
  ```
  > **Note:** Get the 6-digit code from Google Authenticator

**Expected Response (200):**
```json
{
  "message": "2FA verified. Login successful.",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Postman Script:**
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("access_token", jsonData.access_token);
    pm.environment.set("refresh_token", jsonData.refresh_token);
}
```

---

### 6. Send Email OTP

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/2fa/send-email-code`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body (raw JSON):**
  ```json
  {
    "user_id": "{{user_id}}"
  }
  ```

**Expected Response (200):**
```json
{
  "message": "OTP code sent to your email"
}
```

> **Note:** Check your email or console logs for the OTP code (if SMTP not configured)

---

### 7. Verify Email OTP

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/2fa/verify-email-code`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body (raw JSON):**
  ```json
  {
    "user_id": "{{user_id}}",
    "otp_code": "123456"
  }
  ```
  > **Note:** Use the OTP code received via email

**Expected Response (200):**
```json
{
  "message": "Email OTP verified. Login successful.",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 8. Send SMS OTP

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/2fa/send-sms-code`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body (raw JSON):**
  ```json
  {
    "user_id": "{{user_id}}"
  }
  ```

**Expected Response (200):**
```json
{
  "message": "OTP code sent to your phone"
}
```

> **Note:** Check your phone or console logs for the OTP code (if Twilio not configured)

---

### 9. Verify SMS OTP

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/2fa/verify-sms-code`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body (raw JSON):**
  ```json
  {
    "user_id": "{{user_id}}",
    "otp_code": "123456"
  }
  ```
  > **Note:** Use the OTP code received via SMS

**Expected Response (200):**
```json
{
  "message": "SMS OTP verified. Login successful.",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 10. Enable Biometric

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/2fa/enable-biometric`
- **Headers:**
  ```
  Authorization: Bearer {{access_token}}
  Content-Type: application/json
  ```

**Expected Response (200):**
```json
{
  "message": "Biometric authentication enabled"
}
```

---

### 11. Verify Biometric

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/2fa/verify-biometric`
- **Headers:**
  ```
  Content-Type: application/json
  ```
- **Body (raw JSON):**
  ```json
  {
    "user_id": "{{user_id}}",
    "biometric_data": "simulated_fingerprint_data"
  }
  ```

**Expected Response (200):**
```json
{
  "message": "Biometric verification successful. Login successful.",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 12. Refresh Token

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/token/refresh`
- **Headers:**
  ```
  Authorization: Bearer {{refresh_token}}
  Content-Type: application/json
  ```

**Expected Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Postman Script:**
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("access_token", jsonData.access_token);
}
```

---

### 13. Assign Role (Admin Only)

**Request:**
- **Method:** `POST`
- **URL:** `{{base_url}}/api/auth/roles/assign`
- **Headers:**
  ```
  Authorization: Bearer {{access_token}}
  Content-Type: application/json
  ```
- **Body (raw JSON):**
  ```json
  {
    "user_id": 2,
    "role": "manager"
  }
  ```
  > **Note:** Must be logged in as admin

**Expected Response (200):**
```json
{
  "message": "Role 'manager' assigned successfully"
}
```

---

### 14. Get Login Attempts

**Request:**
- **Method:** `GET`
- **URL:** `{{base_url}}/api/auth/login-attempts`
- **Headers:**
  ```
  Authorization: Bearer {{access_token}}
  ```

**Expected Response (200):**
```json
{
  "login_attempts": [
    {
      "id": 1,
      "email": "test@example.com",
      "ip_address": "127.0.0.1",
      "success": true,
      "failure_reason": null,
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "id": 2,
      "email": "test@example.com",
      "ip_address": "127.0.0.1",
      "success": false,
      "failure_reason": "wrong_password",
      "timestamp": "2024-01-01T11:55:00"
    }
  ]
}
```

---

## 🎯 Quick Testing Scenarios

### Scenario 1: Complete TOTP Flow
1. Signup → Save tokens
2. Setup TOTP → Scan QR code
3. Enable TOTP → Enter code from app
4. Login → Get 2FA requirement
5. Verify TOTP → Enter code from app → Get tokens

### Scenario 2: Email OTP Flow
1. Login → Get 2FA requirement
2. Send Email OTP → Check email/console
3. Verify Email OTP → Enter code → Get tokens

### Scenario 3: Account Lockout Test
1. Try login with wrong password 5 times
2. 6th attempt should return: `Account is locked`
3. Wait 30 minutes or manually reset in database

### Scenario 4: Token Refresh
1. Use refresh token to get new access token
2. Use new access token for protected endpoints

---

## 🔍 Troubleshooting

### Issue: "Token is missing"
- **Solution:** Make sure you're using `Authorization: Bearer {{access_token}}` header

### Issue: "Invalid token"
- **Solution:** Token might be expired. Use refresh token to get a new one.

### Issue: "Account is locked"
- **Solution:** Wait 30 minutes or reset `account_locked_until` in database

### Issue: "TOTP code invalid"
- **Solution:** 
  - Check device time is synchronized
  - Make sure you're using the latest code from Google Authenticator
  - Codes expire every 30 seconds

### Issue: "OTP code expired"
- **Solution:** OTP codes expire after 10 minutes. Request a new one.

---

## 📦 Postman Collection JSON

You can import this collection directly into Postman:

```json
{
  "info": {
    "name": "Inventory API - Authentication",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "1. Signup",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"{{test_email}}\",\n  \"password\": \"{{test_password}}\",\n  \"phone_number\": \"+1234567890\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/auth/signup",
          "host": ["{{base_url}}"],
          "path": ["api", "auth", "signup"]
        }
      }
    },
    {
      "name": "2. Login",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"{{test_email}}\",\n  \"password\": \"{{test_password}}\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/auth/login",
          "host": ["{{base_url}}"],
          "path": ["api", "auth", "login"]
        }
      }
    }
  ]
}
```

---

## ✅ Tips for Testing

1. **Use Environment Variables:** Always use `{{variable_name}}` for tokens and URLs
2. **Save Responses:** Use Postman scripts to automatically save tokens
3. **Test Error Cases:** Try invalid credentials, expired tokens, etc.
4. **Check Console:** For development, OTP codes are printed to console
5. **Use Pre-request Scripts:** To automatically add timestamps or generate test data

---

Happy Testing! 🚀


