from marshmallow import Schema, fields

class TransactionSchema(Schema):
    id = fields.Int(dump_only=True)
    cart_id = fields.Int()
    customer_id = fields.Int()
    total_amount = fields.Float()
    timestamp = fields.DateTime()
    status = fields.Str()

