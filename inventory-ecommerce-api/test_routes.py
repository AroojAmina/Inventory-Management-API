"""
Quick diagnostic script to check if all routes are registered correctly
Run this to verify your Flask app is set up correctly
"""
from app import create_app

app = create_app()

print("=" * 70)
print("FLASK APP ROUTE DIAGNOSTIC")
print("=" * 70)
print()

# List all registered routes
print("Registered Routes:")
print("-" * 70)
print(f"{'Route':<50} {'Methods':<20} {'Endpoint'}")
print("-" * 70)

auth_routes = []
all_routes = []

with app.app_context():
    for rule in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        route_info = f"{rule.rule:<50} {methods:<20} {rule.endpoint}"
        all_routes.append(route_info)
        
        if 'auth' in rule.rule.lower():
            auth_routes.append(route_info)
            print(f"🔐 {route_info}")
        else:
            print(f"   {route_info}")

print("-" * 70)
print()

# Summary
print("Summary:")
print(f"  Total routes: {len(all_routes)}")
print(f"  Auth routes: {len(auth_routes)}")
print()

# List auth routes specifically
if auth_routes:
    print("Authentication Endpoints:")
    print("-" * 70)
    for route in auth_routes:
        print(f"  {route}")
    print()
else:
    print("⚠️  WARNING: No auth routes found!")
    print("   Check if auth_bp is registered in app/__init__.py")
    print()

# Test health check
print("Testing Health Check Endpoint:")
print("-" * 70)
try:
    with app.test_client() as client:
        response = client.get('/healthcheck')
        if response.status_code == 200:
            print("✅ Health check: OK")
        else:
            print(f"❌ Health check failed: {response.status_code}")
except Exception as e:
    print(f"❌ Health check error: {str(e)}")

print()
print("=" * 70)
print("If you see auth routes above, your app is configured correctly!")
print("If not, check for import errors or missing blueprint registration.")
print("=" * 70)


