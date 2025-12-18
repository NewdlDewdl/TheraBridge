"""Add timeline_events table for Feature 5

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-12-17 20:00:00.000000

This migration adds the timeline_events table for Feature 5 (Session Timeline):
- Stores events in a patient's therapy journey (sessions, milestones, notes, etc.)
- Supports flexible event types and subtypes
- Includes metadata for extensibility
- Optimized for patient timeline queries with proper indexing
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timeline_events table with defensive checks."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # ==========================================================================
    # Create timeline_events table
    # ==========================================================================

    if 'timeline_events' not in tables:
        op.create_table(
            'timeline_events',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('event_subtype', sa.String(length=50), nullable=True),
            sa.Column('event_date', sa.TIMESTAMP(timezone=True), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('metadata', postgresql.JSONB(), nullable=True),
            sa.Column('related_entity_type', sa.String(length=50), nullable=True),
            sa.Column('related_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('importance', sa.String(length=20), server_default='normal', nullable=False),
            sa.Column('is_private', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_timeline_events_patient_id',
            'timeline_events',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_timeline_events_therapist_id',
            'timeline_events',
            'users',
            ['therapist_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add check constraint for importance values
        op.create_check_constraint(
            'ck_timeline_events_importance',
            'timeline_events',
            "importance IN ('low', 'normal', 'high', 'critical')"
        )

        # Add check constraint for event_type values
        op.create_check_constraint(
            'ck_timeline_events_type',
            'timeline_events',
            "event_type IN ('session', 'milestone', 'note', 'diagnosis', 'treatment_plan', 'medication', 'assessment', 'external_event')"
        )

        # Add indexes for performance
        op.create_index(
            'idx_timeline_patient_date',
            'timeline_events',
            ['patient_id', sa.text('event_date DESC')]
        )
        op.create_index(
            'idx_timeline_type',
            'timeline_events',
            ['event_type']
        )


def downgrade() -> None:
    """Reverse the changes."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Drop timeline_events table if it exists
    if 'timeline_events' in tables:
        op.drop_index('idx_timeline_type', table_name='timeline_events')
        op.drop_index('idx_timeline_patient_date', table_name='timeline_events')
        op.drop_check_constraint('ck_timeline_events_type', 'timeline_events', type_='check')
        op.drop_check_constraint('ck_timeline_events_importance', 'timeline_events', type_='check')
        op.drop_constraint('fk_timeline_events_therapist_id', 'timeline_events', type_='foreignkey')
        op.drop_constraint('fk_timeline_events_patient_id', 'timeline_events', type_='foreignkey')
        op.drop_table('timeline_events')
