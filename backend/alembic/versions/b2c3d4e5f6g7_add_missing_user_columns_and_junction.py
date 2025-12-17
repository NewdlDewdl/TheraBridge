"""Add missing user columns and therapist_patients junction table

Revision ID: b2c3d4e5f6g7
Revises: 42ef48f739a4
Create Date: 2025-12-17 17:00:00.000000

This migration adds the final missing pieces for Feature 1:
1. Adds first_name, last_name, is_verified to users table
2. Creates therapist_patients junction table
3. Renames sessions table to therapy_sessions (if not already done)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = '42ef48f739a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns and junction table."""

    # ==========================================================================
    # STEP 1: Add missing columns to users table (if they don't exist)
    # ==========================================================================

    # Use batch mode to handle conditional column additions
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    user_columns = {col['name'] for col in inspector.get_columns('users')}

    # Add first_name if it doesn't exist
    if 'first_name' not in user_columns:
        op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True))

        # Populate from full_name (split on first space)
        op.execute("""
            UPDATE users
            SET first_name = SPLIT_PART(full_name, ' ', 1)
            WHERE first_name IS NULL
        """)

    # Add last_name if it doesn't exist
    if 'last_name' not in user_columns:
        op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True))

        # Populate from full_name (everything after first space)
        op.execute("""
            UPDATE users
            SET last_name = CASE
                WHEN POSITION(' ' IN full_name) > 0
                THEN SUBSTRING(full_name FROM POSITION(' ' IN full_name) + 1)
                ELSE ''
            END
            WHERE last_name IS NULL
        """)

    # Add is_verified if it doesn't exist
    if 'is_verified' not in user_columns:
        op.add_column('users', sa.Column(
            'is_verified',
            sa.Boolean(),
            server_default='false',
            nullable=False
        ))

    # ==========================================================================
    # STEP 2: Create therapist_patients junction table (if it doesn't exist)
    # ==========================================================================

    tables = inspector.get_table_names()

    if 'therapist_patients' not in tables:
        op.create_table(
            'therapist_patients',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('relationship_type', sa.String(50), server_default='primary', nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
            sa.Column('ended_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_therapist_patients_therapist_id',
            'therapist_patients',
            'users',
            ['therapist_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_therapist_patients_patient_id',
            'therapist_patients',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add unique constraint
        op.create_unique_constraint(
            'uq_therapist_patients_therapist_patient',
            'therapist_patients',
            ['therapist_id', 'patient_id']
        )

        # Add indexes
        op.create_index('ix_therapist_patients_therapist_id', 'therapist_patients', ['therapist_id'])
        op.create_index('ix_therapist_patients_patient_id', 'therapist_patients', ['patient_id'])

    # ==========================================================================
    # STEP 3: Create therapy_sessions table if sessions table is auth-related
    # ==========================================================================

    # Check if 'sessions' table has therapy columns or auth columns
    session_columns = {col['name'] for col in inspector.get_columns('sessions')}

    # If sessions table has 'patient_id', it's already therapy_sessions
    # If it has 'user_id' and 'refresh_token', it's auth_sessions
    if 'patient_id' in session_columns and 'therapy_sessions' not in tables:
        # Rename sessions to therapy_sessions
        op.rename_table('sessions', 'therapy_sessions')


def downgrade() -> None:
    """Reverse the changes."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Drop therapist_patients table if it exists
    if 'therapist_patients' in tables:
        op.drop_index('ix_therapist_patients_patient_id', table_name='therapist_patients')
        op.drop_index('ix_therapist_patients_therapist_id', table_name='therapist_patients')
        op.drop_constraint('uq_therapist_patients_therapist_patient', 'therapist_patients', type_='unique')
        op.drop_constraint('fk_therapist_patients_patient_id', 'therapist_patients', type_='foreignkey')
        op.drop_constraint('fk_therapist_patients_therapist_id', 'therapist_patients', type_='foreignkey')
        op.drop_table('therapist_patients')

    # Remove added columns from users
    user_columns = {col['name'] for col in inspector.get_columns('users')}

    if 'is_verified' in user_columns:
        op.drop_column('users', 'is_verified')
    if 'last_name' in user_columns:
        op.drop_column('users', 'last_name')
    if 'first_name' in user_columns:
        op.drop_column('users', 'first_name')

    # Rename therapy_sessions back to sessions if needed
    if 'therapy_sessions' in tables:
        op.rename_table('therapy_sessions', 'sessions')
