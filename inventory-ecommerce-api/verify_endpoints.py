"""
Quick script to verify all authentication endpoints are registered
Run this to check if your endpoints are properly set up
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    
    app = create_app()
    
    print("=" * 70)
    print("AUTHENTICATION ENDPOINTS VERIFICATION")
    print("=" * 70)
    print()
    
    # Expected auth endpoints
    expected_endpoints = [
        '/api/auth/signup',
        '/api/auth/login',
        '/api/auth/2fa/setup',
        '/api/auth/2fa/enable',
        '/api/auth/2fa/verify-totp',
        '/api/auth/2fa/send-email-code',
        '/api/auth/2fa/verify-email-code',
        '/api/auth/2fa/send-sms-code',
        '/api/auth/2fa/verify-sms-code',
        '/api/auth/2fa/verify-biometric',
        '/api/auth/2fa/enable-biometric',
        '/api/auth/token/refresh',
        '/api/auth/roles/assign',
        '/api/auth/login-attempts'
    ]
    
    # Get all registered routes
    registered_routes = []
    with app.app_context():
        for rule in app.url_map.iter_rules():
            if 'auth' in rule.rule:
                registered_routes.append(rule.rule)
    
    print("Expected Auth Endpoints:")
    print("-" * 70)
    for endpoint in expected_endpoints:
        if endpoint in registered_routes:
            print(f"✅ {endpoint}")
        else:
            print(f"❌ {endpoint} - NOT FOUND")
    
    print()
    print("All Registered Auth Routes:")
    print("-" * 70)
    for route in sorted(registered_routes):
        # Get methods for each route
        for rule in app.url_map.iter_rules():
            if rule.rule == route:
                methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
                print(f"  {route:<50} [{methods}]")
                break
    
    print()
    print("=" * 70)
    
    # Check if all expected endpoints are registered
    missing = [ep for ep in expected_endpoints if ep not in registered_routes]
    if missing:
        print(f"⚠️  WARNING: {len(missing)} endpoint(s) not found!")
        print("   Missing endpoints:")
        for ep in missing:
            print(f"     - {ep}")
        print()
        print("   Possible causes:")
        print("   1. Import errors in auth.py")
        print("   2. Blueprint not registered in app/__init__.py")
        print("   3. Syntax errors in route definitions")
        sys.exit(1)
    else:
        print("✅ All authentication endpoints are properly registered!")
        print("=" * 70)
        sys.exit(0)
        
except ImportError as e:
    print(f"❌ Import Error: {str(e)}")
    print("   Make sure you're running this from the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


