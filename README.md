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
   git clone https://github.com/your-org/church.git
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
   sudo apt-get update
   sudo apt-get install python3-pip python3-venv nginx

   # Create application user
   sudo useradd -m -s /bin/bash church_app
   sudo su - church_app
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
   sudo systemctl start church
   sudo systemctl enable church
   sudo systemctl restart nginx
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
   sudo apt update && sudo apt upgrade

   # Update Python packages
   pip install --upgrade -r requirements.txt
   ```

4. **SSL Certificate Renewal**
   ```bash
   # Auto-renewal with Let's Encrypt
   sudo certbot renew
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
