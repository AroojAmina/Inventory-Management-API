from flask import Blueprint, request, jsonify, abort
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, DataError, OperationalError, SQLAlchemyError
from app.core.models import Category
from app.schemas.category_schema import CategorySchema
from app.utils.db_utils import db
import logging

category_bp = Blueprint("category", __name__)
api = Api(category_bp)

category_schema = CategorySchema()
category_list_schema = CategorySchema(many=True)


def abort_json(status_code, message):
    response = jsonify(error=message)
    response.status_code = status_code
    abort(response)


class CategoryListAPI(Resource):
    
    def get(self):
        """Get list of categories with optional search and pagination"""
        try:
            page = int(request.args.get("page", 1))
            count = int(request.args.get("count", 10))
            name = request.args.get("name", "")

            query = Category.query.filter_by(is_trash=False)

            if name:
                query = query.filter(Category.name.ilike(f"%{name}%"))

            paginated = db.paginate(query.order_by(Category.id.desc()), page=page, per_page=count, error_out=False)

            return {
                "count": count,
                "total": paginated.total,
                "pages": paginated.pages,
                "page": paginated.page,
                "results": category_list_schema.dump(paginated.items),
            }, 200

        except Exception as e:
            logging.error(f"Error fetching categories: {e}")
            return {"error": "Internal server error"}, 500


    def post(self):
        try:
            data = request.get_json()
            category_data = category_schema.load(data)
            category = Category(**category_data)
            db.session.add(category)
            db.session.commit()
            return {"message": "Category created successfully"}, 201
        except ValidationError as ve:
            return {"error": ve.messages}, 400
        except IntegrityError:
            db.session.rollback()
            return {"error": "Category with this name already exists"}, 409
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500


class CategoryDetailAPI(Resource):
    
    def get(self, id):
        category = Category.query.get(id)
        if not category or category.is_trash:
            return {"message": "Category not found"}, 404
        return category_schema.dump(category), 200

   
    def put(self, id):
        category = Category.query.get(id)
        if not category or category.is_trash:
            return {"message": "Category not found"}, 404
        try:
            data = request.get_json()
            updated_data = category_schema.load(data, partial=True)
            for key, value in updated_data.items():
                setattr(category, key, value)
            db.session.commit()
            return {"message": "Category updated successfully"}, 200
        except ValidationError as ve:
            return {"error": ve.messages}, 400
        except IntegrityError:
            db.session.rollback()
            return {"error": "Category with this name already exists"}, 409
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    
    def delete(self, id):
        category = Category.query.get(id)
        if not category or category.is_trash:
            return {"message": "Category not found"}, 404
        try:
            category.is_trash = True  # Soft delete
            db.session.commit()
            return {"message": "Category deleted successfully"}, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500


# Register routes
api.add_resource(CategoryListAPI, "/categories/")
api.add_resource(CategoryDetailAPI, "/categories/<int:id>/")
