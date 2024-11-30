from app import app, db, User
from getpass import getpass

def create_admin():
    with app.app_context():
        print("Create Admin User")
        print("-----------------")
        
        email = input("Enter admin email: ")
        password = getpass("Enter admin password: ")
        confirm_password = getpass("Confirm password: ")
        
        if password != confirm_password:
            print("Error: Passwords don't match")
            return
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if existing_user.is_admin:
                print("Error: An admin with this email already exists")
                return
            # Make existing user an admin
            existing_user.is_admin = True
            existing_user.set_password(password)
            db.session.commit()
            print(f"Existing user {email} has been made an admin")
        else:
            # Create new admin user
            admin = User(email=email, is_admin=True)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user {email} has been created")

if __name__ == '__main__':
    create_admin()
