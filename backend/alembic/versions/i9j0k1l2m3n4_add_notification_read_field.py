"""add notification read field

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2025-12-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i9j0k1l2m3n4'
down_revision = 'h8i9j0k1l2m3'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add 'read' field to progress_milestones table for notification tracking.

    This enables the notification polling endpoint to track which milestone
    notifications have been viewed by users.
    """
    # Add read column to progress_milestones
    op.add_column(
        'progress_milestones',
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false')
    )

    # Remove server default after creation (only needed for existing rows)
    op.alter_column('progress_milestones', 'read', server_default=None)


def downgrade():
    """
    Remove 'read' field from progress_milestones table.
    """
    op.drop_column('progress_milestones', 'read')
