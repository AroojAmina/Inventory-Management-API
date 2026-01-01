# Troubleshooting 404 Errors

## Common Causes and Solutions

### 1. Check if Flask App is Running

**Verify the app is running:**
```bash
# Check if the app is running
# You should see output like:
# * Running on http://127.0.0.1:5000
```

**Start the app:**
```bash
cd inventory-ecommerce-api
python run.py
```

Or:
```bash
flask run
```

---

### 2. Verify the Correct URL

**Base URL:** `http://localhost:5000` or `http://127.0.0.1:5000`

**Correct Endpoint URLs:**
- ✅ `POST http://localhost:5000/api/auth/signup`
- ✅ `POST http://localhost:5000/api/auth/login`
- ✅ `POST http://localhost:5000/api/auth/2fa/setup`
- ❌ `POST http://localhost:5000/signup` (WRONG - missing `/api/auth/`)
- ❌ `POST http://localhost:5000/auth/signup` (WRONG - missing `/api/`)

**All auth endpoints start with:** `/api/auth/`

---

### 3. Check for Import Errors

**Test if routes are loading:**
```bash
python -c "from app import create_app; app = create_app(); print([rule.rule for rule in app.url_map.iter_rules()])"
```

This should list all registered routes. If you see errors, there's an import issue.

**Common import errors:**
- Missing dependencies: `pip install -r requirements.txt`
- Database connection issues
- Module import errors

---

### 4. Verify Blueprint Registration

Check `app/__init__.py` line 63:
```python
app.register_blueprint(auth_bp, url_prefix='/api/auth/')
```

This should be present. If not, the routes won't be registered.

---

### 5. Test with Health Check Endpoint

**First, test the health check:**
```bash
GET http://localhost:5000/healthcheck
```

**Expected Response:** `OK` (200 status)

If this fails, the app isn't running or there's a configuration issue.

---

### 6. Check Flask App Context

**If running in Python shell:**
```python
from app import create_app
app = create_app()

# List all routes
with app.app_context():
    for rule in app.url_map.iter_rules():
        print(f"{rule.rule} -> {rule.endpoint}")
```

---

### 7. Verify Port Number

**Default Flask port:** `5000`

**If using a different port:**
- Check `run.py` for custom port
- Update Postman base_url accordingly

**Check what port Flask is using:**
```python
# In run.py, you can specify:
app.run(debug=True, port=5000)
```

---

### 8. Check for Route Conflicts

**Make sure no other routes conflict:**
- Check if `/api/auth/` is used elsewhere
- Verify blueprint names are unique

---

### 9. Database Migration Issues

**If routes load but endpoints fail:**
```bash
# Create migration
flask db migrate -m "Add 2FA tables"

# Apply migration
flask db upgrade
```

---

### 10. Quick Diagnostic Script

Create `test_routes.py`:
```python
from app import create_app

app = create_app()

print("=" * 50)
print("Registered Routes:")
print("=" * 50)

with app.app_context():
    for rule in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{rule.rule:50} {methods:20} {rule.endpoint}")

print("=" * 50)
print(f"Total routes: {len(list(app.url_map.iter_rules()))}")
```

Run it:
```bash
python test_routes.py
```

---

## Postman Testing Checklist

1. ✅ App is running (`python run.py`)
2. ✅ Base URL is correct (`http://localhost:5000`)
3. ✅ Full endpoint URL includes `/api/auth/`
4. ✅ HTTP method is correct (POST, GET, etc.)
5. ✅ Headers include `Content-Type: application/json`
6. ✅ Body is valid JSON (for POST requests)
7. ✅ Authorization header format: `Bearer <token>` (if required)

---

## Example: Correct Postman Request

**Request:**
```
Method: POST
URL: http://localhost:5000/api/auth/signup
Headers:
  Content-Type: application/json
Body (raw JSON):
{
  "email": "test@example.com",
  "password": "Test123!@#"
}
```

**If you get 404, check:**
1. Is the app running? → Check terminal
2. Is the URL correct? → Must include `/api/auth/`
3. Are there errors in terminal? → Check for import/database errors

---

## Common Error Messages

### "404 Not Found"
- **Cause:** Route not registered or wrong URL
- **Solution:** Verify URL includes `/api/auth/` prefix

### "500 Internal Server Error"
- **Cause:** Server-side error (database, import, etc.)
- **Solution:** Check terminal for error messages

### "Method Not Allowed"
- **Cause:** Wrong HTTP method (GET instead of POST)
- **Solution:** Use correct method (POST for signup/login)

---

## Still Getting 404?

1. **Restart the Flask app:**
   ```bash
   # Stop the app (Ctrl+C)
   # Then restart:
   python run.py
   ```

2. **Clear Python cache:**
   ```bash
   find . -type d -name __pycache__ -exec rm -r {} +
   find . -type f -name "*.pyc" -delete
   ```

3. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

4. **Check for syntax errors:**
   ```bash
   python -m py_compile app/api/inventory/auth.py
   ```

---

## Quick Test Commands

```bash
# Test if app starts without errors
python -c "from app import create_app; app = create_app(); print('App loaded successfully!')"

# Test route registration
python -c "from app import create_app; app = create_app(); print([r.rule for r in app.url_map.iter_rules() if 'auth' in r.rule])"
```

---

If none of these work, share:
1. The exact URL you're trying to access
2. The error message from terminal
3. Output from the diagnostic script above

