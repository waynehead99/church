from flask import Flask
from models import db, User
from werkzeug.security import generate_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///church.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def init_db():
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Check if admin user exists
        admin_email = "admin@example.com"
        if not User.query.filter_by(email=admin_email).first():
            # Create admin user
            admin = User(
                email=admin_email,
                is_admin=True
            )
            admin.set_password("Admin123!")  # Remember to change this in production
            db.session.add(admin)
            db.session.commit()
            print("Created admin user")
        
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
