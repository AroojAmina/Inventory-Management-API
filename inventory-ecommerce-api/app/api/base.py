from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from app.core.models import db, User, Customer
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
# filepath: c:\Users\Admin\Desktop\Arooj SS\flask restfull\app store\inventory-ecommerce-api\app\api\base.py
class ModelView:
    def list(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    phone = data.get('phone')

    if not email or not password or not name:
        return jsonify({'msg': 'Missing required fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'msg': 'Email already registered'}), 400

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    customer = Customer(user_id=user.id, name=name, email=email, phone=phone)
    db.session.add(customer)
    db.session.commit()

    return jsonify({'msg': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'msg': 'Missing email or password'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'msg': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    return jsonify({'id': user.id, 'email': user.email, 'role': user.role, 'is_active': user.is_active}), 200