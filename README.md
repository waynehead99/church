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

## Setup Instructions

1. **Clone Repository**
   ```bash
   git clone https://github.com/waynehead99/church.git
   cd church
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings:
   # - SECRET_KEY
   # - MAIL_SERVER
   # - MAIL_USERNAME
   # - MAIL_PASSWORD
   ```

5. **Initialize Database**
   ```bash
   flask db upgrade
   ```

6. **Run Development Server**
   ```bash
   flask run
   ```

## Linux Installation

### Automated Installation

The easiest way to install the Church Management System is using our automated installation script. The script must be run as root:

1. **Download the latest release**
   ```bash
   git clone https://github.com/your-org/church.git
   cd church
   ```

2. **Make the installation script executable**
   ```bash
   chmod +x install.sh
   ```

3. **Run the installation script as root**
   ```bash
   ./install.sh
   ```

The installation script will:
- Install all required dependencies
- Create a dedicated user (church_app)
- Set up the Python virtual environment
- Configure Nginx as a reverse proxy
- Set up the systemd service
- Initialize the database
- Configure automatic backups

### Post-Installation Steps

1. **Update Environment Variables**
   ```bash
   nano /opt/church/.env
   ```
   Update the following settings:
   - Email configuration (SMTP settings)
   - Application settings
   - Backup configuration

2. **Create Admin User**
   ```bash
   runuser -u church_app -- /opt/church/venv/bin/python /opt/church/create_admin.py
   ```

3. **Check Service Status**
   ```bash
   systemctl status church
   systemctl status nginx
   ```

### Installation Location

- Application: `/opt/church`
- Virtual Environment: `/opt/church/venv`
- Database: `/opt/church/instance/church.db`
- Uploads: `/opt/church/uploads`
- Backups: `/opt/church/backups`
- Logs: `/var/log/church`

### Maintenance Commands

```bash
# Restart application
systemctl restart church

# View logs
journalctl -u church

# Manual backup
runuser -u church_app -- /opt/church/backup.sh

# Update application
cd /opt/church
runuser -u church_app -- git pull
runuser -u church_app -- /opt/church/venv/bin/pip install -r requirements.txt
systemctl restart church
```

### Uninstallation

To remove the Church Management System:

```bash
# Stop and disable services
systemctl stop church
systemctl disable church

# Remove files and user
rm -rf /opt/church
userdel -r church_app
rm /etc/nginx/sites-enabled/church
rm /etc/nginx/sites-available/church
rm /etc/systemd/system/church.service
rm /etc/cron.d/church-backup

# Restart Nginx
systemctl restart nginx
```

## Docker Deployment

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- SSL certificates for HTTPS (optional for development)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/church.git
   cd church
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **SSL Certificates (Optional)**
   ```bash
   # Create ssl directory
   mkdir ssl
   
   # For development, generate self-signed certificates
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout ssl/key.pem -out ssl/cert.pem
   
   # For production, place your real SSL certificates in the ssl directory:
   # - ssl/cert.pem
   # - ssl/key.pem
   ```

4. **Build and start containers**
   ```bash
   # Build images
   docker compose build

   # Start services
   docker compose up -d
   ```

5. **Initialize the database**
   ```bash
   # Create database tables
   docker compose exec web flask db upgrade

   # Create admin user
   docker compose exec web python create_admin.py
   ```

### Docker Commands

```bash
# View logs
docker compose logs -f

# Stop containers
docker compose down

# Rebuild and restart containers
docker compose up -d --build

# Execute commands in container
docker compose exec web flask db upgrade
docker compose exec web python create_admin.py

# Backup database
docker compose exec web sqlite3 instance/church.db ".backup '/app/instance/backup.db'"
```

### Container Structure

- **Web Container**
  - Python application running with Gunicorn
  - SQLite database in `/app/instance`
  - Application logs in stdout/stderr

- **Nginx Container**
  - Handles SSL termination
  - Serves static files
  - Proxies requests to web container

### Volumes

- `./instance:/app/instance`: Persists SQLite database
- `./ssl:/etc/nginx/ssl`: SSL certificates
- `./nginx.conf:/etc/nginx/conf.d/default.conf`: Nginx configuration

### Ports

- 80: HTTP (redirects to HTTPS)
- 443: HTTPS
- 8000: Gunicorn (internal)

### Production Considerations

1. **SSL Certificates**
   - Replace self-signed certificates with real ones
   - Consider using Let's Encrypt with Certbot

2. **Security**
   - Review and adjust Nginx security headers
   - Set strong passwords in .env
   - Keep Docker and dependencies updated

3. **Backups**
   - Implement regular database backups
   - Consider volume backups
   - Test restore procedures

4. **Monitoring**
   - Use Docker's built-in health checks
   - Monitor container logs
   - Set up container metrics monitoring

## Production Deployment

### Current Setup
This application uses SQLite as its database, which is suitable for smaller deployments with:
- Low to moderate traffic
- Single-server deployment
- Limited concurrent users
- Simple backup requirements

### Prerequisites
- Linux server with Python 3.7+
- SMTP server for emails
- SSL certificate for HTTPS

### Deployment Steps

1. **Server Setup**
   ```bash
   # Install system dependencies
   apt-get update
   apt-get install python3-pip python3-venv nginx

   # Create application user
   useradd -m -s /bin/bash church_app
   su - church_app
   ```

2. **Application Setup**
   ```bash
   # Clone and setup application
   git clone https://github.com/your-org/church.git
   cd church
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   # Setup environment variables
   cp .env.example .env
   # Edit .env with production values:
   # - Set SECRET_KEY
   # - Configure SMTP settings
   # - Enable production mode
   ```

4. **Database Setup**
   ```bash
   # Initialize database
   flask db upgrade
   python create_admin.py  # Create initial admin user
   
   # Set proper permissions for SQLite database
   chmod 640 church.db
   ```

5. **Gunicorn Setup**
   Create `/etc/systemd/system/church.service`:
   ```ini
   [Unit]
   Description=Church Management System
   After=network.target

   [Service]
   User=church_app
   WorkingDirectory=/home/church_app/church
   Environment="PATH=/home/church_app/church/venv/bin"
   ExecStart=/home/church_app/church/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

6. **Nginx Configuration**
   Create `/etc/nginx/sites-available/church`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl;
       server_name your-domain.com;

       ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

7. **Start Services**
   ```bash
   systemctl start church
   systemctl enable church
   systemctl restart nginx
   ```

### Monitoring and Maintenance

1. **Log Monitoring**
   - Application logs: `/home/church_app/church/app.log`
   - Nginx access logs: `/var/log/nginx/access.log`
   - System logs: `journalctl -u church`

2. **Backup Strategy**
   ```bash
   # Database backup (daily)
   sqlite3 church.db ".backup 'backup_$(date +%Y%m%d).db'"

   # Application backup
   tar -czf church_app_$(date +%Y%m%d).tar.gz /home/church_app/church
   ```

3. **Security Updates**
   ```bash
   # Update system packages
   apt update && apt upgrade

   # Update Python packages
   pip install --upgrade -r requirements.txt
   ```

4. **SSL Certificate Renewal**
   ```bash
   # Auto-renewal with Let's Encrypt
   certbot renew
   ```

### Scaling Considerations

If your application grows and needs to handle:
- Higher traffic volumes
- Multiple concurrent users
- Complex queries
- High availability requirements

Consider upgrading to:
1. PostgreSQL for better concurrency and scalability
2. Redis for session management and caching
3. Load balancing across multiple servers

Contact the development team for guidance on scaling the application.

## Usage Guide

1. **User Registration**
   - Navigate to /signup
   - Enter email and password
   - Verify email address
   - Complete profile information

2. **Submitting Forms**
   - Login to your account
   - Navigate to form submission
   - Fill required information
   - Upload necessary documents
   - Submit and receive confirmation

3. **Administrative Tasks**
   - Login as admin
   - Access admin dashboard
   - View all submissions
   - Export data as needed
   - Manage user accounts

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create pull request

See PROCESS.md for detailed development guidelines.

## Security

- All passwords are hashed
- Forms protected against CSRF
- Input sanitization
- Regular security audits
- Encrypted data storage

## Support

- GitHub Issues for bug reports
- Email support@church.org
- Documentation in /docs
- Regular maintenance updates
- Security patch notifications

## License

This project is licensed under the MIT License - see LICENSE file for details.
