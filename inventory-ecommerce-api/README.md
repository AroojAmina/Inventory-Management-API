# Inventory E-commerce API

A RESTful API for managing inventory, carts, transactions, and customers for an e-commerce platform. Built with Flask, SQLAlchemy, and Alembic.

## Features

- Product, Category, and Stock management
- Cart and Cart Item management
- Customer and Transaction tracking
- Product Returns and Stock Movements
- Soft delete support (`is_trash` flag)
- Database migrations with Alembic

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/inventory-ecommerce-api.git
cd inventory-ecommerce-api
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory and add your configuration (example):



### 5. Initialize the database

```bash
flask db upgrade
```

### 6. Run the application

```bash
python run.py
```

## API Endpoints

- `/api/products` - Manage products
- `/api/categories` - Manage categories
- `/api/carts` - Manage carts and cart items
- `/api/customers` - Manage customers
- `/api/transactions` - Manage transactions
- `/api/returns` - Manage product returns

*(See code for full details or add API documentation with Swagger/Postman)*

## Migrations

To create a new migration after changing models:

```bash
flask db migrate -m "Your message"
flask db upgrade
```

## License

[MIT](LICENSE)