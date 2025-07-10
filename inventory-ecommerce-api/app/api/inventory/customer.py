from flask import Blueprint, abort, jsonify
from flask_jwt_extended import jwt_required
from flask_restful import Api, Resource, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, DataError, OperationalError, SQLAlchemyError
from app.core.models import Customer
from app.schemas.customer_schema import CustomerSchema
from app.utils.db_utils import db
import logging
from math import ceil

customer_bp = Blueprint("customer", __name__)
api = Api(customer_bp)

def abort_json(status_code, message):
    response = jsonify(error=message)
    response.status_code = status_code
    abort(response)

customer_schema = CustomerSchema()
customer_list_schema = CustomerSchema(many=True)

class CustomerListAPI(Resource):
    def get(self):
        """Get list of customers with pagination"""
        try:
            page = int(request.args.get("page", 1))
            count = int(request.args.get("count", 10))
            name = request.args.get("name", "")

            query = Customer.query

            if name:
                query = query.filter(Customer.name.ilike(f"%{name}%"))

            paginated = db.paginate(
                query.order_by(Customer.id.desc()),
                page=page,
                per_page=count,
                error_out=False
            )

            return {
                "count": count,
                "total": paginated.total,
                "pages": paginated.pages,
                "page": paginated.page,
                "results": customer_list_schema.dump(paginated.items),
            }, 200

        except (IntegrityError, DataError, OperationalError, SQLAlchemyError) as e:
            logging.error(f"Error fetching customers: {e}")
            return {"error": "Internal server error while fetching customers"}, 500

    def post(self):
        try:
            data = request.get_json()
            customer_data = customer_schema.load(data)
            customer = Customer(**customer_data)
            db.session.add(customer)
            db.session.commit()
            # return customer_schema.dump(customer), 201
            return {"message": "Customer created successfully"}, 201
        except ValidationError as ve:
            return {"error": ve.messages}, 400
        except IntegrityError as ie:
            db.session.rollback()
            return {"error": "Email already exists"}, 409
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500
            

class CustomerDetailAPI(Resource):
    def get(self, id):
        customer = Customer.query.get(id)
        if not customer:
            return {"message": "Customer not found"}, 404
        return customer_schema.dump(customer), 200

    def put(self, id):
        customer = Customer.query.get(id)
        if not customer:
            return {"message": "Customer not found"}, 404
        try:
            data = request.get_json()
            updated_data = customer_schema.load(data, partial=True)
            for key, value in updated_data.items():
                setattr(customer, key, value)
            db.session.commit()
            return {"message": "Customer updated successfully"}, 200
        except ValidationError as ve:
            return {"error": ve.messages}, 400
        except IntegrityError as ie:
            db.session.rollback()
            return {"error": "Email already exists"}, 409
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def delete(self, id):
        customer = Customer.query.get(id)
        if not customer:
            return {"message": "Customer not found"}, 404
        db.session.delete(customer)
        db.session.commit()
        return {"message": "Customer deleted successfully"}, 200
    
    
api.add_resource(CustomerListAPI, "/customer/")
api.add_resource(CustomerDetailAPI, "/customers/<int:id>/")
