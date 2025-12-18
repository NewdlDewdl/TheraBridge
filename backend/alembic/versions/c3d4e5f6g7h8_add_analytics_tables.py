"""Add analytics tables for Feature 2

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-12-17 18:00:00.000000

This migration adds the analytics tables for Feature 2:
1. session_metrics - Per-session analytics metrics
2. daily_stats - Aggregated daily statistics per therapist
3. patient_progress - Patient progress tracking snapshots
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add analytics tables with defensive checks."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # ==========================================================================
    # STEP 1: Create session_metrics table
    # ==========================================================================

    if 'session_metrics' not in tables:
        op.create_table(
            'session_metrics',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('session_date', sa.DateTime(), nullable=False),
            sa.Column('duration_minutes', sa.Integer(), nullable=True),
            sa.Column('mood_pre', sa.Integer(), nullable=True),
            sa.Column('mood_post', sa.Integer(), nullable=True),
            sa.Column('mood_change', sa.Integer(), nullable=True),
            sa.Column('engagement_score', sa.Float(), nullable=True),
            sa.Column('speaking_time_therapist_seconds', sa.Integer(), nullable=True),
            sa.Column('speaking_time_patient_seconds', sa.Integer(), nullable=True),
            sa.Column('word_count_therapist', sa.Integer(), nullable=True),
            sa.Column('word_count_patient', sa.Integer(), nullable=True),
            sa.Column('key_topics', postgresql.JSONB(), nullable=True),
            sa.Column('interventions_used', postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column('homework_assigned', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_session_metrics_session_id',
            'session_metrics',
            'therapy_sessions',
            ['session_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_session_metrics_therapist_id',
            'session_metrics',
            'users',
            ['therapist_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_session_metrics_patient_id',
            'session_metrics',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add check constraints for mood values
        op.create_check_constraint(
            'ck_session_metrics_mood_pre_range',
            'session_metrics',
            'mood_pre IS NULL OR (mood_pre >= 1 AND mood_pre <= 10)'
        )
        op.create_check_constraint(
            'ck_session_metrics_mood_post_range',
            'session_metrics',
            'mood_post IS NULL OR (mood_post >= 1 AND mood_post <= 10)'
        )

        # Add indexes for performance
        op.create_index(
            'idx_session_metrics_therapist_date',
            'session_metrics',
            ['therapist_id', sa.text('session_date DESC')]
        )
        op.create_index(
            'idx_session_metrics_patient',
            'session_metrics',
            ['patient_id']
        )

    # ==========================================================================
    # STEP 2: Create daily_stats table
    # ==========================================================================

    if 'daily_stats' not in tables:
        op.create_table(
            'daily_stats',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('stat_date', sa.Date(), nullable=False),
            sa.Column('total_sessions', sa.Integer(), server_default='0', nullable=False),
            sa.Column('unique_patients', sa.Integer(), server_default='0', nullable=False),
            sa.Column('total_duration_minutes', sa.Integer(), server_default='0', nullable=False),
            sa.Column('avg_mood_change', sa.Float(), nullable=True),
            sa.Column('avg_engagement_score', sa.Float(), nullable=True),
            sa.Column('patients_with_homework', sa.Integer(), server_default='0', nullable=False),
            sa.Column('top_topics', postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign key
        op.create_foreign_key(
            'fk_daily_stats_therapist_id',
            'daily_stats',
            'users',
            ['therapist_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add unique constraint (one row per therapist per day)
        op.create_unique_constraint(
            'uq_daily_stats_therapist_date',
            'daily_stats',
            ['therapist_id', 'stat_date']
        )

        # Add index for performance
        op.create_index(
            'idx_daily_stats_therapist_date',
            'daily_stats',
            ['therapist_id', sa.text('stat_date DESC')]
        )

    # ==========================================================================
    # STEP 3: Create patient_progress table
    # ==========================================================================

    if 'patient_progress' not in tables:
        op.create_table(
            'patient_progress',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('snapshot_date', sa.Date(), nullable=False),
            sa.Column('total_sessions', sa.Integer(), server_default='0', nullable=False),
            sa.Column('avg_mood_trend', sa.Float(), nullable=True),
            sa.Column('engagement_trend', sa.Float(), nullable=True),
            sa.Column('homework_completion_rate', sa.Float(), nullable=True),
            sa.Column('key_achievements', postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column('areas_for_focus', postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column('overall_progress_score', sa.Float(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign key
        op.create_foreign_key(
            'fk_patient_progress_patient_id',
            'patient_progress',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add unique constraint (one snapshot per patient per day)
        op.create_unique_constraint(
            'uq_patient_progress_patient_date',
            'patient_progress',
            ['patient_id', 'snapshot_date']
        )

        # Add index for performance
        op.create_index(
            'idx_patient_progress_patient_date',
            'patient_progress',
            ['patient_id', sa.text('snapshot_date DESC')]
        )


def downgrade() -> None:
    """Reverse the changes."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Drop patient_progress table if it exists
    if 'patient_progress' in tables:
        op.drop_index('idx_patient_progress_patient_date', table_name='patient_progress')
        op.drop_constraint('uq_patient_progress_patient_date', 'patient_progress', type_='unique')
        op.drop_constraint('fk_patient_progress_patient_id', 'patient_progress', type_='foreignkey')
        op.drop_table('patient_progress')

    # Drop daily_stats table if it exists
    if 'daily_stats' in tables:
        op.drop_index('idx_daily_stats_therapist_date', table_name='daily_stats')
        op.drop_constraint('uq_daily_stats_therapist_date', 'daily_stats', type_='unique')
        op.drop_constraint('fk_daily_stats_therapist_id', 'daily_stats', type_='foreignkey')
        op.drop_table('daily_stats')

    # Drop session_metrics table if it exists
    if 'session_metrics' in tables:
        op.drop_index('idx_session_metrics_patient', table_name='session_metrics')
        op.drop_index('idx_session_metrics_therapist_date', table_name='session_metrics')
        op.drop_check_constraint('ck_session_metrics_mood_post_range', 'session_metrics')
        op.drop_check_constraint('ck_session_metrics_mood_pre_range', 'session_metrics')
        op.drop_constraint('fk_session_metrics_patient_id', 'session_metrics', type_='foreignkey')
        op.drop_constraint('fk_session_metrics_therapist_id', 'session_metrics', type_='foreignkey')
        op.drop_constraint('fk_session_metrics_session_id', 'session_metrics', type_='foreignkey')
        op.drop_table('session_metrics')
