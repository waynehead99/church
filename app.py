"""
Church Management System
A Flask-based web application for managing church member information and form submissions.

Features:
- User authentication and authorization with role-based access
- Secure form submission and storage for member information
- Historical data retrieval and export capabilities
- Email notifications for important updates
- Administrative dashboard for data management

Dependencies:
- Flask: Web framework
- SQLAlchemy: Database ORM
- Flask-Login: User session management
- Flask-Mail: Email functionality

Author: Church Management Team
Version: 1.0.1
Last Updated: 2024
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, FormData
from routes.admin import admin_bp
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from functools import wraps
import io
import csv
from flask import Response
from flask_mail import Mail, Message
import logging
import sys
from flask_migrate import Migrate
from utils.password_validation import validate_password, calculate_password_strength

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
log_file = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.urandom(24)  # Generate a random secret key for session security
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///church.db'  # SQLite database configuration

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Production configuration
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

# Initialize Sentry for error tracking
if os.getenv('FLASK_ENV') == 'production':
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )

# Redis configuration
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# Initialize caching
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379')
})

# Initialize rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=os.getenv('REDIS_URL', 'redis://localhost:6379')
)

# Initialize extensions
db.init_app(app)
mail = Mail(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Specify the login view for unauthorized access

# Admin required decorator
def admin_required(f):
    """
    Decorator to restrict access to admin-only routes.
    Checks if the current user has admin privileges before allowing access.
    
    Args:
        f: The function to be decorated
        
    Returns:
        decorated_function: The wrapped function with admin check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login user loader callback.
    Loads user object from database based on user_id stored in session.
    
    Args:
        user_id: The ID of the user to load
        
    Returns:
        User object or None if not found
    """
    return User.query.get(int(user_id))

def send_registration_confirmation(form_data):
    """
    Send a confirmation email for a new registration.
    
    Args:
        form_data: FormData object containing the registration details
    """
    try:
        msg = Message(
            subject=f"Registration Confirmation - {form_data.event_name}",
            recipients=[current_user.email]
        )
        
        # Render the HTML template with the form data
        msg.html = render_template(
            'email/registration_confirmation.html',
            student_name=form_data.student_name,
            date_of_birth=form_data.date_of_birth,
            street=form_data.street,
            city=form_data.city,
            zip_code=form_data.zip_code,
            parent_guardian=form_data.parent_guardian,
            parent_cell_phone=form_data.parent_cell_phone,
            home_phone=form_data.home_phone,
            emergency_contact=form_data.emergency_contact,
            emergency_phone=form_data.emergency_phone,
            current_treatment=form_data.current_treatment,
            treatment_details=form_data.treatment_details,
            physical_restrictions=form_data.physical_restrictions,
            restriction_details=form_data.restriction_details,
            event_name=form_data.event_name,
            event_cost=form_data.event_cost,
            payment_status=form_data.payment_status
        )
        
        mail.send(msg)
        logger.info(f"Sent registration confirmation email for {form_data.student_name} to {current_user.email}")
    except Exception as e:
        logger.error(f"Failed to send registration confirmation email: {str(e)}")
        # Don't raise the exception - we don't want to break the registration process if email fails

# Routes
@app.route('/')
def index():
    """
    Homepage route that displays the landing page.
    Accessible to all users, both authenticated and anonymous.
    
    Returns:
        Rendered index.html template
    """
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route handling both GET (display form) and POST (process form) requests.
    Authenticates users and creates a session using Flask-Login.
    
    Returns:
        GET: Rendered login form
        POST: Redirects to dashboard on success, back to login on failure
    """
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            # Get the next page from the URL parameters, defaulting to dashboard
            next_page = request.args.get('next')
            # Ensure the next page is safe (relative URL)
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            return redirect(next_page)
        
        # Don't reveal whether user exists or password was wrong
        flash('Invalid email or password', 'error')
        logger.warning(f"Failed login attempt for email: {email}")
        
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Signup route for new user registration.
    Creates new user accounts with proper password hashing and validation.
    
    Returns:
        GET: Rendered signup form
        POST: Redirects to dashboard on success, back to signup on failure
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('signup'))
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('signup'))
        
        # Validate password
        is_valid, error_message = validate_password(password)
        if not is_valid:
            flash(error_message)
            return redirect(url_for('signup'))
        
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email
        try:
            logger.info(f"Attempting to send welcome email to {email}")
            msg = Message(
                'Welcome to Reclaim Student Ministry',
                recipients=[email]
            )
            msg.html = render_template(
                'email/welcome.html',
                user=user
            )
            mail.send(msg)
            logger.info(f"Successfully sent welcome email to {email}")
        except Exception as e:
            logger.error(f"Error sending welcome email to {email}: {str(e)}")
            logger.exception("Full traceback:")
            flash("Your account was created, but we couldn't send the welcome email. Please contact support if you don't receive it.")
        
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Protected dashboard route showing user's form submissions.
    Requires authentication through @login_required decorator.
    
    Returns:
        Rendered dashboard template with user's form submissions
    """
    forms = FormData.query.filter_by(user_id=current_user.id).order_by(FormData.date_submitted.desc()).all()
    return render_template('dashboard.html', forms=forms)

@app.route('/submit-form', methods=['GET', 'POST'])
@login_required
def submit_form():
    """
    Protected route for submitting new forms.
    Handles form submission, validation, and storage in the database.
    
    Returns:
        GET: Rendered form submission template
        POST: Redirects to dashboard on success with confirmation message
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    if request.method == 'POST':
        try:
            form_data = FormData(
                user_id=current_user.id,
                student_name=request.form.get('student_name'),
                date_of_birth=request.form.get('date_of_birth'),
                street=request.form.get('street'),
                city=request.form.get('city'),
                zip_code=request.form.get('zip_code'),
                parent_guardian=request.form.get('parent_guardian'),
                parent_cell_phone=request.form.get('parent_cell_phone'),
                home_phone=request.form.get('home_phone'),
                emergency_contact=request.form.get('emergency_contact'),
                emergency_phone=request.form.get('emergency_phone'),
                current_treatment=bool(request.form.get('current_treatment')),
                treatment_details=request.form.get('treatment_details'),
                physical_restrictions=bool(request.form.get('physical_restrictions')),
                restriction_details=request.form.get('restriction_details'),
                family_doctor=request.form.get('family_doctor'),
                doctor_phone=request.form.get('doctor_phone'),
                insurance_company=request.form.get('insurance_company'),
                policy_number=request.form.get('policy_number'),
                photo_release=bool(request.form.get('photo_release')),
                liability_signature=request.form.get('liability_signature'),
                photo_signature=request.form.get('photo_signature')
            )
            
            db.session.add(form_data)
            db.session.commit()
            
            # Send confirmation email
            send_registration_confirmation(form_data)
            
            flash('Form submitted successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting form: {str(e)}")
            flash('An error occurred while submitting the form. Please try again.', 'error')
            return redirect(url_for('submit_form'))
    
    return render_template('submit_form.html')

# Register blueprints
app.register_blueprint(admin_bp)

@app.route('/logout')
@login_required
def logout():
    """
    Logout route to end user session.
    Clears the user session and redirects to homepage.
    
    Returns:
        Redirect to homepage with logout confirmation
    """
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/password-strength', methods=['POST'])
def check_password_strength():
    password = request.json.get('password', '')
    strength = calculate_password_strength(password)
    return jsonify({'strength': strength})

@app.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    """
    Handle password reset requests.
    Sends a password reset link to the user's email if the account exists.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.generate_reset_token()
            reset_url = url_for('reset_password', token=token, _external=True)
            
            try:
                msg = Message(
                    'Password Reset Request',
                    recipients=[user.email]
                )
                msg.html = render_template(
                    'email/reset_password.html',
                    reset_url=reset_url
                )
                mail.send(msg)
                logger.info(f"Password reset email sent to {email}")
                flash('Check your email for instructions to reset your password')
            except Exception as e:
                logger.error(f"Error sending password reset email to {email}: {str(e)}")
                logger.exception("Full traceback:")
                flash('Error sending password reset email. Please try again later.')
        else:
            # Don't reveal if email exists or not for security
            flash('Check your email for instructions to reset your password')
            
        return redirect(url_for('login'))
    
    return render_template('reset_password_request.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Handle password reset confirmation.
    Validates the reset token and allows user to set a new password.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.is_reset_token_valid(token):
        flash('Invalid or expired reset link')
        return redirect(url_for('reset_password_request'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('reset_password', token=token))
            
        # Validate password
        is_valid, error_message = validate_password(password)
        if not is_valid:
            flash(error_message)
            return redirect(url_for('reset_password', token=token))
            
        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()
        
        flash('Your password has been reset')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html')

# Health check endpoints
@app.route('/health')
@cache.cached(timeout=60)
def health_check():
    """Basic application health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow()})

@app.route('/health/db')
@cache.cached(timeout=60)
def db_health():
    """Database connectivity health check."""
    try:
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'service': 'database'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'service': 'database', 'error': str(e)}), 500

@app.route('/health/redis')
@cache.cached(timeout=60)
def redis_health():
    """Redis connectivity health check."""
    try:
        redis_client.ping()
        return jsonify({'status': 'healthy', 'service': 'redis'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'service': 'redis', 'error': str(e)}), 500

@app.route('/health/email')
@cache.cached(timeout=60)
def email_health():
    """Email service health check."""
    try:
        with app.app_context():
            mail.connect()
        return jsonify({'status': 'healthy', 'service': 'email'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'service': 'email', 'error': str(e)}), 500

# Apply rate limiting to sensitive endpoints
@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login_post():
    """Rate-limited login endpoint."""
    return login()

@app.route('/signup', methods=['POST'])
@limiter.limit("3 per minute")
def signup_post():
    """Rate-limited signup endpoint."""
    return signup()

if __name__ == '__main__':
    with app.app_context():
        # Only create tables if they don't exist
        db.create_all()
    app.run(host='0.0.0.0', debug=True)
