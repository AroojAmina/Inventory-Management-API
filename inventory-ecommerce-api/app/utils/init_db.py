  
import os
import logging
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .api.inventory.cart import cart_bp as cart
from app.api.inventory.category import category_bp as category 
from app.api.inventory.stock import stock_bp as stock_bp
from app.api.inventory.products import products_bp 
from app.api.inventory.customer import customer_bp
from app.api.inventory.sales import sales_bp
from app.api.inventory.return_products import return_products_bp
from app.utils.db_utils import db
from config import Config

migrate = Migrate()  # <-- This is important!

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize logging
    logging.basicConfig(level=logging.DEBUG if app.config['DEBUG'] else logging.INFO)

    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    migrate.init_app(app, db)  # <-- This is important!

    # Register blueprints
    app.register_blueprint(cart, url_prefix='/api/')
    app.register_blueprint(category, url_prefix='/api/category')
    app.register_blueprint(stock_bp, url_prefix='/api/stock/')
    app.register_blueprint(products_bp, url_prefix='/api/')
    app.register_blueprint(return_products_bp, url_prefix='/api/return_products/')
    app.register_blueprint(customer_bp, url_prefix='/api/')
    app.register_blueprint(sales_bp, url_prefix='/api/')
    
    # Health check endpoint
    @app.route('/healthcheck')
    def healthcheck():
        try:
            db.session.execute('SELECT 1')
            return 'OK', 200
        except Exception as e:
            return f'Database Error: {str(e)}', 500

    return app