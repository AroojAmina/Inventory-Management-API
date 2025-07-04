from flask import Blueprint, abort, jsonify
from flask_jwt_extended import jwt_required
from flask_restful import Api, request, Resource
from sqlalchemy.exc import IntegrityError, DataError, OperationalError, SQLAlchemyError
from marshmallow.exceptions import ValidationError

from app.core.models import Product, Stock, StockMovement
from app.schemas.product_schema import ProductSchema
from app.utils.db_utils import db
from math import ceil
import logging

return_products_bp = Blueprint("return_products", __name__)
api = Api(return_products_bp)

product_schema = ProductSchema()

def abort_json(status_code, message):
    response = jsonify(error=message)
    response.status_code = status_code
    abort(response)

class return_ProductListResource(Resource):
    def post(self):
        data = request.get_json()
        product_id = data.get("product_id")
        quantity = data.get("quantity")

        # Validation
        if not product_id or not quantity:
            return {"error": "Product ID and quantity are required"}, 400

        # Check if product and stock exist
        product = Product.query.get(product_id)
        if not product:
            return {"error": "Product not found"}, 404

        stock = Stock.query.filter_by(product_id=product_id).first()
        if not stock:
            return {"error": "Stock not found for the product"}, 404

        # Update stock
        stock.quantity += quantity
        
        return_movement = StockMovement(
            product_id=product_id,
            quantity_change=quantity,
            type='return'
        )
        db.session.add(return_movement)
        
        db.session.commit()

        return {"message": "Product returned successfully"}, 200
    
    def get_list (self, *args, **kwargs):
        """Get list of products with pagination"""
        try:
            page = int(request.args.get("page", 1))
            count = int(request.args.get("count", 10))
            product_id = request.get("product_id")
            quantity = request.get("quantity")
            category_id = request.args.get("category_id", "")
            
            
            query = Product.query

            if product_id:
                query = query.filter(Product.name.like(f"%{product_id}%"))

            if category_id:
                query = query.filter_by(category=category_id)

            if quantity:
                query = query.filter_by(quantity=quantity)

            total = query.count()
            pages = ceil(total / count)

            paginated_query = query.order_by(Product.created_at.desc()).paginate(
                page, count, error_out=False
            )

            records = []
            for product in paginated_query.items:
                product_dict = product_schema.dump(product)
                product_dict["is_trash"] = bool(product.is_trash)
                records.append(product_dict)

            return {
                "total": total,
                "pages": pages,
                "current_page": page,
                "records": records,
            }, 200

        except (IntegrityError, DataError, OperationalError) as e:
            db.session.rollback()
            logging.error(f"Database error: {str(e)}")
            return {"error": "Database error"}, 500
        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy error: {str(e)}")
            return {"error": "SQLAlchemy error"}, 500
        except ValidationError as e:
            logging.error(f"Validation error: {str(e)}")
            return {"error": str(e)}, 400
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return {"error": "Unexpected error"}, 500
        
        
    def get(self, id):
        """Get a product by ID"""
        try:
            product = Product.query.get(id)
            if not product:
                return {"error": "Product not found"}, 404
            

            product_dict = product_schema.dump(product)
            return product_dict, 200

        except (IntegrityError, DataError, OperationalError) as e:
            db.session.rollback()
            logging.error(f"Database error: {str(e)}")
            return {"error": "Database error"}, 500
        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy error: {str(e)}")
            return {"error": "SQLAlchemy error"}, 500
        except ValidationError as e:
            logging.error(f"Validation error: {str(e)}")
            return {"error": str(e)}, 400
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return {"error": "Unexpected error"}, 500
        
        
    def put(self, id):
        """Update a product by ID"""
        try:
            data = request.get_json()
            if not data:
                return {"error": "Invalid input data"}, 400

            try:
                # Validate and deserialize input
                product_data = product_schema.load(data)
            except ValidationError as ve:
                return {"error": ve.messages}, 400

            # Update product instance
            product = Product.query.get(id)
            if not product:
                return {"error": "Product not found"}, 404

            for key, value in product_data.items():
                setattr(product, key, value)

            # Commit changes to the database
            db.session.commit()

            return {"message": "Product updated successfully"}, 200


        except (IntegrityError, DataError, OperationalError) as e:
            db.session.rollback()
            logging.error(f"Database error: {str(e)}")
            return {"error": "Database error"}, 500
        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy error: {str(e)}")
            return {"error": "SQLAlchemy error"}, 500
        except ValidationError as e:
            logging.error(f"Validation error: {str(e)}")
            return {"error": str(e)}, 400
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return {"error": "Unexpected error"}, 500  
        
    def delete(self, id):
        """Delete a product by ID"""
        try:
            product = Product.query.get(id)
            if not product:
                return {"error": "Product not found"}, 404

            db.session.delete()
            db.session.commit()

            return {"message": "Product deleted successfully"}, 200

        except (IntegrityError, DataError, OperationalError) as e:
            db.session.rollback()
            logging.error(f"Database error: {str(e)}")
            return {"error": "Database error"}, 500
        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy error: {str(e)}")
            return {"error": "SQLAlchemy error"}, 500
        except ValidationError as e:
            logging.error(f"Validation error: {str(e)}")
            return {"error": str(e)}, 400
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return {"error": "Unexpected error"}, 500       
    
    
    
api.add_resource(return_ProductListResource, "/product_return/")    
