# Deployment Instructions

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

3. Edit the church.service file:
   - Update the `WorkingDirectory` path to your actual application directory
   - Update the `Environment` and `ExecStart` paths to your virtual environment location

4. Set up the systemd service:
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

5. Check service status:
```bash
sudo systemctl status church
```

## Important Notes

- The application will run on port 8000 by default (configured in gunicorn.conf.py)
- Make sure all environment variables are properly set in your .env file
- Logs will be written to access.log and error.log in your application directory

## Troubleshooting

If the service fails to start:
1. Check logs: `sudo journalctl -u church`
2. Verify permissions: Make sure your application directory is accessible
3. Check gunicorn.conf.py settings
4. Ensure all environment variables are set correctly
