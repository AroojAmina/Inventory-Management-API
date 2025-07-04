# app/schemas/cart_schema.py
from marshmallow import Schema, fields

class CartItemSchema(Schema):
    id = fields.Int(required=False)
    cart_id = fields.Int(required=False)
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True)

class CartSchema(Schema):
    id = fields.Int(dump_only=True)
    customer_id = fields.Int(required=True)
    items = fields.Nested(CartItemSchema, many=True)
