from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
# filepath: c:\Users\Admin\Desktop\Arooj SS\flask restfull\app store\inventory-ecommerce-api\app\api\base.py
class ModelView:
    def list(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError