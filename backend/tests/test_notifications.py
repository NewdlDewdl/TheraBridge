"""
Test notification polling endpoints for milestone achievements.

Tests the GET /api/v1/notifications and PATCH /api/v1/notifications/{id}/read endpoints
to ensure proper functionality, authorization, and performance.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from app.models.tracking_models import ProgressMilestone
from app.models.goal_models import TreatmentGoal
from app.models.db_models import User, TherapistPatient


@pytest.mark.asyncio
async def test_patient_can_view_own_notifications(async_client, patient_user, therapist_user, db_session):
    """Test that patients can view their own milestone notifications"""

    # Create a goal for the patient
    goal = TreatmentGoal(
        id=uuid4(),
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        description="Test goal for notifications",
        status="in_progress",
        baseline_value=10.0,
        target_value=2.0
    )
    db_session.add(goal)
    await db_session.flush()

    # Create an achieved milestone
    milestone = ProgressMilestone(
        id=uuid4(),
        goal_id=goal.id,
        milestone_type="percentage",
        title="50% Improvement Achieved",
        description="Reached 50% progress toward goal target",
        target_value=0.50,
        achieved_at=datetime.utcnow(),
        read=False
    )
    db_session.add(milestone)
    await db_session.commit()

    # Patient requests their own notifications
    response = await async_client.get(
        f"/api/v1/notifications?patient_id={patient_user.id}",
        headers={"Authorization": f"Bearer {patient_user.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "notifications" in data
    assert "unread_count" in data
    assert len(data["notifications"]) == 1
    assert data["unread_count"] == 1

    notification = data["notifications"][0]
    assert notification["type"] == "milestone_achieved"
    assert notification["goal_id"] == str(goal.id)
    assert notification["read"] is False
    assert notification["milestone"]["type"] == "percentage"
    assert notification["milestone"]["title"] == "50% Improvement Achieved"


@pytest.mark.asyncio
async def test_patient_cannot_view_other_patient_notifications(async_client, patient_user, patient_user_2):
    """Test that patients cannot view other patients' notifications"""

    # Patient tries to access another patient's notifications
    response = await async_client.get(
        f"/api/v1/notifications?patient_id={patient_user_2.id}",
        headers={"Authorization": f"Bearer {patient_user.access_token}"}
    )

    assert response.status_code == 403
    assert "can only view their own" in response.json()["detail"]


@pytest.mark.asyncio
async def test_patient_must_provide_patient_id(async_client, patient_user):
    """Test that patients must provide patient_id parameter"""

    # Patient requests without patient_id
    response = await async_client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {patient_user.access_token}"}
    )

    assert response.status_code == 400
    assert "patient_id is required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_therapist_can_view_assigned_patient_notifications(
    async_client, therapist_user, patient_user, db_session
):
    """Test that therapists can view notifications for assigned patients"""

    # Create therapist-patient relationship
    relationship = TherapistPatient(
        id=uuid4(),
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        is_active=True
    )
    db_session.add(relationship)

    # Create a goal
    goal = TreatmentGoal(
        id=uuid4(),
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        description="Test goal",
        status="in_progress"
    )
    db_session.add(goal)
    await db_session.flush()

    # Create milestone
    milestone = ProgressMilestone(
        id=uuid4(),
        goal_id=goal.id,
        milestone_type="streak",
        title="7-Day Streak Achieved",
        achieved_at=datetime.utcnow(),
        read=False
    )
    db_session.add(milestone)
    await db_session.commit()

    # Therapist requests patient's notifications
    response = await async_client.get(
        f"/api/v1/notifications?patient_id={patient_user.id}",
        headers={"Authorization": f"Bearer {therapist_user.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 1


@pytest.mark.asyncio
async def test_therapist_cannot_view_unassigned_patient_notifications(
    async_client, therapist_user, patient_user
):
    """Test that therapists cannot view notifications for unassigned patients"""

    # Therapist tries to access unassigned patient's notifications
    response = await async_client.get(
        f"/api/v1/notifications?patient_id={patient_user.id}",
        headers={"Authorization": f"Bearer {therapist_user.access_token}"}
    )

    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


@pytest.mark.asyncio
async def test_since_parameter_filters_notifications(
    async_client, patient_user, therapist_user, db_session
):
    """Test that 'since' parameter correctly filters notifications by time"""

    # Create a goal
    goal = TreatmentGoal(
        id=uuid4(),
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        description="Test goal",
        status="in_progress"
    )
    db_session.add(goal)
    await db_session.flush()

    # Create old milestone (2 days ago)
    old_milestone = ProgressMilestone(
        id=uuid4(),
        goal_id=goal.id,
        milestone_type="percentage",
        title="25% Improvement",
        achieved_at=datetime.utcnow() - timedelta(days=2),
        read=False
    )
    db_session.add(old_milestone)

    # Create recent milestone (1 hour ago)
    recent_milestone = ProgressMilestone(
        id=uuid4(),
        goal_id=goal.id,
        milestone_type="percentage",
        title="50% Improvement",
        achieved_at=datetime.utcnow() - timedelta(hours=1),
        read=False
    )
    db_session.add(recent_milestone)
    await db_session.commit()

    # Request notifications since 12 hours ago
    since_time = datetime.utcnow() - timedelta(hours=12)
    response = await async_client.get(
        f"/api/v1/notifications?patient_id={patient_user.id}&since={since_time.isoformat()}",
        headers={"Authorization": f"Bearer {patient_user.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should only see the recent milestone
    assert len(data["notifications"]) == 1
    assert data["notifications"][0]["milestone"]["title"] == "50% Improvement"


@pytest.mark.asyncio
async def test_limit_parameter_caps_notifications(
    async_client, patient_user, therapist_user, db_session
):
    """Test that 'limit' parameter correctly limits result count"""

    # Create a goal
    goal = TreatmentGoal(
        id=uuid4(),
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        description="Test goal",
        status="in_progress"
    )
    db_session.add(goal)
    await db_session.flush()

    # Create 10 milestones
    for i in range(10):
        milestone = ProgressMilestone(
            id=uuid4(),
            goal_id=goal.id,
            milestone_type="custom",
            title=f"Milestone {i}",
            achieved_at=datetime.utcnow() - timedelta(minutes=i),
            read=False
        )
        db_session.add(milestone)
    await db_session.commit()

    # Request with limit=5
    response = await async_client.get(
        f"/api/v1/notifications?patient_id={patient_user.id}&limit=5",
        headers={"Authorization": f"Bearer {patient_user.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should only see 5 notifications
    assert len(data["notifications"]) == 5


@pytest.mark.asyncio
async def test_mark_notification_as_read(
    async_client, patient_user, therapist_user, db_session
):
    """Test marking a notification as read"""

    # Create a goal
    goal = TreatmentGoal(
        id=uuid4(),
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        description="Test goal",
        status="in_progress"
    )
    db_session.add(goal)
    await db_session.flush()

    # Create milestone
    milestone = ProgressMilestone(
        id=uuid4(),
        goal_id=goal.id,
        milestone_type="percentage",
        title="50% Improvement",
        achieved_at=datetime.utcnow(),
        read=False
    )
    db_session.add(milestone)
    await db_session.commit()

    # Mark as read
    response = await async_client.patch(
        f"/api/v1/notifications/{milestone.id}/read",
        json={"read": True},
        headers={"Authorization": f"Bearer {patient_user.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["read"] is True

    # Verify in database
    await db_session.refresh(milestone)
    assert milestone.read is True


@pytest.mark.asyncio
async def test_patient_cannot_mark_other_patient_notification_as_read(
    async_client, patient_user, patient_user_2, therapist_user, db_session
):
    """Test that patients cannot mark other patients' notifications as read"""

    # Create a goal for patient 2
    goal = TreatmentGoal(
        id=uuid4(),
        patient_id=patient_user_2.id,
        therapist_id=therapist_user.id,
        description="Test goal",
        status="in_progress"
    )
    db_session.add(goal)
    await db_session.flush()

    # Create milestone for patient 2
    milestone = ProgressMilestone(
        id=uuid4(),
        goal_id=goal.id,
        milestone_type="percentage",
        title="50% Improvement",
        achieved_at=datetime.utcnow(),
        read=False
    )
    db_session.add(milestone)
    await db_session.commit()

    # Patient 1 tries to mark patient 2's notification as read
    response = await async_client.patch(
        f"/api/v1/notifications/{milestone.id}/read",
        json={"read": True},
        headers={"Authorization": f"Bearer {patient_user.access_token}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unread_count_calculation(
    async_client, patient_user, therapist_user, db_session
):
    """Test that unread_count is calculated correctly"""

    # Create a goal
    goal = TreatmentGoal(
        id=uuid4(),
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        description="Test goal",
        status="in_progress"
    )
    db_session.add(goal)
    await db_session.flush()

    # Create 3 unread and 2 read milestones
    for i in range(5):
        milestone = ProgressMilestone(
            id=uuid4(),
            goal_id=goal.id,
            milestone_type="custom",
            title=f"Milestone {i}",
            achieved_at=datetime.utcnow(),
            read=(i < 2)  # First 2 are read, last 3 are unread
        )
        db_session.add(milestone)
    await db_session.commit()

    # Get notifications
    response = await async_client.get(
        f"/api/v1/notifications?patient_id={patient_user.id}",
        headers={"Authorization": f"Bearer {patient_user.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should have 5 total notifications but only 3 unread
    assert len(data["notifications"]) == 5
    assert data["unread_count"] == 3


@pytest.mark.asyncio
async def test_notifications_ordered_by_achieved_at_desc(
    async_client, patient_user, therapist_user, db_session
):
    """Test that notifications are ordered by achieved_at descending (newest first)"""

    # Create a goal
    goal = TreatmentGoal(
        id=uuid4(),
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        description="Test goal",
        status="in_progress"
    )
    db_session.add(goal)
    await db_session.flush()

    # Create milestones with different timestamps
    timestamps = [
        datetime.utcnow() - timedelta(hours=3),
        datetime.utcnow() - timedelta(hours=1),
        datetime.utcnow() - timedelta(hours=2),
    ]

    for i, ts in enumerate(timestamps):
        milestone = ProgressMilestone(
            id=uuid4(),
            goal_id=goal.id,
            milestone_type="custom",
            title=f"Milestone at {ts}",
            achieved_at=ts,
            read=False
        )
        db_session.add(milestone)
    await db_session.commit()

    # Get notifications
    response = await async_client.get(
        f"/api/v1/notifications?patient_id={patient_user.id}",
        headers={"Authorization": f"Bearer {patient_user.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should be ordered newest first
    achieved_times = [
        datetime.fromisoformat(n["milestone"]["achieved_at"].replace("Z", "+00:00"))
        for n in data["notifications"]
    ]

    # Verify descending order
    for i in range(len(achieved_times) - 1):
        assert achieved_times[i] >= achieved_times[i + 1]
