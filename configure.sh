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

# Configuration variables
APP_DIR="/opt/church"
ENV_FILE="$APP_DIR/.env"

# Generate a random secret key
generate_secret_key() {
    python3 -c 'import secrets; print(secrets.token_hex(32))'
}

# Configure environment variables
setup_env() {
    print_status "Configuring environment variables..."
    
    if [ -f "$ENV_FILE" ]; then
        print_warning "Environment file already exists. Creating backup..."
        cp "$ENV_FILE" "$ENV_FILE.backup"
    fi

    # Generate new .env file
    cat > "$ENV_FILE" << EOL
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=$(generate_secret_key)

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=

# Security Configuration
SESSION_COOKIE_SECURE=True
REMEMBER_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
REMEMBER_COOKIE_HTTPONLY=True

# Rate Limiting
RATELIMIT_DEFAULT=200 per day

# Application Settings
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=/opt/church/uploads
ALLOWED_EXTENSIONS=pdf,doc,docx,jpg,jpeg,png

# Backup Configuration
BACKUP_DIRECTORY=/opt/church/backups
BACKUP_RETENTION_DAYS=30
EOL

    chown church_app:church_app "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    
    print_status "Environment file created at $ENV_FILE"
    print_warning "Please update the email configuration in $ENV_FILE"
}

# Create necessary directories
create_directories() {
    print_status "Creating application directories..."
    
    # Create directories
    mkdir -p "$APP_DIR/uploads"
    mkdir -p "$APP_DIR/backups"
    mkdir -p "$APP_DIR/instance"
    
    # Set permissions
    chown -R church_app:church_app "$APP_DIR/uploads"
    chown -R church_app:church_app "$APP_DIR/backups"
    chown -R church_app:church_app "$APP_DIR/instance"
    
    chmod 750 "$APP_DIR/uploads"
    chmod 750 "$APP_DIR/backups"
    chmod 750 "$APP_DIR/instance"
}

# Set up backup script
setup_backup() {
    print_status "Setting up backup script..."
    
    BACKUP_SCRIPT="$APP_DIR/backup.sh"
    cat > "$BACKUP_SCRIPT" << 'EOL'
#!/bin/bash

BACKUP_DIR="/opt/church/backups"
DB_FILE="/opt/church/instance/church.db"
RETENTION_DAYS=30

# Create backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/church_db_$TIMESTAMP.db"

# Create backup
sqlite3 "$DB_FILE" ".backup '$BACKUP_FILE'"

# Compress backup
gzip "$BACKUP_FILE"

# Remove old backups
find "$BACKUP_DIR" -name "church_db_*.db.gz" -type f -mtime +$RETENTION_DAYS -delete
EOL

    chmod +x "$BACKUP_SCRIPT"
    chown church_app:church_app "$BACKUP_SCRIPT"
    
    # Set up daily cron job for backup
    CRON_FILE="/etc/cron.d/church-backup"
    echo "0 2 * * * church_app $BACKUP_SCRIPT" > "$CRON_FILE"
    chmod 644 "$CRON_FILE"
}

# Main configuration process
main() {
    print_status "Starting configuration..."
    
    setup_env
    create_directories
    setup_backup
    
    print_status "Configuration completed successfully!"
    print_warning "Please review and update the .env file with your settings"
}

# Run main configuration
main
