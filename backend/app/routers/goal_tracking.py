"""
Goal tracking endpoints for treatment goal management and progress monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from typing import List, Optional
from datetime import date as date_type, datetime

from app.database import get_db
from app.auth.dependencies import require_role
from app.models.db_models import User, TherapistPatient
from app.models.goal_models import TreatmentGoal
from app.schemas.tracking_schemas import (
    TrackingConfigCreate,
    TrackingConfigResponse,
    ProgressEntryCreate,
    ProgressEntryResponse,
    ProgressHistoryQuery,
    ProgressHistoryResponse,
    GoalDashboardResponse,
    TreatmentGoalCreate,
    TreatmentGoalResponse,
    GoalStatus,
    AggregationPeriod,
    NotificationsResponse,
    NotificationResponse,
    NotificationReadUpdate,
    MilestoneData
)
from app.services import tracking_service, dashboard_service
from app.middleware.rate_limit import limiter

router = APIRouter()


@router.post("/goals/{goal_id}/tracking/config", response_model=TrackingConfigResponse)
@limiter.limit("20/minute")
async def create_goal_tracking_config(
    request: Request,
    goal_id: UUID,
    config_data: TrackingConfigCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Configure tracking method for a goal.

    Sets up how progress will be tracked for a specific goal including:
    - Tracking method (scale, frequency, duration, binary, assessment)
    - Tracking frequency (daily, weekly, session, custom)
    - Scale ranges and labels (if using scale method)
    - Units (if using frequency or duration method)
    - Target direction (increase, decrease, maintain)
    - Reminder settings

    Auth:
        Requires therapist role

    Rate Limit:
        20 requests per minute per IP address

    Args:
        goal_id: UUID of the goal to configure tracking for
        config_data: TrackingConfigCreate schema with configuration details
        current_user: Authenticated therapist user
        db: AsyncSession database dependency

    Returns:
        TrackingConfigResponse: Created/updated tracking configuration

    Raises:
        HTTPException 403: If user is not a therapist
        HTTPException 404: If goal not found
        HTTPException 400: If tracking method requirements not met (e.g., missing scale_min/max)
        HTTPException 429: Rate limit exceeded

    Example Request:
        POST /goals/{goal_id}/tracking/config
        {
            "tracking_method": "scale",
            "tracking_frequency": "daily",
            "scale_min": 1,
            "scale_max": 10,
            "target_direction": "decrease",
            "reminder_enabled": true
        }
    """
    return await tracking_service.create_tracking_config(
        goal_id=goal_id,
        config_data=config_data,
        db=db
    )


@router.post("/goals/{goal_id}/progress", response_model=ProgressEntryResponse)
@limiter.limit("50/minute")
async def record_progress(
    request: Request,
    goal_id: UUID,
    entry_data: ProgressEntryCreate,
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Record a progress entry for a goal.

    Creates a new progress data point with value, date, time, notes, and context.
    Validates that the goal exists and belongs to the current user (patient) or
    their assigned therapist.

    Auth:
        Requires therapist or patient role
        Data isolation: Goal must belong to current user or their therapist

    Rate Limit:
        50 requests per minute per IP address

    Args:
        goal_id: UUID of the goal to record progress for
        entry_data: ProgressEntryCreate schema with entry details
        current_user: Authenticated user (therapist or patient)
        db: AsyncSession database dependency

    Returns:
        ProgressEntryResponse: Created progress entry

    Raises:
        HTTPException 403: If user not authorized to record progress for this goal
        HTTPException 404: If goal or tracking config not found
        HTTPException 400: If entry date is in future or value out of range
        HTTPException 429: Rate limit exceeded

    Data Isolation:
        - Patients: Can only record progress for their own goals
        - Therapists: Can only record progress for goals of assigned patients

    Example Request:
        POST /goals/{goal_id}/progress
        {
            "entry_date": "2025-12-17",
            "entry_time": "14:30:00",
            "value": 7.5,
            "value_label": "Better today",
            "notes": "Feeling much more in control",
            "context": "self_report"
        }
    """
    # Verify goal exists and user has access
    goal_query = select(TreatmentGoal).where(TreatmentGoal.id == goal_id)
    goal_result = await db.execute(goal_query)
    goal = goal_result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=404,
            detail=f"Goal with id {goal_id} not found"
        )

    # Data isolation check
    if current_user.role.value == "patient":
        # Patients can only record progress for their own goals
        if goal.patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to record progress for this goal"
            )
    elif current_user.role.value == "therapist":
        # Therapists can only record progress for goals of assigned patients
        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == goal.patient_id,
                TherapistPatient.is_active == True
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to record progress for this patient's goal"
            )

    return await tracking_service.record_progress_entry(
        goal_id=goal_id,
        entry_data=entry_data,
        recorded_by_id=current_user.id,
        db=db
    )


@router.get("/goals/{goal_id}/progress", response_model=ProgressHistoryResponse)
@limiter.limit("100/minute")
async def get_goal_progress_history(
    request: Request,
    goal_id: UUID,
    start_date: Optional[date_type] = Query(None, description="Start date for filtering entries"),
    end_date: Optional[date_type] = Query(None, description="End date for filtering entries"),
    aggregation: Optional[AggregationPeriod] = Query(None, description="Period for aggregating data (none, daily, weekly, monthly)"),
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get progress history for a goal with filtering and aggregation.

    Retrieves all progress entries for a goal, optionally filtered by date range
    and aggregated by period (daily, weekly, monthly). Includes statistical summary
    with average, min, max, trend slope, and trend direction.

    Auth:
        Requires therapist or patient role
        Data isolation: Goal must belong to current user or their therapist

    Rate Limit:
        100 requests per minute per IP address

    Query Parameters:
        - start_date: Include only entries on or after this date (ISO 8601 format)
        - end_date: Include only entries on or before this date (ISO 8601 format)
        - aggregation: Group entries by period (none, daily, weekly, monthly)

    Args:
        goal_id: UUID of the goal to retrieve history for
        start_date: Optional start date filter
        end_date: Optional end date filter
        aggregation: Optional aggregation period
        current_user: Authenticated user (therapist or patient)
        db: AsyncSession database dependency

    Returns:
        ProgressHistoryResponse: Progress entries and statistical summary

    Raises:
        HTTPException 403: If user not authorized to view this goal's progress
        HTTPException 404: If goal not found
        HTTPException 429: Rate limit exceeded

    Data Isolation:
        - Patients: Can only view progress for their own goals
        - Therapists: Can only view progress for goals of assigned patients

    Example Request:
        GET /goals/{goal_id}/progress?start_date=2025-11-01&end_date=2025-12-17&aggregation=weekly
    """
    # Verify goal exists and user has access
    goal_query = select(TreatmentGoal).where(TreatmentGoal.id == goal_id)
    goal_result = await db.execute(goal_query)
    goal = goal_result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=404,
            detail=f"Goal with id {goal_id} not found"
        )

    # Data isolation check
    if current_user.role.value == "patient":
        # Patients can only view progress for their own goals
        if goal.patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view progress for this goal"
            )
    elif current_user.role.value == "therapist":
        # Therapists can only view progress for goals of assigned patients
        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == goal.patient_id,
                TherapistPatient.is_active == True
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this patient's goal progress"
            )

    # Build query parameters
    query_params = ProgressHistoryQuery(
        start_date=start_date,
        end_date=end_date,
        aggregation=aggregation
    )

    return await tracking_service.get_progress_history(
        goal_id=goal_id,
        query_params=query_params,
        db=db
    )


@router.get("/patients/{patient_id}/goals/dashboard", response_model=GoalDashboardResponse)
@limiter.limit("50/minute")
async def get_patient_goal_dashboard(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete goal tracking dashboard for a patient.

    Aggregates data from multiple sources including:
    - Active goals count
    - Tracking activity summary (entries this week, streak days, completion rate)
    - Per-goal dashboard items with progress metrics and trends
    - Recent milestones achieved (last 30 days)
    - Assessments due for administration

    Auth:
        Requires therapist or patient role
        Data isolation: Therapist must have access to patient, or patient must be current user

    Rate Limit:
        50 requests per minute per IP address

    Args:
        patient_id: UUID of the patient to retrieve dashboard for
        current_user: Authenticated user (therapist or patient)
        db: AsyncSession database dependency

    Returns:
        GoalDashboardResponse: Complete dashboard with all goal tracking data

    Raises:
        HTTPException 403: If user not authorized to view this patient's dashboard
        HTTPException 404: If patient not found
        HTTPException 429: Rate limit exceeded

    Data Isolation:
        - Patients: Can only view their own dashboard
        - Therapists: Can only view dashboards of assigned patients

    Example Response:
        {
            "patient_id": "uuid",
            "active_goals": 3,
            "tracking_summary": {
                "entries_this_week": 12,
                "streak_days": 7,
                "completion_rate": 85.7
            },
            "goals": [...],
            "recent_milestones": [...],
            "assessments_due": [...]
        }
    """
    # Data isolation check
    if current_user.role.value == "patient":
        # Patients can only view their own dashboard
        if patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Patients can only view their own goal dashboard"
            )
    elif current_user.role.value == "therapist":
        # Therapists can only view dashboards of assigned patients
        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == patient_id,
                TherapistPatient.is_active == True
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this patient's goal dashboard"
            )

    return await dashboard_service.get_goal_dashboard(
        patient_id=patient_id,
        db=db
    )


@router.post("/patients/{patient_id}/goals", response_model=TreatmentGoalResponse)
@limiter.limit("20/minute")
async def create_treatment_goal(
    request: Request,
    patient_id: UUID,
    goal_data: TreatmentGoalCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new treatment goal for a patient.

    Creates a goal record with description, category, baseline/target values,
    and target date. Goals are initially assigned status 'assigned' and can be
    updated to 'in_progress', 'completed', or 'abandoned' later.

    Auth:
        Requires therapist role

    Rate Limit:
        20 requests per minute per IP address

    Args:
        patient_id: UUID of the patient to create goal for
        goal_data: TreatmentGoalCreate schema with goal details
        current_user: Authenticated therapist user
        db: AsyncSession database dependency

    Returns:
        TreatmentGoalResponse: Created treatment goal

    Raises:
        HTTPException 403: If user is not a therapist
        HTTPException 404: If patient not found
        HTTPException 400: If validation fails (e.g., target date in past)
        HTTPException 429: Rate limit exceeded

    Example Request:
        POST /patients/{patient_id}/goals
        {
            "description": "Reduce anxiety symptoms to manageable levels",
            "category": "Anxiety management",
            "baseline_value": 8.5,
            "target_value": 3.0,
            "target_date": "2026-03-15"
        }
    """
    # Verify patient exists
    patient_query = select(User).where(
        and_(
            User.id == patient_id,
            User.role == "patient"
        )
    )
    patient_result = await db.execute(patient_query)
    patient = patient_result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient with id {patient_id} not found"
        )

    # Create treatment goal
    new_goal = TreatmentGoal(
        patient_id=patient_id,
        therapist_id=current_user.id,
        description=goal_data.description,
        category=goal_data.category,
        baseline_value=goal_data.baseline_value,
        target_value=goal_data.target_value,
        target_date=goal_data.target_date,
        status='assigned'
    )

    db.add(new_goal)
    await db.commit()
    await db.refresh(new_goal)

    return TreatmentGoalResponse.model_validate(new_goal)


@router.get("/patients/{patient_id}/goals", response_model=List[TreatmentGoalResponse])
@limiter.limit("100/minute")
async def list_patient_goals(
    request: Request,
    patient_id: UUID,
    status: Optional[GoalStatus] = Query(None, description="Filter by goal status (assigned, in_progress, completed, abandoned)"),
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all treatment goals for a patient with optional status filtering.

    Retrieves goals ordered by creation date (newest first). Can be filtered
    by status to show only assigned, in_progress, completed, or abandoned goals.

    Auth:
        Requires therapist or patient role
        Data isolation: Therapist must have access to patient, or patient must be current user

    Rate Limit:
        100 requests per minute per IP address

    Query Parameters:
        - status: Optional filter by goal status (assigned, in_progress, completed, abandoned)

    Args:
        patient_id: UUID of the patient to list goals for
        status: Optional GoalStatus filter
        current_user: Authenticated user (therapist or patient)
        db: AsyncSession database dependency

    Returns:
        List[TreatmentGoalResponse]: List of treatment goals matching filters

    Raises:
        HTTPException 403: If user not authorized to view this patient's goals
        HTTPException 404: If patient not found
        HTTPException 429: Rate limit exceeded

    Data Isolation:
        - Patients: Can only view their own goals
        - Therapists: Can only view goals of assigned patients

    Example Request:
        GET /patients/{patient_id}/goals
        GET /patients/{patient_id}/goals?status=in_progress
    """
    # Data isolation check
    if current_user.role.value == "patient":
        # Patients can only view their own goals
        if patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Patients can only view their own goals"
            )
    elif current_user.role.value == "therapist":
        # Therapists can only view goals of assigned patients
        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == patient_id,
                TherapistPatient.is_active == True
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this patient's goals"
            )

    # Build query
    query = select(TreatmentGoal).where(
        TreatmentGoal.patient_id == patient_id
    ).order_by(TreatmentGoal.created_at.desc())

    # Apply status filter if provided
    if status:
        query = query.where(TreatmentGoal.status == status.value)

    # Execute query
    result = await db.execute(query)
    goals = result.scalars().all()

    return [TreatmentGoalResponse.model_validate(goal) for goal in goals]


@router.get("/notifications", response_model=NotificationsResponse)
@limiter.limit("100/minute")
async def get_notifications(
    request: Request,
    patient_id: Optional[UUID] = Query(None, description="Patient ID to filter notifications (required for patients, optional for therapists)"),
    since: Optional[datetime] = Query(None, description="Only include notifications since this timestamp (default: last 24 hours)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of notifications to return"),
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent milestone achievement notifications.

    Retrieves milestone notifications that can be polled by frontends for
    real-time updates. Supports filtering by time range and patient.

    Auth:
        Requires therapist or patient role
        Data isolation: Patients can only see their own notifications,
                       therapists can see notifications for assigned patients

    Rate Limit:
        100 requests per minute per IP address

    Query Parameters:
        - patient_id: Filter to specific patient (required for patients viewing their own)
        - since: Only show notifications after this timestamp (ISO 8601 format)
                 Default: last 24 hours
        - limit: Max notifications to return (1-100, default: 20)

    Args:
        request: FastAPI request object (for rate limiting)
        patient_id: Optional patient ID filter
        since: Optional timestamp filter
        limit: Maximum number of results
        current_user: Authenticated user
        db: AsyncSession database dependency

    Returns:
        NotificationsResponse: List of notifications with unread count

    Raises:
        HTTPException 403: If patient tries to access another patient's notifications
        HTTPException 400: If patient_id not provided by patient user
        HTTPException 429: Rate limit exceeded

    Data Isolation:
        - Patients: Can only view their own notifications (must provide patient_id matching their user ID)
        - Therapists: Can view notifications for all assigned patients

    Example Request:
        GET /notifications?patient_id={uuid}&since=2025-01-15T00:00:00Z&limit=20

    Example Response:
        {
            "notifications": [
                {
                    "id": "uuid",
                    "type": "milestone_achieved",
                    "goal_id": "uuid",
                    "goal_description": "Reduce anxiety to manageable levels",
                    "milestone": {
                        "type": "percentage",
                        "title": "50% Improvement Achieved",
                        "description": "Reached 50% progress toward goal target",
                        "achieved_at": "2025-01-15T10:30:00Z"
                    },
                    "created_at": "2025-01-15T10:30:00Z",
                    "read": false
                }
            ],
            "unread_count": 3
        }
    """
    from app.models.tracking_models import ProgressMilestone
    from sqlalchemy.orm import selectinload

    # Data isolation check
    if current_user.role.value == "patient":
        # Patients must provide their own patient_id
        if patient_id is None:
            raise HTTPException(
                status_code=400,
                detail="patient_id is required for patient users"
            )

        if patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Patients can only view their own notifications"
            )

    elif current_user.role.value == "therapist":
        # Therapists can optionally filter by patient_id
        # If patient_id provided, verify they have access to that patient
        if patient_id:
            assignment_query = select(TherapistPatient).where(
                and_(
                    TherapistPatient.therapist_id == current_user.id,
                    TherapistPatient.patient_id == patient_id,
                    TherapistPatient.is_active == True
                )
            )
            assignment_result = await db.execute(assignment_query)
            assignment = assignment_result.scalar_one_or_none()

            if not assignment:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to view this patient's notifications"
                )

    # Set default time filter to last 24 hours if not provided
    if since is None:
        from datetime import timedelta
        since = datetime.utcnow() - timedelta(hours=24)

    # Build query for achieved milestones
    query = (
        select(ProgressMilestone)
        .options(selectinload(ProgressMilestone.goal))
        .where(
            and_(
                ProgressMilestone.achieved_at.isnot(None),
                ProgressMilestone.achieved_at >= since
            )
        )
        .order_by(ProgressMilestone.achieved_at.desc())
        .limit(limit)
    )

    # Filter by patient if specified
    if patient_id:
        # Join with TreatmentGoal to filter by patient_id
        query = query.join(TreatmentGoal).where(TreatmentGoal.patient_id == patient_id)
    elif current_user.role.value == "therapist":
        # Therapist without patient_id filter: show all their patients' notifications
        # Join with TherapistPatient to get only assigned patients
        query = (
            query
            .join(TreatmentGoal)
            .join(
                TherapistPatient,
                and_(
                    TherapistPatient.patient_id == TreatmentGoal.patient_id,
                    TherapistPatient.therapist_id == current_user.id,
                    TherapistPatient.is_active == True
                )
            )
        )

    # Execute query
    result = await db.execute(query)
    milestones = result.scalars().all()

    # Build notification responses
    notifications = []
    for milestone in milestones:
        notification = NotificationResponse(
            id=milestone.id,
            type="milestone_achieved",
            goal_id=milestone.goal_id,
            goal_description=milestone.goal.description,
            milestone=MilestoneData(
                type=milestone.milestone_type or "custom",
                title=milestone.title,
                description=milestone.description,
                achieved_at=milestone.achieved_at
            ),
            created_at=milestone.achieved_at,
            read=milestone.read
        )
        notifications.append(notification)

    # Count unread notifications (same filters, but only count unread)
    unread_query = (
        select(ProgressMilestone)
        .where(
            and_(
                ProgressMilestone.achieved_at.isnot(None),
                ProgressMilestone.achieved_at >= since,
                ProgressMilestone.read == False
            )
        )
    )

    if patient_id:
        unread_query = unread_query.join(TreatmentGoal).where(TreatmentGoal.patient_id == patient_id)
    elif current_user.role.value == "therapist":
        unread_query = (
            unread_query
            .join(TreatmentGoal)
            .join(
                TherapistPatient,
                and_(
                    TherapistPatient.patient_id == TreatmentGoal.patient_id,
                    TherapistPatient.therapist_id == current_user.id,
                    TherapistPatient.is_active == True
                )
            )
        )

    unread_result = await db.execute(unread_query)
    unread_count = len(unread_result.scalars().all())

    return NotificationsResponse(
        notifications=notifications,
        unread_count=unread_count
    )


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
@limiter.limit("100/minute")
async def mark_notification_read(
    request: Request,
    notification_id: UUID,
    update_data: NotificationReadUpdate = NotificationReadUpdate(read=True),
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a notification as read or unread.

    Updates the read status of a milestone notification. Used to track
    which notifications the user has seen.

    Auth:
        Requires therapist or patient role
        Data isolation: Users can only mark notifications for their accessible patients

    Rate Limit:
        100 requests per minute per IP address

    Args:
        request: FastAPI request object (for rate limiting)
        notification_id: UUID of the notification (milestone) to update
        update_data: Read status update (default: read=true)
        current_user: Authenticated user
        db: AsyncSession database dependency

    Returns:
        NotificationResponse: Updated notification

    Raises:
        HTTPException 404: If notification not found
        HTTPException 403: If user not authorized to access this notification
        HTTPException 429: Rate limit exceeded

    Data Isolation:
        - Patients: Can only mark their own notifications as read
        - Therapists: Can mark notifications for assigned patients as read

    Example Request:
        PATCH /notifications/{notification_id}/read
        {
            "read": true
        }
    """
    from app.models.tracking_models import ProgressMilestone
    from sqlalchemy.orm import selectinload

    # Load milestone with goal relationship
    query = (
        select(ProgressMilestone)
        .options(selectinload(ProgressMilestone.goal))
        .where(ProgressMilestone.id == notification_id)
    )

    result = await db.execute(query)
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(
            status_code=404,
            detail=f"Notification with id {notification_id} not found"
        )

    # Get patient_id from the goal
    patient_id = milestone.goal.patient_id

    # Data isolation check
    if current_user.role.value == "patient":
        # Patients can only mark their own notifications
        if patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to mark this notification as read"
            )
    elif current_user.role.value == "therapist":
        # Therapists can only mark notifications for assigned patients
        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == patient_id,
                TherapistPatient.is_active == True
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to mark this notification as read"
            )

    # Update read status
    milestone.read = update_data.read
    await db.commit()
    await db.refresh(milestone)

    # Return updated notification
    notification = NotificationResponse(
        id=milestone.id,
        type="milestone_achieved",
        goal_id=milestone.goal_id,
        goal_description=milestone.goal.description,
        milestone=MilestoneData(
            type=milestone.milestone_type or "custom",
            title=milestone.title,
            description=milestone.description,
            achieved_at=milestone.achieved_at
        ),
        created_at=milestone.achieved_at,
        read=milestone.read
    )

    return notification
