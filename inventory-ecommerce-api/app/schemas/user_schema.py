from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=6))
    role = fields.Str(validate=validate.OneOf(["customer", "admin"]))
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True) 