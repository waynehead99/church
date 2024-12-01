from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import User, db
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///church.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

# Initialize extensions
db.init_app(app)

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(email='admin@church.org').first()
        if not admin:
            # Create admin user
            admin = User(
                email='admin@church.org',
                is_admin=True
            )
            admin.set_password('admin123')  # Change this password in production!
            db.session.add(admin)
            db.session.commit()
            print("Created admin user")
        
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
