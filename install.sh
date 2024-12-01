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
            apt-get install -y python3 python3-pip python3-venv nginx sqlite3 curl redis-server
            systemctl start redis-server
            systemctl enable redis-server
            ;;
        "CentOS Linux" | "Red Hat Enterprise Linux")
            print_status "Installing dependencies for CentOS/RHEL..."
            yum update -y
            yum install -y python3 python3-pip nginx sqlite redis
            systemctl start redis
            systemctl enable redis
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
    mkdir -p "$APP_DIR/flask_session"
    
    # Set permissions
    chown -R church_app:church_app "$APP_DIR/uploads"
    chown -R church_app:church_app "$APP_DIR/backups"
    chown -R church_app:church_app "$APP_DIR/static"
    chown -R church_app:church_app "$APP_DIR/logs"
    chown -R church_app:church_app "$APP_DIR/flask_session"
    
    chmod 755 "$APP_DIR/uploads"
    chmod 755 "$APP_DIR/backups"
    chmod 755 "$APP_DIR/static"
    chmod 755 "$APP_DIR/logs"
    chmod 755 "$APP_DIR/flask_session"
}

# Set up environment variables
setup_env() {
    print_status "Setting up environment variables..."
    
    # Generate a random secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    
    cat > "$APP_DIR/.env" << EOL
SECRET_KEY=$SECRET_KEY
FLASK_APP=app.py
FLASK_ENV=production
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_specific_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
DATABASE_URL=sqlite:///church.db
REDIS_URL=redis://localhost:6379
EOL
    
    chown church_app:church_app "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
}

# Set up Python virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    cd "$APP_DIR"
    python3 -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Deactivate virtual environment
    deactivate
}

# Initialize the database
init_database() {
    print_status "Initializing database..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Remove existing database if it exists
    if [ -f "church.db" ]; then
        rm church.db
    fi
    
    # Initialize database
    python3 init_db.py
    
    if [ $? -eq 0 ]; then
        print_status "Database initialized successfully"
    else
        print_error "Failed to initialize database!"
        exit 1
    fi
    
    # Set proper permissions
    chown church_app:church_app church.db
    chmod 640 church.db
    
    # Deactivate virtual environment
    deactivate
}

# Configure Nginx
setup_nginx() {
    print_status "Configuring Nginx..."
    
    # Create SSL directory
    mkdir -p /etc/nginx/ssl
    
    # Generate self-signed SSL certificate for development
    print_status "Generating self-signed SSL certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/key.pem \
        -out /etc/nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    
    # Copy project nginx configuration
    print_status "Installing nginx configuration..."
    cp "$APP_DIR/nginx.conf" /etc/nginx/conf.d/church.conf
    
    # Create static directory if it doesn't exist
    mkdir -p "$APP_DIR/static"
    
    # Ensure proper permissions
    chown -R www-data:www-data /etc/nginx/ssl
    chmod 600 /etc/nginx/ssl/key.pem
    chmod 600 /etc/nginx/ssl/cert.pem
    
    # Remove default nginx site if it exists
    rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    nginx -t
    
    # Restart Nginx
    systemctl restart nginx
}

# Set up systemd service
setup_service() {
    print_status "Setting up systemd service..."
    
    # Create systemd service file
    cat > /etc/systemd/system/church.service << EOL
[Unit]
Description=Church Management System
After=network.target

[Service]
User=church_app
Group=church_app
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 app:app --log-level debug --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
EOL
    
    # Reload systemd and start service
    systemctl daemon-reload
    systemctl enable church
    systemctl start church
}

# Main installation process
main() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root"
        exit 1
    fi
    
    install_dependencies
    setup_user
    create_directories
    setup_env
    setup_venv
    init_database
    setup_nginx
    setup_service
    
    print_status "Installation completed successfully!"
    print_status "Please update the .env file with your email settings"
    print_status "Default admin credentials: admin@church.org / admin123"
}

# Run main installation
main
