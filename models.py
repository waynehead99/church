from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
    forms = db.relationship('FormData', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FormData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Student Information
    student_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.String(20))
    street = db.Column(db.String(200))
    city = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    
    # Contact Information
    parent_guardian = db.Column(db.String(100))
    parent_cell_phone = db.Column(db.String(20))
    home_phone = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    
    # Medical Information
    current_treatment = db.Column(db.Boolean, default=False)
    treatment_details = db.Column(db.Text)
    physical_restrictions = db.Column(db.Boolean, default=False)
    restriction_details = db.Column(db.Text)
    family_doctor = db.Column(db.String(100))
    doctor_phone = db.Column(db.String(20))
    insurance_company = db.Column(db.String(100))
    policy_number = db.Column(db.String(50))
    
    # Photo/Video Release
    photo_release = db.Column(db.Boolean, default=False)
    
    # Event Information
    event_name = db.Column(db.String(100), default="Winter Camp")
    event_cost = db.Column(db.String(20), default="$150")
    payment_status = db.Column(db.Boolean, default=False)
    
    # Signatures
    liability_signature = db.Column(db.Text)
    photo_signature = db.Column(db.Text)
    
    # Submission Information
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    form_type = db.Column(db.String(50), default='winter_camp')
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

class RateLimit(db.Model):
    __tablename__ = 'rate_limits'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), nullable=False, index=True)
    hits = db.Column(db.Integer, default=0)
    reset_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_rate_limit(cls, key):
        limit = cls.query.filter_by(key=key).first()
        now = datetime.utcnow()
        if limit and limit.reset_time <= now:
            limit.hits = 0
            limit.reset_time = now + timedelta(hours=1)
            db.session.commit()
        return limit
    
    @classmethod
    def increment(cls, key, reset_after=timedelta(hours=1)):
        now = datetime.utcnow()
        limit = cls.get_rate_limit(key)
        if not limit:
            limit = cls(key=key, hits=1, reset_time=now + reset_after)
            db.session.add(limit)
        else:
            limit.hits += 1
        db.session.commit()
        return limit.hits
