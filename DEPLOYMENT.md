# Deployment Instructions

## Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

## Setup Steps

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
# Create instance directory for SQLite database
mkdir -p instance

# Initialize database and run migrations
flask db upgrade
```

4. Edit the church.service file:
   - Update the `WorkingDirectory` path to your actual application directory
   - Update the `Environment` and `ExecStart` paths to your virtual environment location
   - Ensure the service user has write permissions to the instance directory

5. Set up the systemd service:
```bash
# Copy the service file
sudo cp church.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Start the service
sudo systemctl start church

# Enable service to start on boot
sudo systemctl enable church
```

6. Check service status:
```bash
sudo systemctl status church
```

## Environment Variables
Create a `.env` file in your application directory with these variables:
```bash
SECRET_KEY=your_secret_key_here
FLASK_APP=app.py
FLASK_ENV=production
```

## Database Management

### Backup Database
To backup the SQLite database:
```bash
# Stop the service first
sudo systemctl stop church

# Create backup
cp instance/church.db instance/church.db.backup

# Restart the service
sudo systemctl start church
```

### Database Migrations
If you need to update the database schema:
```bash
# Run migrations
flask db upgrade
```

## Troubleshooting

### Service Issues
If the service fails to start:
1. Check logs: `sudo journalctl -u church`
2. Verify permissions:
   ```bash
   # Ensure application directory is accessible
   sudo chown -R www-data:www-data /path/to/your/app
   sudo chmod -R 755 /path/to/your/app
   
   # Ensure database directory is writable
   sudo chown -R www-data:www-data /path/to/your/app/instance
   sudo chmod -R 750 /path/to/your/app/instance
   ```
3. Check gunicorn.conf.py settings
4. Ensure all environment variables are set correctly

### Database Issues
If you encounter database errors:
1. Check database file permissions
2. Verify SQLite file is not corrupted:
   ```bash
   sqlite3 instance/church.db "PRAGMA integrity_check;"
   ```
3. Restore from backup if needed:
   ```bash
   cp instance/church.db.backup instance/church.db
   ```

## Security Notes
- Keep your `.env` file secure and never commit it to version control
- Regularly backup your database
- Monitor the application logs for any suspicious activity
- Consider implementing regular database maintenance tasks
