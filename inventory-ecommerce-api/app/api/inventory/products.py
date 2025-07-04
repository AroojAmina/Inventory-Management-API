from flask import Blueprint, abort, jsonify
from flask_jwt_extended import jwt_required
from flask_restful import Api, request, Resource
from sqlalchemy.exc import IntegrityError, DataError, OperationalError, SQLAlchemyError
from marshmallow.exceptions import ValidationError

from app.core.models import Product, Stock
from app.schemas.product_schema import ProductSchema
from app.utils.db_utils import db
from math import ceil
import logging

products_bp = Blueprint("products", __name__)
api = Api(products_bp)

product_schema = ProductSchema()
product_list_schema = ProductSchema(many=True)

def abort_json(status_code, message):
    response = jsonify(error=message)
    response.status_code = status_code
    abort(response)

class ProductListResource(Resource):
    # decorators = (jwt_required(),)

    def get(self):
        try:
            page = int(request.args.get("page", 1))
            count = int(request.args.get("count", 10))
            name = request.args.get("name", "")
            category_id = request.args.get("category_id", "")

            query = Product.query.filter_by(is_trash=False)
            if name:
                query = query.filter(Product.name.ilike(f"%{name}%"))
            if category_id:
                query = query.filter_by(category=category_id)

            total = query.count()
            pages = ceil(total / count)

            paginated = db.paginate(
                query.order_by(Product.id.desc()),
                page=page,
                per_page=count,
                error_out=False
            )

            # Include stock info in results
            results = []
            for product in paginated.items:
                prod_data = product_schema.dump(product)
                prod_data['quantity'] = product.stock.quantity if product.stock else 0
                results.append(prod_data)

            return {
                "count": count,
                "total": paginated.total,
                "pages": paginated.pages,
                "page": paginated.page,
                "results": results,
            }, 200

        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            logging.error(f"Error fetching products: {e}")
            return {"error": "Internal server error while fetching products"}, 500

    def post(self):
        """Create a new product with stock"""
        try:
            data = request.get_json()
            if not data:
                return {"error": "Invalid input data"}, 400

            try:
                product_data = product_schema.load(data)
            except ValidationError as ve:
                return {"error": ve.messages}, 400

            # Create new product instance
            product = Product(**product_data)
            db.session.add(product)
            db.session.flush()

            # Handle stock as part of product
            quantity = data.get('quantity', 0)
            stock = Stock(
                product_id=product.id,
                quantity=quantity,
                category_id=product.category_id
            )
            db.session.add(stock)
            db.session.commit()

            return {
                "message": "Product created successfully",
                "id": product.id,
                "quantity": stock.quantity
            }, 201

        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            db.session.rollback()
            logging.error(f"Error creating product: {e}")
            abort_json(500, str(e))

class ProductResource(Resource):
    # decorators = (jwt_required(),)

    def get(self, product_id):
        """Get single product by ID, including stock"""
        try:
            product = Product.query.filter_by(id=product_id, is_trash=False).first()
            if not product:
                return {"message": "Product not found"}, 404

            prod_data = product_schema.dump(product)
            prod_data['quantity'] = product.stock.quantity if product.stock else 0
            return prod_data, 200
        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            logging.error(f"Error fetching product: {e}")
            abort_json(500, str(e))

    def put(self, product_id):
        """Update a product and its stock"""
        try:
            data = request.get_json()
            product = Product.query.filter_by(id=product_id, is_trash=False).first()
            if not product:
                return {"message": "Invalid Product ID"}, 404

            try:
                product_data = product_schema.load(data, partial=True)
            except ValidationError as ve:
                return {"error": ve.messages}, 400

            # Update product attributes
            for key, value in product_data.items():
                setattr(product, key, value)

            # Update stock if quantity is provided
            if 'quantity' in data:
                if product.stock:
                    product.stock.quantity = data['quantity']
                else:
                    stock = Stock(
                        product_id=product.id,
                        quantity=data['quantity'],
                        category_id=product.category_id
                    )
                    db.session.add(stock)

            db.session.commit()
            return {"message": "Product Updated Successfully"}, 200

        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            db.session.rollback()
            logging.error(f"Error updating product: {e}")
            abort_json(500, str(e))

    def delete(self, product_id):
        try:
            product = Product.query.filter_by(id=product_id).first()
            if not product:
                return {"message": "Invalid Product ID"}, 404

            product.is_trash = True
            db.session.commit()
            return {"message": "Product Deleted Successfully"}, 200

        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            db.session.rollback()
            logging.error(f"Error deleting product: {e}")
            abort_json(500, str(e))

# Register resources with routes
api.add_resource(ProductListResource, "/products/")
api.add_resource(ProductResource, "/products/<int:product_id>/")
