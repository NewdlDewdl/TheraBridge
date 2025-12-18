"""
Analytics endpoints for therapist dashboard insights
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.auth.dependencies import require_role
from app.models.db_models import User
from app.models.schemas import (
    AnalyticsOverviewResponse,
    PatientProgressResponse,
    SessionTrendsResponse,
    TopicsResponse
)
from app.services.analytics import (
    calculate_overview_analytics,
    calculate_patient_progress,
    calculate_session_trends,
    calculate_topic_frequencies
)
from app.middleware.rate_limit import limiter

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverviewResponse)
@limiter.limit("50/minute")
async def get_analytics_overview(
    request: Request,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get practice overview analytics for the current therapist.

    Returns comprehensive statistics about the therapist's practice including:
    - Total number of patients
    - Total number of therapy sessions
    - Number of sessions this month
    - Average session duration
    - Active patients count
    - Sessions by status breakdown

    Auth:
        Requires therapist role

    Rate Limit:
        50 requests per minute per IP address

    Args:
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        AnalyticsOverviewResponse: Practice overview statistics

    Raises:
        HTTPException 403: If user is not a therapist
        HTTPException 429: Rate limit exceeded
    """
    return await calculate_overview_analytics(current_user.id, db)


@router.get("/patients/{patient_id}/progress", response_model=PatientProgressResponse)
@limiter.limit("50/minute")
async def get_patient_progress(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get progress analytics for a specific patient.

    Returns detailed progress metrics for an individual patient including:
    - Total session count
    - Most recent session date
    - Session frequency (sessions per week/month)
    - Progress indicators (sentiment trends, topic evolution)
    - Treatment milestones

    Auth:
        Requires therapist role
        Validates patient belongs to current therapist

    Rate Limit:
        50 requests per minute per IP address

    Args:
        patient_id: UUID of the patient to retrieve progress for
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        PatientProgressResponse: Patient progress statistics and trends

    Raises:
        HTTPException 403: If user is not a therapist or patient doesn't belong to therapist
        HTTPException 404: If patient not found
        HTTPException 429: Rate limit exceeded
    """
    return await calculate_patient_progress(patient_id, current_user.id, db)


@router.get("/sessions/trends", response_model=SessionTrendsResponse)
@limiter.limit("50/minute")
async def get_session_trends(
    request: Request,
    period: str = Query(default="month", regex="^(week|month|quarter|year)$"),
    patient_id: Optional[UUID] = None,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get session trends over time for the therapist's practice.

    Analyzes session data over a specified time period, showing:
    - Session count trends (daily/weekly breakdown)
    - Topic frequency distribution
    - Average session duration trends
    - Patient engagement patterns
    - Risk flag occurrences over time

    Can be filtered to a specific patient or show practice-wide trends.

    Auth:
        Requires therapist role
        If patient_id provided, validates patient belongs to therapist

    Rate Limit:
        50 requests per minute per IP address

    Args:
        period: Time period for trends ("week", "month", "quarter", "year")
        patient_id: Optional UUID to filter trends to a specific patient
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        SessionTrendsResponse: Time-series trends and aggregated statistics

    Raises:
        HTTPException 400: If period is invalid
        HTTPException 403: If user is not a therapist or patient doesn't belong to therapist
        HTTPException 404: If patient_id provided but not found
        HTTPException 429: Rate limit exceeded

    Query Examples:
        GET /analytics/sessions/trends - monthly trends for all patients
        GET /analytics/sessions/trends?period=week - weekly trends for all patients
        GET /analytics/sessions/trends?patient_id=<uuid> - monthly trends for specific patient
        GET /analytics/sessions/trends?period=quarter&patient_id=<uuid> - quarterly trends for specific patient
    """
    # Validate period parameter (regex already validates in Query, this is for clarity)
    valid_periods = ["week", "month", "quarter", "year"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period '{period}'. Must be one of: {', '.join(valid_periods)}"
        )

    return await calculate_session_trends(current_user.id, period, patient_id, db)


@router.get("/topics", response_model=TopicsResponse)
@limiter.limit("50/minute")
async def get_topic_frequencies(
    request: Request,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get topic frequency distribution across all sessions.

    Aggregates and ranks all topics discussed in therapy sessions, showing:
    - Most frequently discussed topics
    - Topic occurrence counts
    - Topic co-occurrence patterns (topics that appear together)
    - Topic trends over time (emerging vs declining topics)

    Useful for understanding practice-wide patterns and common patient concerns.

    Auth:
        Requires therapist role

    Rate Limit:
        50 requests per minute per IP address

    Args:
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        TopicsResponse: Topic frequency statistics and rankings

    Raises:
        HTTPException 403: If user is not a therapist
        HTTPException 429: Rate limit exceeded
    """
    return await calculate_topic_frequencies(current_user.id, db)
