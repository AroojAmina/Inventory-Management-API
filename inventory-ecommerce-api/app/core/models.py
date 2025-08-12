from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.db_utils import db
from werkzeug.security import generate_password_hash, check_password_hash


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(Integer, primary_key=True)
    cart_id = db.Column(Integer, ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    is_trash = db.Column(db.Boolean(), default=False) 


    product = db.relationship('Product', back_populates='cart_items')
    cart = db.relationship('Cart', back_populates='items')  


class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, ForeignKey('customers.id'), nullable=False)  
    is_trash = db.Column(db.Boolean(), default=False)  
    
    items = db.relationship('CartItem', back_populates='cart', lazy=True)
    customer = db.relationship('Customer', back_populates='carts')  
    transactions = db.relationship('Transaction', back_populates='cart')
    # cart = db.relationship('Cart', back_populates='items', lazy=True)


    def __repr__(self):
        return f'<Cart {self.id} for User {self.customer_id}>'
    


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    products = db.relationship('Product', backref='category', lazy=True)
    is_trash = db.Column(db.Boolean(), default=False)  
    
    
    stocks = db.relationship("Stock", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"    


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    is_trash = db.Column(db.Boolean(), default=False) 
    
    stock = db.relationship('Stock', back_populates='product', uselist=False)
    cart_items = db.relationship('CartItem', back_populates='product')
    transaction_items = db.relationship('TransactionItem', back_populates='product') 
    stock_movements = db.relationship('StockMovement', back_populates='product')

    def __repr__(self):
        return f'<Product {self.name}>'
    

class Stock(db.Model):
    __tablename__ = 'stocks'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_trash = db.Column(db.Boolean(), default=False) 


    product = db.relationship('Product', back_populates='stock')
    category = db.relationship('Category', back_populates='stocks')
    

    def __repr__(self):
        return f'<Stock {self.id} - Product ID: {self.product_id}, Quantity: {self.quantity}>'
    
class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_trash = db.Column(db.Boolean(), default=False)
    status = db.Column(db.String(50), nullable=False, default='pending')  
    

    cart = db.relationship('Cart', back_populates='transactions') 
    customer = db.relationship('Customer', back_populates='transactions') 

    def __repr__(self):
        return f'<Transaction {self.id} - Total: {self.total_amount}>'
    
class TransactionItem(db.Model):
    __tablename__ = 'transaction_items'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    is_trash = db.Column(db.Boolean(), default=False)  
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    transaction = db.relationship('Transaction', backref='items')
    product = db.relationship('Product')


class ReturnProduct(db.Model):
    __tablename__ = 'return_products'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_trash = db.Column(db.Boolean(), default=False) 

    product = db.relationship('Product', backref='returns')

    def __repr__(self):
        return f'<ReturnProduct {self.id} - Product ID: {self.product_id}, Quantity: {self.quantity}>'
    
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), default='customer')
    is_active = db.Column(db.Boolean(), default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('Customer', back_populates='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=True)
    is_trash = db.Column(db.Boolean(), default=False)
    
    user = db.relationship('User', back_populates='customer')
    carts = db.relationship('Cart', back_populates='customer')
    transactions = db.relationship('Transaction', back_populates='customer')

    def __repr__(self):
        return f'<Customer {self.name}>'

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_change = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., 'restock', 'sale', 'return'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_trash = db.Column(db.Boolean(), default=False)

    product = db.relationship('Product', back_populates='stock_movements')

    def __repr__(self):
        return f'<StockMovement {self.id} - Product ID: {self.product_id}, Change: {self.quantity_change}>'

class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Permission {self.name}>'