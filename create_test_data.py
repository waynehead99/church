from app import app, db, User, FormData
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random
import names

def create_test_data():
    with app.app_context():
        # Create or get the user
        email = "wayne.erikson@hotmail.com"
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                is_admin=False
            )
            user.set_password("Test123!")
            db.session.add(user)
            db.session.commit()
            print(f"Created user: {email}")

        # List of possible values for random selection
        cities = ["Seattle", "Bellevue", "Redmond", "Kirkland", "Renton"]
        doctors = ["Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Brown", "Dr. Davis"]
        insurance_companies = ["Blue Cross", "Aetna", "UnitedHealth", "Cigna", "Kaiser"]
        events = ["Winter Camp 2024", "Summer Camp 2024", "Spring Retreat 2024", "Fall Festival 2024"]
        costs = ["$150", "$200", "$175", "$225"]
        streets = ["123 Main St", "456 Pine St", "789 Oak Ave", "321 Cedar Rd", "654 Maple Dr"]

        # Generate 20 random entries
        for i in range(20):
            # Generate random dates within a reasonable range
            dob_year = random.randint(2005, 2015)
            dob_month = random.randint(1, 12)
            dob_day = random.randint(1, 28)
            dob = f"{dob_year}-{dob_month:02d}-{dob_day:02d}"

            # Generate random phone numbers
            phone = f"206-{random.randint(100,999)}-{random.randint(1000,9999)}"

            # Create random form data
            form = FormData(
                user_id=user.id,
                student_name=names.get_full_name(),
                date_of_birth=dob,
                street=random.choice(streets),
                city=random.choice(cities),
                zip_code=f"981{random.randint(0,9):02d}",
                parent_guardian=f"{names.get_first_name()} {names.get_last_name()}",
                parent_cell_phone=phone,
                home_phone=f"206-{random.randint(100,999)}-{random.randint(1000,9999)}",
                emergency_contact=names.get_full_name(),
                emergency_phone=f"206-{random.randint(100,999)}-{random.randint(1000,9999)}",
                current_treatment=random.choice([True, False]),
                treatment_details=None if random.random() > 0.3 else "Some medical condition",
                physical_restrictions=random.choice([True, False]),
                family_doctor=random.choice(doctors),
                doctor_phone=f"206-{random.randint(100,999)}-{random.randint(1000,9999)}",
                insurance_company=random.choice(insurance_companies),
                policy_number=f"{random.choice(['BC', 'AE', 'UH', 'CI', 'KP'])}{random.randint(100000,999999)}",
                photo_release=random.choice([True, False]),
                event_name=random.choice(events),
                event_cost=random.choice(costs),
                payment_status=random.choice([True, False]),
                liability_signature=names.get_full_name(),
                photo_signature=names.get_full_name(),
                date_submitted=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.session.add(form)

        db.session.commit()
        print("Created 20 random test registrations")

if __name__ == "__main__":
    create_test_data()
