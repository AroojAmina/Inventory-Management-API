from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

def drop_db(app):
    with app.app_context():
        db.drop_all()

def migrate_db(app):
    migrate = Migrate(app, db)
    with app.app_context():
        migrate.init_app(app, db)
        # Apply migrations
        pass

def seed_db():
    # Placeholder for seeding the database with initial data
    pass