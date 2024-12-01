from app import app, db
from models import User, FormData, Session
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Check if admin user exists
        admin_email = "admin@church.org"
        if not User.query.filter_by(email=admin_email).first():
            # Create admin user
            admin = User(
                email=admin_email,
                is_admin=True
            )
            admin.set_password("admin123")  # Remember to change this in production
            db.session.add(admin)
            db.session.commit()
            print("Created admin user")
        
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
