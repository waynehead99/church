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

# Set up Python virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    cd "$APP_DIR"
    python3 -m venv venv
    chown -R church_app:church_app venv
    runuser -u church_app -- bash -c "source venv/bin/activate && pip install -r requirements.txt"
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

# Initialize database
init_database() {
    print_status "Initializing database..."
    runuser -u church_app -- bash -c "cd $APP_DIR && source venv/bin/activate && flask db upgrade"
    
    # Run configuration script
    if [ -f "$APP_DIR/configure.sh" ]; then
        chmod +x "$APP_DIR/configure.sh"
        "$APP_DIR/configure.sh"
    fi
}

# Main installation process
main() {
    print_status "Starting installation of Church Management System..."
    
    install_dependencies
    setup_user
    setup_venv
    setup_nginx
    setup_service
    init_database
    
    print_status "Installation completed successfully!"
    print_status "Please visit http://localhost to access the application"
    print_warning "Don't forget to:"
    print_warning "1. Configure SSL certificates if needed"
    print_warning "2. Update the .env file with your settings"
    print_warning "3. Create an admin user using: runuser -u church_app -- /opt/church/venv/bin/python /opt/church/create_admin.py"
}

# Run main installation
main
