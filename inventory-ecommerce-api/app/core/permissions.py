from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from app.core.models import User


ROLE_PERMISSIONS = {
    "admin": {"view_users", "edit_users", "delete_users", "view_inventory", "edit_inventory", "delete_inventory"},
    "manager": {"view_inventory", "edit_inventory"},
    "staff": {"view_inventory"},
    "customer": set()
}

def has_permission(permission):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user:
                return jsonify({"msg": "User not found"}), 404
            # Admin always has all permissions
            if user.role == "admin" or permission in ROLE_PERMISSIONS.get(user.role, set()):
                return fn(*args, **kwargs)
            return jsonify({"msg": "Access forbidden: insufficient permission"}), 403
        return wrapper
    return decorator

def check_permission(permission):
    from flask_jwt_extended import get_jwt_identity
    from app.core.models import User
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return False
    if user.role == "admin" or permission in ROLE_PERMISSIONS.get(user.role, set()):
        return True
    return False 