from marshmallow import Schema, fields

class StockSchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    last_updated = fields.DateTime(dump_only=True)
    category_id = fields.Int(required=True)