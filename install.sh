#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[*]${NC} $1"
}

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    print_error "Cannot detect Linux distribution"
    exit 1
fi

print_status "Detected OS: $OS $VER"

# Install dependencies based on distribution
install_dependencies() {
    case $OS in
        "Ubuntu" | "Debian GNU/Linux")
            print_status "Installing dependencies for Ubuntu/Debian..."
            apt-get update
            apt-get install -y python3 python3-pip python3-venv nginx sqlite3 curl
            ;;
        "CentOS Linux" | "Red Hat Enterprise Linux")
            print_status "Installing dependencies for CentOS/RHEL..."
            yum update -y
            yum install -y python3 python3-pip nginx sqlite
            ;;
        *)
            print_error "Unsupported distribution: $OS"
            exit 1
            ;;
    esac
}

# Create application user and directory
setup_user() {
    print_status "Creating application user and directory..."
    if ! id -u church_app > /dev/null 2>&1; then
        useradd -m -s /bin/bash church_app
        print_status "Created user: church_app"
    else
        print_warning "User church_app already exists"
    fi

    # Set up application directory
    APP_DIR="/opt/church"
    if [ ! -d "$APP_DIR" ]; then
        mkdir -p "$APP_DIR"
        cp -r . "$APP_DIR"
        chown -R church_app:church_app "$APP_DIR"
        print_status "Created application directory: $APP_DIR"
    else
        print_warning "Application directory already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    # Create app directories
    mkdir -p "$APP_DIR/uploads"
    mkdir -p "$APP_DIR/backups"
    mkdir -p "$APP_DIR/static"
    mkdir -p "$APP_DIR/logs"
    
    # Set permissions
    chown -R church_app:church_app "$APP_DIR/uploads"
    chown -R church_app:church_app "$APP_DIR/backups"
    chown -R church_app:church_app "$APP_DIR/static"
    chown -R church_app:church_app "$APP_DIR/logs"
    
    chmod 755 "$APP_DIR/uploads"
    chmod 755 "$APP_DIR/backups"
    chmod 755 "$APP_DIR/static"
    chmod 755 "$APP_DIR/logs"
}

# Set up environment variables
setup_env() {
    print_status "Setting up environment variables..."
    
    # Generate a random secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    
    # Create .env file
    cat > "$APP_DIR/.env" << EOL
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=sqlite:///instance/church.db

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Backup Configuration
BACKUP_RETENTION_DAYS=7
BACKUP_TIME=02:00

# Application Configuration
UPLOAD_FOLDER=/opt/church/uploads
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg,doc,docx

# Security Configuration
SESSION_COOKIE_SECURE=True
REMEMBER_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
REMEMBER_COOKIE_HTTPONLY=True
EOL

    # Set proper permissions
    chown church_app:church_app "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    
    print_status "Environment file created at $APP_DIR/.env"
    print_warning "Please update the email configuration in .env with your email credentials"
}

# Set up Python virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    cd "$APP_DIR"
    
    print_status "Creating virtual environment in $APP_DIR/venv"
    python3 -m venv venv
    
    print_status "Setting ownership of venv directory"
    chown -R church_app:church_app venv
    
    print_status "Creating pip cache directory"
    mkdir -p /home/church_app/.cache/pip
    chown -R church_app:church_app /home/church_app/.cache
    
    print_status "Activating virtual environment"
    if [ ! -f "venv/bin/activate" ]; then
        print_error "Virtual environment activation script not found!"
        exit 1
    fi
    
    # Set HOME to church_app's home directory for pip cache
    export HOME="/home/church_app"
    source venv/bin/activate
    
    print_status "Python interpreter path: $(which python)"
    print_status "Pip path: $(which pip)"
    
    print_status "Upgrading pip..."
    python -m pip install --upgrade pip
    
    print_status "Installing dependencies..."
    python -m pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies!"
        exit 1
    fi
    
    print_status "Deactivating virtual environment"
    deactivate
    
    # Reset HOME
    unset HOME
    
    print_status "Setting final permissions"
    chown -R church_app:church_app "$APP_DIR/venv"
    
    print_status "Virtual environment setup completed"
}

# Initialize the database
init_database() {
    print_status "Initializing database..."
    cd "$APP_DIR"
    
    # Clean up existing migrations if they exist
    if [ -d "migrations" ]; then
        print_status "Removing existing migrations..."
        rm -rf migrations
    fi
    
    # Remove existing database if it exists
    if [ -f "instance/church.db" ]; then
        print_status "Removing existing database..."
        rm -f instance/church.db
    fi
    
    # Create instance directory if it doesn't exist
    mkdir -p instance
    chown -R church_app:church_app instance
    
    print_status "Running database migrations..."
    export FLASK_APP=app.py
    runuser -u church_app -- "$APP_DIR/venv/bin/flask" db init
    runuser -u church_app -- "$APP_DIR/venv/bin/flask" db migrate -m "Initial migration"
    runuser -u church_app -- "$APP_DIR/venv/bin/flask" db upgrade
    
    if [ $? -ne 0 ]; then
        print_error "Failed to initialize database!"
        exit 1
    fi
    
    # Set proper permissions
    chown -R church_app:church_app migrations
    chown -R church_app:church_app instance
    
    print_status "Database initialization completed"
}

# Set up backup script
setup_backup() {
    print_status "Setting up backup script..."
    
    # Copy backup script to app directory
    cp "$APP_DIR/backup.sh" "$APP_DIR/backup.sh"
    chmod +x "$APP_DIR/backup.sh"
    chown church_app:church_app "$APP_DIR/backup.sh"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$APP_DIR/backups"
    chown church_app:church_app "$APP_DIR/backups"
    
    # Set up daily cron job for backups at 2 AM
    CRON_JOB="0 2 * * * /opt/church/backup.sh >> /opt/church/logs/backup.log 2>&1"
    (crontab -u church_app -l 2>/dev/null || echo "") | grep -v "/opt/church/backup.sh" | { cat; echo "$CRON_JOB"; } | crontab -u church_app -
    
    print_status "Backup script and cron job configured"
}

# Configure Nginx
setup_nginx() {
    print_status "Configuring Nginx..."
    if [ -f /etc/nginx/sites-enabled/default ]; then
        rm /etc/nginx/sites-enabled/default
    fi
    
    cat > /etc/nginx/sites-available/church << 'EOL'
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/church/static/;
    }
}
EOL
    
    ln -sf /etc/nginx/sites-available/church /etc/nginx/sites-enabled/
    
    # Test Nginx configuration
    nginx -t
    if [ $? -eq 0 ]; then
        systemctl restart nginx
        print_status "Nginx configured successfully"
    else
        print_error "Nginx configuration test failed"
        exit 1
    fi
}

# Set up systemd service
setup_service() {
    print_status "Setting up systemd service..."
    cat > /etc/systemd/system/church.service << EOL
[Unit]
Description=Church Management System
After=network.target

[Service]
User=church_app
WorkingDirectory=/opt/church
Environment="PATH=/opt/church/venv/bin"
ExecStart=/opt/church/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL

    systemctl daemon-reload
    systemctl enable church
    systemctl start church
    print_status "Systemd service configured and started"
}

# Main installation process
main() {
    print_status "Starting installation of Church Management System..."
    
    install_dependencies
    setup_user
    create_directories
    setup_env
    setup_venv
    init_database
    setup_backup
    setup_nginx
    setup_service
    
    print_status "Installation completed successfully!"
    print_status "Important next steps:"
    print_status "1. Update email settings in /opt/church/.env"
    print_status "2. Create an admin user with: runuser -u church_app -- /opt/church/venv/bin/python /opt/church/create_admin.py"
    print_status "3. Visit http://your-domain to access the application"
}

# Run main installation
main
