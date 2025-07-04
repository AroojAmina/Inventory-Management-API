from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError, DataError, OperationalError, SQLAlchemyError
from marshmallow.exceptions import ValidationError
from app.core.models import Product, Transaction, TransactionItem, Stock, Customer, StockMovement
from app.schemas.product_schema import ProductSchema
from app.utils.db_utils import db
from math import ceil
import logging
from datetime import datetime

sales_bp = Blueprint("sales", __name__)
api = Api(sales_bp)

product_schema = ProductSchema()

def abort_json(status_code, message):
    response = jsonify(error=message)
    response.status_code = status_code
    abort(response)

class SalesResource(Resource):
    def get(self):
        """Get list of sales transactions with pagination"""
        try:
            page = request.args.get('page', default=1, type=int)
            count = request.args.get('count', default=10, type=int)
            name = request.args.get('name', default=None, type=str)
            category_id = request.args.get('category_id', default=None, type=str)
            status = request.args.get('status', default=None, type=str)
            start_date_str = request.args.get('start_date', default=None, type=str)
            end_date_str = request.args.get('end_date', default=None, type=str)

            # Query for transactions
            query = Transaction.query

            if name:
                query = query.filter(Transaction.name.like(f"%{name}%"))

            if category_id:
                query = query.filter(Transaction.category == category_id)

            if status:
                query = query.filter(Transaction.status == status)

            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str)
                query = query.filter(Transaction.timestamp >= start_date)
            
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str)
                query = query.filter(Transaction.timestamp <= end_date)

            total = query.count()
            pages = ceil(total / count)

            # Paginate the results
            paginated_query = query.order_by(Transaction.created_at.desc()).paginate(
                page, count, error_out=False
            )

            records = []
            for transaction in paginated_query.items:
                # Fetch related transaction items and stock
                transaction_dict = {
                    **product_schema.dump(transaction),
                    "items": [product_schema.dump(item) for item in transaction.items],
                    "stock": [product_schema.dump(stock) for stock in transaction.stock],
                    "customer": product_schema.dump(transaction.customer)  # Add customer info
                }
                records.append(transaction_dict)

            return {
                "count": count,
                "total": total,
                "pages": pages,
                "page": paginated_query.page,
                "results": records,
            }, 200

        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            logging.error(f"Error fetching sales: {e}")
            abort_json(500, str(e))

    def post(self):
        """Create a new sale transaction"""
        try:
            data = request.get_json()
            if not data:
                return {"error": "Invalid input data"}, 400

            try:
                # Validate and deserialize input
                transaction_data = product_schema.load(data)
            except ValidationError as ve:
                return {"error": ve.messages}, 400

            # Check if customer exists, if not, create a new one
            customer_data = data.get('customer')
            if customer_data:
                customer = Customer.query.filter_by(email=customer_data['email']).first()
                if not customer:
                    # Create new customer if doesn't exist
                    customer = Customer(**customer_data)
                    db.session.add(customer)
                    db.session.commit()
            else:
                return {"error": "Customer data is required"}, 400

            # Create new transaction instance
            transaction = Transaction(
                customer_id=customer.id, **transaction_data
            )
            
            # Add to session and commit
            db.session.add(transaction)
            db.session.commit()
            
            return {"message": "Sale created successfully", "id": transaction.id}, 201
        
        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            db.session.rollback()
            logging.error(f"Error creating sale: {e}")
            abort_json(500, str(e))

class SalesDetailResource(Resource):
    def get(self, transaction_id):
        """Get a single sale transaction by ID"""
        try:
            transaction = Transaction.query.filter_by(id=transaction_id).first()
            if not transaction:
                return {"message": "Transaction not found"}, 404

            # Fetch related transaction items and stock
            transaction_dict = {
                **product_schema.dump(transaction),
                "items": [product_schema.dump(item) for item in transaction.items],
                "stock": [product_schema.dump(stock) for stock in transaction.stock],
                "customer": product_schema.dump(transaction.customer)  # Add customer info
            }
            return transaction_dict, 200

        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            logging.error(f"Error fetching transaction: {e}")
            abort_json(500, str(e))

    def put(self, transaction_id):
        """Update a sale transaction"""
        try:
            body = request.get_json()
            transaction = Transaction.query.filter_by(id=transaction_id).first()

            if not transaction:
                return {"message": "Invalid Transaction ID"}, 404

            try:
                # Validate input
                transaction_data = product_schema.load(body, partial=True)
            except ValidationError as ve:
                return {"error": ve.messages}, 400

            # Update transaction attributes
            for key, value in transaction_data.items():
                setattr(transaction, key, value)
                
            db.session.commit()
            return {"message": "Transaction Updated Successfully"}, 200
        
        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            db.session.rollback()
            logging.error(f"Error updating transaction: {e}")
            abort_json(500, str(e))

    def delete(self, transaction_id):
        """Delete a sale transaction"""
        try:
            transaction = Transaction.query.filter_by(id=transaction_id).first()

            if not transaction:
                return {"message": "Invalid Transaction ID"}, 404

            db.session.delete(transaction)
            db.session.commit()
            return {"message": "Transaction Deleted Successfully"}, 200
        
        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            db.session.rollback()
            logging.error(f"Error deleting transaction: {e}")
            abort_json(500, str(e))
            

class SalesCheckoutView(Resource):
    def post(self):
        """Handle the checkout of a sale transaction"""
        try:
            data = request.get_json()
            if not data:
                return {"error": "Invalid input data"}, 400

            # Assuming data contains transaction details, like items and quantities
            items = data.get("items")
            if not items:
                return {"error": "No items in the transaction"}, 400

            # Validate if stock is available for each item
            for item_data in items:
                product_id = item_data["product_id"]
                quantity = item_data["quantity"]

                # Check if product exists and if enough stock is available
                product = Product.query.filter_by(id=product_id).first()
                if not product:
                    return {"error": f"Product {product_id} not found"}, 404

                stock = Stock.query.filter_by(product_id=product_id).first()
                if stock and stock.quantity < quantity:
                    return {"error": f"Not enough stock for {product.name}"}, 400

            # If all items are valid, proceed with the sale
            customer_data = data.get('customer')
            customer = Customer.query.filter_by(email=customer_data['email']).first()
            if not customer:
                return {"error": "Customer not found"}, 404

            transaction = Transaction(status="Completed", customer_id=customer.id)
            db.session.add(transaction)
            db.session.commit()

            # Add items to the transaction
            for item_data in items:
                product_id = item_data["product_id"]
                quantity = item_data["quantity"]

                product = Product.query.get(product_id)
                transaction_item = TransactionItem(
                    transaction_id=transaction.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price
                )
                db.session.add(transaction_item)

                # Update stock quantity
                stock = Stock.query.filter_by(product_id=product_id).first()
                if stock:
                    stock.quantity -= quantity
                    
                    sale_movement = StockMovement(
                        product_id=product.id,
                        quantity_change=-quantity,
                        type='sale'
                    )
                    db.session.add(sale_movement)

            # Commit all changes to the database
            db.session.commit()

            # Return success response
            return {"message": "Checkout successful", "transaction_id": transaction.id}, 200

        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            db.session.rollback()
            logging.error(f"Error during checkout: {e}")
            abort_json(500, str(e))


api.add_resource(SalesCheckoutView, "/sales/checkout/")            
api.add_resource(SalesResource, "/sales/")
api.add_resource(SalesDetailResource, "/sales/<int:transaction_id>/")
