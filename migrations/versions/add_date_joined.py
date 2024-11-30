"""add date joined column

Revision ID: add_date_joined
Revises: ed548fe47562
Create Date: 2024-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_date_joined'
down_revision = 'ed548fe47562'
branch_labels = None
depends_on = None


def upgrade():
    # Create a temporary table with the new schema
    op.execute('''
        CREATE TABLE user_new (
            id INTEGER PRIMARY KEY,
            email VARCHAR(120) NOT NULL UNIQUE,
            password_hash VARCHAR(128),
            is_admin BOOLEAN DEFAULT 0,
            reset_token VARCHAR(100) UNIQUE,
            reset_token_expiry DATETIME,
            date_joined DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Copy data from the old table to the new table
    op.execute('''
        INSERT INTO user_new (id, email, password_hash, is_admin, reset_token, reset_token_expiry)
        SELECT id, email, password_hash, is_admin, reset_token, reset_token_expiry
        FROM user
    ''')
    
    # Drop the old table
    op.execute('DROP TABLE user')
    
    # Rename the new table to the original name
    op.execute('ALTER TABLE user_new RENAME TO user')


def downgrade():
    # Create a temporary table without the date_joined column
    op.execute('''
        CREATE TABLE user_new (
            id INTEGER PRIMARY KEY,
            email VARCHAR(120) NOT NULL UNIQUE,
            password_hash VARCHAR(128),
            is_admin BOOLEAN DEFAULT 0,
            reset_token VARCHAR(100) UNIQUE,
            reset_token_expiry DATETIME
        )
    ''')
    
    # Copy data from the current table to the new table
    op.execute('''
        INSERT INTO user_new (id, email, password_hash, is_admin, reset_token, reset_token_expiry)
        SELECT id, email, password_hash, is_admin, reset_token, reset_token_expiry
        FROM user
    ''')
    
    # Drop the current table
    op.execute('DROP TABLE user')
    
    # Rename the new table to the original name
    op.execute('ALTER TABLE user_new RENAME TO user')
