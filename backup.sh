#!/bin/bash

# Church Management System Backup Script
# This script creates backups of the database and uploaded files

# Load environment variables
source /opt/church/.env

# Set backup directory
BACKUP_DIR="/opt/church/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/opt/church/instance/church.db"
UPLOADS_DIR="/opt/church/uploads"

# Create backup filename
BACKUP_NAME="church_backup_${DATE}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Create temporary directory for this backup
mkdir -p "${BACKUP_PATH}"

# Backup database
if [ -f "$DB_FILE" ]; then
    echo "Backing up database..."
    cp "$DB_FILE" "${BACKUP_PATH}/church.db"
fi

# Backup uploads directory
if [ -d "$UPLOADS_DIR" ]; then
    echo "Backing up uploads..."
    cp -r "$UPLOADS_DIR" "${BACKUP_PATH}/uploads"
fi

# Create tarball
tar -czf "${BACKUP_PATH}.tar.gz" -C "$BACKUP_DIR" "${BACKUP_NAME}"

# Remove temporary directory
rm -rf "${BACKUP_PATH}"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "church_backup_*.tar.gz" -type f -mtime +7 -delete

echo "Backup completed: ${BACKUP_PATH}.tar.gz"
