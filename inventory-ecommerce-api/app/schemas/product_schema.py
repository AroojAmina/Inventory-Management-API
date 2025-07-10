from marshmallow import Schema, fields

class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    price = fields.Float(required=True)
    category_id = fields.Int(required=True)
    quantity = fields.Int(load_only=True) 
    
    # For creating stock with product