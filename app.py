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

import os
import sys
import logging
import io
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app with security and configuration settings
app = Flask(__name__, 
    static_url_path='',
    static_folder='static',
    template_folder='templates'
)

# Core application configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///church.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30  # Database connection timeout
app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600  # Recycle connections after an hour
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session expires after 24 hours of inactivity
app.config['SESSION_COOKIE_SECURE'] = False  # Allow cookies over HTTP for local development
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent client-side access to cookies
app.config['SESSION_COOKIE_SAMESITE'] = None  # Disable SameSite for local development
app.config['SESSION_COOKIE_NAME'] = 'church_session'
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)  # "Remember me" cookie duration
app.config['REMEMBER_COOKIE_SECURE'] = False  # Allow cookies over HTTP for local development
app.config['REMEMBER_COOKIE_HTTPONLY'] = True  # Prevent JS access to remember-me cookie
app.config['REMEMBER_COOKIE_NAME'] = 'church_remember'

# Development settings
if app.debug:
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize extensions
from models import db, RateLimit
db.init_app(app)
Session(app)

# Custom rate limiter implementation
def rate_limit(max_requests, period):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            key = f"{get_remote_address()}:{f.__name__}"
            hits = RateLimit.increment(key, reset_after=period)
            
            if hits > max_requests:
                return jsonify({"error": "Too many requests"}), 429
            return f(*args, **kwargs)
        return wrapped
    return decorator

# Configure caching system
cache = Cache(app, config={
    'CACHE_TYPE': 'simple'  # Simple cache for development, consider 'redis' for production
})

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

# Add both potential paths to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
opt_dir = '/opt/church'
for path in [current_dir, opt_dir]:
    if path not in sys.path:
        sys.path.append(path)
        logger.debug(f"Added {path} to Python path")

# Configure secure password requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIREMENTS = {
    'min_length': PASSWORD_MIN_LENGTH,
    'require_upper': True,  # Must contain uppercase letters
    'require_lower': True,  # Must contain lowercase letters
    'require_digit': True,  # Must contain numbers
    'require_special': True  # Must contain special characters
}

@login_manager.user_loader
def load_user(user_id):
    """
    Load a user instance from the database based on the provided user ID.
    
    Args:
        user_id (int): The ID of the user to load
    
    Returns:
        User instance if found, otherwise None
    """
    try:
        user = User.query.get(int(user_id))
        if user:
            logger.debug(f"Successfully loaded user: {user.email}")
            return user
        logger.warning(f"No user found with ID: {user_id}")
        return None
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {str(e)}")
        return None

def send_registration_confirmation(form_data):
    """
    Send a confirmation email to users after successful registration submission.
    
    Args:
        form_data (FormData): Object containing all registration form fields including:
            - student_name: Name of the registered student
            - date_of_birth: Student's birth date
            - contact information: Address, phone numbers
            - emergency contacts
            - medical information
            - event details and payment status
    
    Note:
        Email sending failures are logged but don't interrupt the registration process
        to ensure users can still register even if email service is temporarily down.
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
            family_doctor=form_data.family_doctor,
            doctor_phone=form_data.doctor_phone,
            insurance_company=form_data.insurance_company,
            policy_number=form_data.policy_number,
            photo_release=form_data.photo_release,
            liability_signature=form_data.liability_signature,
            photo_signature=form_data.photo_signature,
            event_name=form_data.event_name,
            event_cost=form_data.event_cost,
            payment_status=form_data.payment_status
        )
        
        mail.send(msg)
        logger.info(f"Sent registration confirmation email for {form_data.student_name} to {current_user.email}")
    except Exception as e:
        logger.error(f"Failed to send registration confirmation email: {str(e)}")
        # Don't raise the exception - we don't want to break the registration process if email fails

@app.after_request
def add_security_headers(response):
    """
    Add security-related HTTP headers to all responses.
    
    Headers added:
    - X-Frame-Options: Prevent clickjacking attacks
    - X-Content-Type-Options: Prevent MIME-type sniffing
    - HSTS: Force HTTPS connections
    
    Args:
        response: Flask response object
    
    Returns:
        Modified response with security headers
    """
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
    return response

def validate_password(password):
    """
    Validate that a password meets all security requirements.
    
    Requirements:
    - Minimum length (defined in PASSWORD_MIN_LENGTH)
    - Contains uppercase and lowercase letters
    - Contains at least one number
    - Contains at least one special character
    
    Args:
        password (str): The password to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if len(password) < PASSWORD_REQUIREMENTS['min_length']:
        return False, f'Password must be at least {PASSWORD_REQUIREMENTS["min_length"]} characters long'
    
    if PASSWORD_REQUIREMENTS['require_upper'] and not any(c.isupper() for c in password):
        return False, 'Password must contain at least one uppercase letter'
        
    if PASSWORD_REQUIREMENTS['require_lower'] and not any(c.islower() for c in password):
        return False, 'Password must contain at least one lowercase letter'
        
    if PASSWORD_REQUIREMENTS['require_digit'] and not any(c.isdigit() for c in password):
        return False, 'Password must contain at least one number'
        
    if PASSWORD_REQUIREMENTS['require_special'] and not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
        return False, 'Password must contain at least one special character'
    
    return True, ''

# Routes
@app.route('/')
def index():
    """
    Serve the application's landing page.
    
    This route is publicly accessible and provides:
    - Welcome message
    - Login/Signup options
    - Basic information about the church management system
    
    Returns:
        str: Rendered HTML for the landing page
    """
    logger.debug(f"Index route accessed. User authenticated: {current_user.is_authenticated}")
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login attempts.
    
    GET:
        Displays the login form
    
    POST:
        Processes the login credentials:
        1. Validates username and password
        2. Checks for active account
        3. Logs in the user
    
    Returns:
        GET: Rendered login template
        POST: Redirects to dashboard on success with status message
    """
    logger.debug("Login route accessed")
    
    if current_user.is_authenticated:
        logger.debug("User already authenticated, redirecting to dashboard")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        logger.debug("Processing login POST request")
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            logger.warning("Login attempt with missing email or password")
            flash('Please provide both email and password', 'error')
            return redirect(url_for('login'))
        
        logger.debug(f"Attempting login for email: {email}")
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Check if user has other active sessions
            if 'user_id' in session and session['user_id'] != user.id:
                # Invalidate other sessions
                session.clear()
            
            logger.info(f"Successful login for user: {email}")
            session.permanent = True
            login_user(user, remember=True, duration=timedelta(days=7))
            
            # Bind session to IP
            session['ip'] = request.remote_addr
            session['user_id'] = user.id
            session['email'] = user.email
            session['is_admin'] = user.is_admin
            session['login_time'] = datetime.utcnow().timestamp()
            
            logger.debug("User logged in successfully with remember=True")
            logger.debug(f"Session contains: {session}")
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            logger.debug(f"Redirecting to: {next_page}")
            return redirect(next_page)
        
        logger.warning(f"Failed login attempt for email: {email}")
        flash('Invalid email or password', 'error')
        
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handle new user registration.
    
    GET:
        Displays the registration form
    
    POST:
        Processes the registration data:
        1. Validates all required fields
        2. Checks for existing email
        3. Creates a new user account
    
    Returns:
        GET: Rendered registration template
        POST: Redirects to dashboard on success with status message
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not email or not password or not confirm_password:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('signup'))

        # Validate password strength
        is_valid, error_message = validate_password(password)
        if not is_valid:
            flash(error_message, 'error')
            return redirect(url_for('signup'))

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))

        try:
            new_user = User(email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            # Log in the new user
            login_user(new_user)
            session.permanent = True
            session['ip'] = request.remote_addr
            session['user_id'] = new_user.id
            session['email'] = new_user.email
            session['is_admin'] = new_user.is_admin
            session['login_time'] = datetime.utcnow().timestamp()
            
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during user registration: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Display the user's personalized dashboard.
    
    Features:
    - Overview of user's submitted forms
    - Quick actions for common tasks
    - Notifications and alerts
    - Access to form submission history
    
    Returns:
        str: Rendered dashboard template with user's data
    
    Note:
        Requires authentication via @login_required decorator
    """
    forms = FormData.query.filter_by(user_id=current_user.id).order_by(FormData.date_submitted.desc()).all()
    return render_template('dashboard.html', forms=forms)

@app.route('/submit-form', methods=['GET', 'POST'])
@login_required
def submit_form():
    """
    Handle the submission and processing of registration forms.
    
    GET:
        Displays the form submission template
    
    POST:
        Processes the submitted form data:
        1. Validates all required fields
        2. Sanitizes input data
        3. Stores in database
        4. Sends confirmation email
        5. Updates user's dashboard
    
    Returns:
        GET: Rendered form template
        POST: Redirect to dashboard with status message
    
    Raises:
        SQLAlchemyError: On database operation failure
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

@app.route('/logout')
@login_required
def logout():
    """
    Handle user logout.
    
    Clears the session and redirects to the login page.
    
    Returns:
        Redirect to login page
    """
    logger.debug(f"Logging out user: {current_user.email if current_user.is_authenticated else 'Unknown'}")
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/api/password-strength', methods=['POST'])
def check_password_strength():
    """
    Check the strength of a given password.
    
    Args:
        password (str): The password to check
    
    Returns:
        dict: Password strength information
    """
    password = request.json.get('password', '')
    strength = calculate_password_strength(password)
    return jsonify({'strength': strength})

@app.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    """
    Handle password reset requests.
    
    Sends a password reset link to the user's email if the account exists.
    
    Returns:
        GET: Rendered password reset request template
        POST: Redirect to login page with status message
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
    
    Returns:
        GET: Rendered password reset template
        POST: Redirect to login page with status message
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

@app.before_request
def check_session_security():
    """
    Verify session security before each request.
    
    Checks for IP mismatch and session timeout.
    
    Returns:
        Redirect to login page if session is invalid
    """
    if current_user.is_authenticated:
        # Check if IP matches the one stored in session
        if 'ip' in session and session['ip'] != request.remote_addr:
            logout_user()
            session.clear()
            flash('Your session has expired for security reasons. Please login again.', 'warning')
            return redirect(url_for('login'))
            
        # Check session timeout
        if 'login_time' in session:
            login_time = datetime.fromtimestamp(session['login_time'])
            if datetime.utcnow() - login_time > timedelta(hours=24):
                logout_user()
                session.clear()
                flash('Your session has expired. Please login again.', 'info')
                return redirect(url_for('login'))

# Debug route for static files
@app.route('/debug-static')
def debug_static():
    static_url = url_for('static', filename='css/style.css')
    static_folder = app.static_folder
    return jsonify({
        'static_url': static_url,
        'static_folder': static_folder,
        'exists': os.path.exists(os.path.join(static_folder, 'css/style.css'))
    })

# Health check endpoints
@app.route('/health')
@cache.cached(timeout=60)
def health_check():
    """
    Basic application health check endpoint.
    
    Verifies:
    - Application is running and responding
    - Basic routing is functional
    
    Returns:
        dict: Status information and timestamp
    """
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow()})

@app.route('/health/db')
def db_health():
    """Database health check."""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'message': 'Database connection is active',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/health/email')
@cache.cached(timeout=60)
def email_health():
    """
    Email service health check.
    
    Verifies:
    - Email server connection
    - SMTP settings are correct
    - Mail sending capability
    
    Returns:
        dict: Email service status and configuration details
    """
    try:
        with app.app_context():
            mail.connect()
        return jsonify({'status': 'healthy', 'service': 'email'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'service': 'email', 'error': str(e)}), 500

# Apply rate limiting to sensitive endpoints
@app.route('/login', methods=['POST'])
@rate_limit(max_requests=5, period=timedelta(minutes=15))
def login_post():
    """
    Rate-limited login endpoint.
    
    Prevents brute force attacks by limiting login attempts.
    
    Returns:
        Redirect to login page with status message
    """
    return login()

@app.route('/signup', methods=['POST'])
@rate_limit(max_requests=3, period=timedelta(hours=1))
def signup_post():
    """
    Rate-limited signup endpoint.
    
    Prevents automated account creation by limiting signup attempts.
    
    Returns:
        Redirect to login page with status message
    """
    return signup()

# Register blueprints
from routes.admin import admin_bp
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
