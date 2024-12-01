"""add rate limit table

Revision ID: add_rate_limit_table
Revises: 6b2cb4a2214e
Create Date: 2024-12-01 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_rate_limit_table'
down_revision = '6b2cb4a2214e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('rate_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('hits', sa.Integer(), nullable=True),
        sa.Column('reset_time', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rate_limits_key'), 'rate_limits', ['key'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_rate_limits_key'), table_name='rate_limits')
    op.drop_table('rate_limits')
