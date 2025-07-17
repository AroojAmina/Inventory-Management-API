from flask import Blueprint, jsonify, request, abort
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError, DataError, OperationalError, SQLAlchemyError
from marshmallow.exceptions import ValidationError
import logging

from app.core.models import Cart, CartItem, Product, Transaction, TransactionItem
from app.schemas.cart_schema import CartSchema, CartItemSchema
from app.utils.db_utils import db

cart_bp = Blueprint("cart", __name__)
api = Api(cart_bp)

cart_schema = CartSchema()
cart_item_schema = CartItemSchema()
cart_item_list_schema = CartItemSchema(many=True)


def abort_json(status_code, message):
    response = jsonify(error=message)
    response.status_code = status_code
    abort(response)


class CartView(Resource):
    @jwt_required()
    def get(self, customer_id):
        try:
            cart = Cart.query.filter_by(customer_id=customer_id).first()
            if not cart:
                return {"message": "Cart not found"}, 404
            return cart_schema.dump(cart), 200
        except (SQLAlchemyError, Exception) as e:
            logging.error(f"Error fetching cart: {e}")
            abort_json(500, "Internal server error")

    @jwt_required()
    def post(self, customer_id):
        try:
            data = request.get_json()
            try:
                validated = cart_item_schema.load(data)
            except ValidationError as ve:
                return {"error": ve.messages}, 400

            product_id = validated["product_id"]
            quantity = validated.get("quantity", 1)

            cart = Cart.query.filter_by(customer_id=customer_id).first()
            if not cart:
                cart = Cart(customer_id=customer_id)
                db.session.add(cart)
                db.session.commit()

            cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
            if cart_item:
                cart_item.quantity += quantity
            else:
                cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
                db.session.add(cart_item)

            db.session.commit()
            return {"message": "Product added to cart"}, 201

        except (SQLAlchemyError, Exception) as e:
            db.session.rollback()
            logging.error(f"Error adding product to cart: {e}")
            abort_json(500, "Internal server error")

    @jwt_required()
    def delete(self, customer_id):
        try:
            data = request.get_json()
            product_id = data.get("product_id")

            cart = Cart.query.filter_by(customer_id=customer_id).first()
            if not customer_id:
                return {"message": "Cart not found"}, 404

            cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
            if cart_item:
                db.session.delete()
                db.session.commit()
                return {"message": "Product removed from cart"}, 200

            return {"message": "Product not found in cart"}, 404
        except (SQLAlchemyError, Exception) as e:
            db.session.rollback()
            logging.error(f"Error removing product from cart: {e}")
            abort_json(500, "Internal server error")



class CheckoutView(Resource):
    @jwt_required()
    def post(self, customer_id):
        try:
            
            cart = Cart.query.filter_by(customer_id=customer_id, is_trash=False).first()
            if not cart or not cart.items:
                return {"message": "Cart is empty or not found"}, 404

            total_amount = 0

            
            for item in cart.items:
                product = Product.query.get(item.product_id)
                if not product or not product.stock or product.stock.quantity < item.quantity:
                    return {"error": f"Insufficient stock for {product.name if product else 'Unknown'}"}, 400

          
            transaction = Transaction(
                cart_id=cart.id,
                customer_id=customer_id,
                total_amount=0,  
                status='pending'  
            )
            db.session.add(transaction)
            db.session.flush()  

            for item in cart.items:
                product = Product.query.get(item.product_id)
                
                
                transaction_item = TransactionItem(
                    transaction_id=transaction.id,
                    product_id=product.id,
                    quantity=item.quantity,
                    price_per_unit=product.price
                )
                db.session.add(transaction_item)

                # Update Stock
                product.stock.quantity -= item.quantity

                # Calculate total
                total_amount += product.price * item.quantity

            # Step 5: Update Transaction Total
            transaction.total_amount = total_amount

            
            cart.is_trash = True  

            db.session.commit()

            return {
                "message": "Checkout successful",
                "transaction_id": transaction.id,
                "total_amount": total_amount
            }, 201

        except (SQLAlchemyError, Exception) as e:
            db.session.rollback()
            logging.error(f"Checkout error: {e}")
            return {"error": "Internal server error"}, 500




# Register the resources
api.add_resource(CartView, "/cart/<int:customer_id>/")
api.add_resource(CheckoutView, "/cart/<int:customer_id>/checkout/")
