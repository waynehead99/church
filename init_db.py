from app import app, db
from models import User, FormData
from werkzeug.security import generate_password_hash

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
