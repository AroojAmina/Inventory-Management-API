from flask import Blueprint, abort, jsonify
from flask_jwt_extended import jwt_required
from flask_restful import Api, Resource, reqparse, request
from sqlalchemy.exc import IntegrityError, DataError, OperationalError, SQLAlchemyError
from marshmallow import ValidationError
from sqlalchemy import text

from app.core.models import Stock, Transaction, StockMovement
from app.schemas.stock_schema import StockSchema
from app.utils.db_utils import db
from datetime import datetime, timedelta
import logging

stock_bp = Blueprint("stock", __name__)
api = Api(stock_bp)

stock_schema = StockSchema()

def make_error_response(status_code, message):
    return ({"error": message}), status_code


class StockListAPI(Resource):       
    
    def get(self):
        """Get list of stocks with optional search and pagination"""
        try:
            page = int(request.args.get("page", 1))
            count = int(request.args.get("count", 10))
            product_id = request.args.get("product_id", "")
            quantity = request.args.get("quantity", "")
            
            query = Stock.query

            if product_id:
                query = query.filter(Stock.product_id.ilike(f"%{product_id}%"))

            if quantity:
                query = query.filter(Stock.quantity.ilike(f"%{quantity}%"))

            paginated = db.paginate(query.order_by(Stock.id.desc()), page=page, per_page=count, error_out=False)

            return {
                "count": count,
                "total": paginated.total,
                "pages": paginated.pages,
                "page": paginated.page,
                "results": stock_schema.dump(paginated.items, many=True),
            }, 200

        except SQLAlchemyError as e:
            logging.error(f"Error fetching stocks: {e}")
            return make_error_response(500, "Internal server error")
        except (IntegrityError, DataError) as e:
            db.session.rollback()
            logging.error(f"Database error: {e}")
            return make_error_response(400, "Invalid stock data")
        except ValidationError as e:
            return make_error_response(400, str(e.messages))
        
    def post(self):
        try:
            data = request.get_json()
            if not data:
                return make_error_response(400, "Invalid input data")
            
            stock_data = stock_schema.load(data)
            
            stock = Stock(**stock_data)
            db.session.add(stock)
            db.session.commit()

            stock_movement = StockMovement(
                product_id=stock.product_id,
                quantity_change=stock.quantity,
                type='initial'
            )
            db.session.add(stock_movement)
            db.session.commit()
            
            return stock_schema.dump(stock), 201
            
        except ValidationError as e:
            return make_error_response(400, str(e.messages))
        except (IntegrityError, DataError) as e:
            db.session.rollback()
            logging.error(f"Database error creating stock: {e}")
            return make_error_response(400, "Invalid stock data")
        except (OperationalError, SQLAlchemyError) as e:
            db.session.rollback()
            logging.error(f"Database operation failed: {e}")
            return make_error_response(500, "Internal server error")
    
class StockView(Resource):
    
    def get(self, pk=None):
        try:
            if pk:
                stock = Stock.query.filter_by(product_id=pk).first()
                if not stock:
                    return make_error_response(404, "Stock not found")
                return stock_schema.dump(stock), 200
            else:
            
                return make_error_response(400, "Product ID is required")
                
        except SQLAlchemyError as e:
            logging.error(f"Error fetching stock: {e}")
            return make_error_response(500, "Internal server error")
    
    def put(self, pk):
        try:
            if not pk:
                return make_error_response(400, "Product ID is required")

            stock = Stock.query.filter_by(product_id=pk).first()
            if not stock:
                return make_error_response(404, "Stock not found")

            data = request.get_json()
            if not data:
                return make_error_response(400, "No update data provided")

            
            update_data = stock_schema.load(data, partial=True)
            
            old_quantity = stock.quantity
            
            for key, value in update_data.items():
                setattr(stock, key, value)
            
            new_quantity = stock.quantity
            quantity_change = new_quantity - old_quantity

            if quantity_change != 0:
                stock_movement = StockMovement(
                    product_id=stock.product_id,
                    quantity_change=quantity_change,
                    type='restock' if quantity_change > 0 else 'adjustment'
                )
                db.session.add(stock_movement)

            db.session.commit()
            return ("Stock updated successfully"), 200
            
        except ValidationError as e:
            return make_error_response(400, str(e.messages))
        except (IntegrityError, DataError) as e:
            db.session.rollback()
            logging.error(f"Database error updating stock: {e}")
            return make_error_response(400, "Invalid stock data")
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database operation failed: {e}")
            return make_error_response(500, "Internal server error")
        
    def delete(self, pk):
        try:
            if not pk:
                return make_error_response(400, "Product ID is required")

            stock = Stock.query.filter_by(product_id=pk).first()
            if not stock:
                return make_error_response(404, "Stock not found")

            db.session.delete(stock)
            db.session.commit()
            return ("Stock deleted successfully"), 200
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Error deleting stock: {e}")
            return make_error_response(500, "Internal server error")
        except IntegrityError as e:
            db.session.rollback()
            logging.error(f"Integrity error: {e}")
            return make_error_response(400, "Invalid stock data")
        except DataError as e:  
            db.session.rollback()
            logging.error(f"Data error: {e}")
            return make_error_response(400, "Invalid stock data")    

class LowStockView(Resource):
    def get(self):
        try:
            threshold = request.args.get('threshold', 12, type=int)
            low_stock_items = Stock.query.filter(Stock.quantity < threshold).all()
            return {
                "low_stock_items": stock_schema.dump(low_stock_items, many=True),
                "count": len(low_stock_items)
            }, 200
        except SQLAlchemyError as e:
            logging.error(f"Error fetching low stock items: {e}")
            return make_error_response(500, "Internal server error")

# List & Create (GET all, POST new)
api.add_resource(StockListAPI, "/stocks/")
# Single item GET, PUT, DELETE
api.add_resource(StockView, "/stocks/<string:pk>/")

# Low stock items
api.add_resource(LowStockView, "/stocks/low/")