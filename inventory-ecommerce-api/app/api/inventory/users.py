from flask import Blueprint, jsonify, request, abort
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow.exceptions import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

from app.core.models import User
from app.schemas.user_schema import UserSchema
from app.utils.db_utils import db
from app.core.permissions import check_permission


user_bp = Blueprint("user", __name__)
api = Api(user_bp)

user_schema = UserSchema()
user_list_schema = UserSchema(many=True)

def abort_json(status_code, message):
    response = jsonify(error=message)
    response.status_code = status_code
    abort(response)

class UserListAPI(Resource):
    @jwt_required()
    def get(self):
        if not check_permission('view_users'):
            return {"msg": "Access forbidden: insufficient permission"}, 403
        try:
            page = int(request.args.get("page", 1))
            count = int(request.args.get("count", 10))
            query = User.query.order_by(User.id.desc())
            paginated = query.paginate(page=page, per_page=count, error_out=False)
            return {
                "count": count,
                "total": paginated.total,
                "pages": paginated.pages,
                "page": paginated.page,
                "results": user_list_schema.dump(paginated.items),
            }, 200
        except SQLAlchemyError as e:
            logging.error(f"Error fetching users: {e}")
            return {"error": "Internal server error while fetching users"}, 500

    @jwt_required()
    def post(self):
        if not check_permission('edit_users'):
            return {"msg": "Access forbidden: insufficient permission"}, 403
        try:
            data = request.get_json()
            user_data = user_schema.load(data)
            if not isinstance(user_data, dict):
                return {"error": "Invalid user data"}, 400
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
            return {"message": "User created successfully"}, 201
        except ValidationError as ve:
            return {"error": ve.messages}, 400
        except IntegrityError:
            db.session.rollback()
            return {"error": "Email already exists"}, 409
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class UserDetailAPI(Resource):
    @jwt_required()
    def get(self, id):
        if not check_permission('view_users'):
            return {"msg": "Access forbidden: insufficient permission"}, 403
        user = User.query.get(id)
        if not user:
            return {"message": "User not found"}, 404
        return user_schema.dump(user), 200

    @jwt_required()
    def put(self, id):
        if not check_permission('edit_users'):
            return {"msg": "Access forbidden: insufficient permission"}, 403
        user = User.query.get(id)
        if not user:
            return {"message": "User not found"}, 404
        try:
            data = request.get_json()
            updated_data = user_schema.load(data, partial=True)
            if not isinstance(updated_data, dict):
                return {"error": "Invalid user data"}, 400
            if "password" in updated_data:
                user.set_password(updated_data["password"])
                updated_data.pop("password")
            for key, value in updated_data.items():
                setattr(user, key, value)
            db.session.commit()
            return {"message": "User updated successfully"}, 200
        except ValidationError as ve:
            return {"error": ve.messages}, 400
        except IntegrityError:
            db.session.rollback()
            return {"error": "Email already exists"}, 409
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    @jwt_required()
    def delete(self, id):
        if not check_permission('delete_users'):
            return {"msg": "Access forbidden: insufficient permission"}, 403
        user = User.query.get(id)
        if not user:
            return {"message": "User not found"}, 404
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted successfully"}, 200

class CurrentUserAPI(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {"message": "User not found"}, 404
        return user_schema.dump(user), 200

api.add_resource(UserListAPI, "/users/")
api.add_resource(UserDetailAPI, "/users/<int:id>/")
api.add_resource(CurrentUserAPI, "/users/me") 
