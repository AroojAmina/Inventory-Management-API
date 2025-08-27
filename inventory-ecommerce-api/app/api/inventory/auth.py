from flask import Blueprint, request, jsonify
from app.core.models import User
from app.utils.db_utils import db
from app.schemas.user_schema import UserSchema
from marshmallow.exceptions import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)
user_schema = UserSchema()

@auth_bp.route("/signup", methods=["POST"])
def signup():
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
        db.session.add(user)
        db.session.commit()

        # return JWT token after signup
        access_token = create_access_token(identity=user.id)
        return {"message": "User created successfully", "access_token": access_token}, 201
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
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Bad email or password"}), 401
