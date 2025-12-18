"""
SQLAlchemy ORM models for analytics and metrics tables
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Date, Numeric, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as SQLUUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class SessionMetrics(Base):
    """
    Pre-computed metrics for therapy sessions.
    Stores denormalized data for fast analytics queries.
    """
    __tablename__ = "session_metrics"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(SQLUUID(as_uuid=True), ForeignKey("therapy_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_date = Column(Date, nullable=False, index=True)
    duration_minutes = Column(Integer)
    mood_pre = Column(Integer, CheckConstraint('mood_pre >= 1 AND mood_pre <= 10'), nullable=True)
    mood_post = Column(Integer, CheckConstraint('mood_post >= 1 AND mood_post <= 10'), nullable=True)
    topics_discussed = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyStats(Base):
    """
    Daily aggregated statistics per therapist.
    Used for dashboard performance metrics and trend analysis.
    """
    __tablename__ = "daily_stats"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    stat_date = Column(Date, nullable=False, index=True)
    total_sessions = Column(Integer, default=0, nullable=False)
    total_patients_seen = Column(Integer, default=0, nullable=False)
    avg_session_duration = Column(Numeric(5, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('therapist_id', 'stat_date', name='uq_therapist_stat_date'),
    )


class PatientProgress(Base):
    """
    Periodic snapshots of patient progress metrics.
    Tracks goal completion and overall therapy progress over time.
    """
    __tablename__ = "patient_progress"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    goals_total = Column(Integer, default=0, nullable=False)
    goals_completed = Column(Integer, default=0, nullable=False)
    action_items_total = Column(Integer, default=0, nullable=False)
    action_items_completed = Column(Integer, default=0, nullable=False)
    overall_progress_score = Column(Numeric(3, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
