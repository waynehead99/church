# Church Management System

A comprehensive web-based church management system built with Flask that enables secure member registration, form submissions, and administrative oversight.

## Features

- **User Authentication & Authorization**
  - Secure user registration and login system
  - Role-based access control (Admin/Member)
  - Password hashing with Werkzeug
  - Session management via Flask-Login
  - Automatic session timeout

- **Form Management**
  - Intuitive member information forms
  - Secure data storage and encryption
  - File upload capabilities
  - Form validation and sanitization
  - Historical submission tracking

- **Administrative Features**
  - Comprehensive admin dashboard
  - Export data to CSV
  - User management interface
  - Form submission overview
  - Activity logging

- **Security Features**
  - CSRF protection
  - XSS prevention
  - SQL injection protection
  - Rate limiting
  - Secure password policies

- **Email Integration**
  - Automated welcome emails
  - Form submission confirmations
  - Password reset functionality
  - Admin notifications
  - Bulk email capabilities

## Technical Stack

- **Backend Framework**
  - Flask 2.3.3: Web framework
  - SQLAlchemy 2.0+: Database ORM
  - Flask-Login 0.6.2: User session management
  - Flask-WTF 1.1.1: Form handling and CSRF
  - Flask-Mail: Email functionality

- **Frontend Technologies**
  - Bootstrap 5: Responsive design
  - HTML5 & CSS3: Structure and styling
  - JavaScript: Interactive features
  - jQuery: DOM manipulation
  - AJAX: Asynchronous requests

- **Database**
  - SQLite: Local development and production deployment
  - SQLAlchemy Migrations: Schema management

## Project Structure

```
church/
├── app.py              # Main application file
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── church.db          # SQLite database
├── static/            # Static assets
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript files
│   └── img/          # Images
├── templates/         # HTML templates
│   ├── base.html     # Base template
│   ├── index.html    # Homepage
│   ├── auth/         # Authentication templates
│   │   ├── login.html
│   │   └── signup.html
│   ├── forms/        # Form templates
│   │   └── submit.html
│   └── admin/        # Admin templates
│       └── dashboard.html
└── migrations/       # Database migrations
```

## Installation

### Prerequisites
- Python 3.12 or higher
- pip (Python package installer)
- virtualenv

### Step 1: Clone the Repository
```bash
git clone [repository-url]
cd church
```

### Step 2: Set Up Virtual Environment
```bash
# Create a new virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- Flask==3.0.0
- Flask-SQLAlchemy==3.1.1
- Flask-Login==0.6.3
- Flask-Mail==0.9.1
- Werkzeug==3.0.1
- gunicorn==21.2.0
- python-dotenv==1.0.0
- SQLAlchemy==2.0.23

### Step 4: Environment Configuration
Create a `.env` file in the root directory with the following variables:
```
SECRET_KEY=your_secret_key_here
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_specific_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

### Step 5: Initialize the Database
```bash
# Create the database and tables
python3 init_db.py
```

### Step 6: Running the Application

#### Development Mode
```bash
# Run with Flask development server
flask run --debug
```

#### Production Mode with Gunicorn
```bash
# Make sure you're in the project directory and virtual environment is activated
gunicorn --bind 0.0.0.0:8000 app:app --log-level debug
```

### Common Issues and Solutions

1. **Login Issues**
   - Ensure the SECRET_KEY is set in your .env file
   - Verify the database exists and contains user records
   - Check app.log in the logs directory for detailed error messages

2. **Database Issues**
   - If tables are missing, run `python3 init_db.py`
   - Ensure write permissions for the church.db file
   - Check database connectivity with health check endpoint

3. **Email Configuration**
   - For Gmail, use App Specific Password
   - Verify all MAIL_* environment variables are set
   - Test email configuration with health check endpoint

4. **Permission Issues**
   - Ensure the logs directory exists and is writable
   - Check file permissions for church.db
   - Verify virtual environment permissions

### Health Check Endpoints

The following endpoints are available to verify system status:
- `/health` - Basic application health
- `/health/db` - Database connectivity
- `/health/email` - Email service status

### Logging

Logs are stored in the `logs/app.log` file. For debugging, check this file for detailed error messages and application status.

## Linux Installation

### Automated Installation

The easiest way to install the Church Management System is using our automated installation script. The script must be run as root:

1. **Download the latest release**
   ```bash
   git clone https://github.com/waynehead99/church.git
   cd church
   ```

2. **Run the installation script**
   ```bash
   sudo ./install.sh
   ```

   The install script will:
   - Install all required system dependencies
   - Set up Python virtual environment and install Python packages
   - Configure nginx with SSL for secure HTTPS access
   - Generate self-signed SSL certificates for development
   - Create necessary directories and set permissions
   - Initialize the database
   - Set up the application as a system service

3. **Access the Application**
   After installation:
   - The application will be available at `https://localhost` (note: using HTTPS)
   - For development with self-signed certificates, you may need to accept the security warning in your browser
   - For production, replace the self-signed certificates in `/etc/nginx/ssl/` with your own SSL certificates

4. **Troubleshooting**
   If you see the nginx welcome page instead of the application:
   - Check that nginx is running: `systemctl status nginx`
   - Verify the application service is running: `systemctl status church`
   - Check nginx error logs: `tail -f /var/log/nginx/error.log`
   - Ensure port 8000 is not in use: `netstat -tulpn | grep 8000`

### Manual Installation
{{ ... }}
