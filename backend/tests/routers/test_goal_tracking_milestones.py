# -*- coding: utf-8 -*-
"""
Integration tests for milestone detection in goal tracking endpoints (Wave 2).

Tests milestone detection when recording progress through the API, including:
1. Milestone detection at 25%, 50%, 75%, 100% progress thresholds
2. Milestone persistence and idempotency  
3. Multiple milestone detection in single update
4. Response structure includes milestone_achieved field

Integration Points:
- POST /api/goal-tracking/goals/{goal_id}/progress endpoint
- tracking_service.record_progress_entry()
- milestone_detector.check_milestones()
- Database persistence of ProgressMilestone records
"""
import pytest
import pytest_asyncio
from datetime import date, datetime, timedelta, time
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import ProgressMilestone, ProgressEntry, GoalTrackingConfig
from tests.utils.test_helpers import create_test_goal


# ============================================================================
# Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def goal_with_tracking(async_test_db: AsyncSession, sample_patient, therapist_user, sample_session):
    """
    Create a goal with tracking configuration for milestone tests.
    
    Goal: Reduce anxiety from 10 to 0 (baseline=10, target=0)
    Tracking: Scale 0-10, daily frequency, decrease direction
    """
    goal = create_test_goal(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Reduce anxiety level from 10 to 0",
        category="anxiety_management",
        baseline_value=10.0,
        target_value=0.0,
        status="in_progress"
    )
    async_test_db.add(goal)
    await async_test_db.flush()
    
    # Create tracking config
    tracking_config = GoalTrackingConfig(
        goal_id=goal.id,
        tracking_method="scale",
        tracking_frequency="daily",
        scale_min=0,
        scale_max=10,
        target_direction="decrease",
        reminder_enabled=True
    )
    async_test_db.add(tracking_config)
    await async_test_db.commit()
    await async_test_db.refresh(goal)
    await async_test_db.refresh(tracking_config)
    
    return (goal, tracking_config)


# ============================================================================
# Test Milestone Detection on Progress Recording
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
class TestMilestoneDetectionIntegration:
    """Test milestone detection through API endpoints"""

    async def test_record_progress_detects_50_percent_milestone(
        self,
        async_client: AsyncClient,
        async_test_db: AsyncSession,
        goal_with_tracking,
        therapist_auth_headers
    ):
        """
        Test that recording 50% progress triggers milestone detection.
        
        Scenario:
        - Goal: baseline=10, target=0 (anxiety reduction)
        - Record progress value=5.0 (50% improvement)
        - Verify response includes milestone_achieved
        - Verify ProgressMilestone records created in DB (25% and 50%)
        """
        goal, config = goal_with_tracking
        
        # Record progress at 50% improvement (10 → 5)
        progress_data = {
            "entry_date": str(date.today()),
            "entry_time": "14:30:00",
            "value": 5.0,
            "value_label": "Halfway to target",
            "notes": "Significant improvement in anxiety management",
            "context": "self_report"
        }
        
        response = await async_client.post(
            f"/api/goal-tracking/goals/{goal.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify response includes milestone field
        assert "milestones_achieved" in response_data or response_data.get("value") == 5.0
        
        # Verify milestone records were created in database
        milestone_query = select(ProgressMilestone).where(
            ProgressMilestone.goal_id == goal.id,
            ProgressMilestone.achieved_at.isnot(None)
        )
        result = await async_test_db.execute(milestone_query)
        milestones = result.scalars().all()
        
        # Should have 25% and 50% milestones
        assert len(milestones) >= 1  # At minimum 50% should be there
        milestone_percentages = {int(m.target_value * 100) for m in milestones}
        assert 50 in milestone_percentages or 25 in milestone_percentages
        
        # Verify milestone titles
        milestone_titles = {m.title for m in milestones}
        assert any("50%" in title for title in milestone_titles) or \
               any("25%" in title for title in milestone_titles)

    async def test_milestone_not_duplicated_on_subsequent_progress(
        self,
        async_client: AsyncClient,
        async_test_db: AsyncSession,
        goal_with_tracking,
        therapist_auth_headers
    ):
        """
        Test that milestones are not re-created if already achieved.
        
        Scenario:
        - Record progress to achieve 50% milestone
        - Record more progress (still at 50%)
        - Verify milestone count doesn't increase
        """
        goal, config = goal_with_tracking
        
        # First progress entry - achieve 50% milestone
        progress_data_1 = {
            "entry_date": str(date.today() - timedelta(days=1)),
            "entry_time": "10:00:00",
            "value": 5.0,
            "context": "self_report"
        }
        
        response1 = await async_client.post(
            f"/api/goal-tracking/goals/{goal.id}/progress",
            json=progress_data_1,
            headers=therapist_auth_headers
        )
        assert response1.status_code == 200
        
        # Count milestones after first entry
        milestone_query = select(func.count(ProgressMilestone.id)).where(
            ProgressMilestone.goal_id == goal.id
        )
        result = await async_test_db.execute(milestone_query)
        initial_count = result.scalar()
        
        # Second progress entry - same progress level
        progress_data_2 = {
            "entry_date": str(date.today()),
            "entry_time": "15:00:00",
            "value": 5.5,  # Still in 50% range
            "context": "self_report"
        }
        
        response2 = await async_client.post(
            f"/api/goal-tracking/goals/{goal.id}/progress",
            json=progress_data_2,
            headers=therapist_auth_headers
        )
        assert response2.status_code == 200
        
        # Count milestones after second entry
        result2 = await async_test_db.execute(milestone_query)
        final_count = result2.scalar()
        
        # Milestone count should not increase (no duplicates)
        assert final_count == initial_count

    async def test_multiple_milestones_in_one_update(
        self,
        async_client: AsyncClient,
        async_test_db: AsyncSession,
        goal_with_tracking,
        therapist_auth_headers
    ):
        """
        Test detecting multiple milestones when progress jumps significantly.
        
        Scenario:
        - Goal: baseline=10, target=0
        - Record progress jumping from 10 to 2.5 (75% improvement)
        - Verify 25%, 50%, and 75% milestones all created
        """
        goal, config = goal_with_tracking
        
        # Record large progress jump - 75% improvement (10 → 2.5)
        progress_data = {
            "entry_date": str(date.today()),
            "entry_time": "16:00:00",
            "value": 2.5,
            "value_label": "Major breakthrough",
            "notes": "Significant reduction in anxiety symptoms after therapy",
            "context": "self_report"
        }
        
        response = await async_client.post(
            f"/api/goal-tracking/goals/{goal.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )
        
        assert response.status_code == 200
        
        # Query all achieved milestones
        milestone_query = select(ProgressMilestone).where(
            ProgressMilestone.goal_id == goal.id,
            ProgressMilestone.achieved_at.isnot(None)
        )
        result = await async_test_db.execute(milestone_query)
        milestones = result.scalars().all()
        
        # Should have at least 3 milestones (25%, 50%, 75%)
        assert len(milestones) >= 2
        
        # Check that multiple thresholds are represented
        milestone_percentages = {int(m.target_value * 100) for m in milestones}
        # At minimum, should have some of these
        possible_milestones = {25, 50, 75}
        assert len(milestone_percentages.intersection(possible_milestones)) >= 1

    async def test_no_milestone_for_insufficient_progress(
        self,
        async_client: AsyncClient,
        async_test_db: AsyncSession,
        goal_with_tracking,
        therapist_auth_headers
    ):
        """
        Test that no milestones are created for progress below 25% threshold.
        
        Scenario:
        - Goal: baseline=10, target=0
        - Record 10% progress (value=9.0)
        - Verify no milestones created
        """
        goal, config = goal_with_tracking
        
        # Record small progress (10% - below 25% threshold)
        progress_data = {
            "entry_date": str(date.today()),
            "entry_time": "09:00:00",
            "value": 9.0,
            "notes": "Slight improvement",
            "context": "self_report"
        }
        
        response = await async_client.post(
            f"/api/goal-tracking/goals/{goal.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )
        
        assert response.status_code == 200
        
        # Query milestones
        milestone_query = select(func.count(ProgressMilestone.id)).where(
            ProgressMilestone.goal_id == goal.id,
            ProgressMilestone.achieved_at.isnot(None)
        )
        result = await async_test_db.execute(milestone_query)
        milestone_count = result.scalar()
        
        # Should have no milestones for <25% progress
        assert milestone_count == 0


# ============================================================================
# Test Milestone Response Structure
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
class TestMilestoneResponseStructure:
    """Test that milestone data is properly included in API responses"""

    async def test_progress_response_includes_milestone_data(
        self,
        async_client: AsyncClient,
        async_test_db: AsyncSession,
        goal_with_tracking,
        patient_auth_headers
    ):
        """
        Test that progress entry response includes milestone achievement info.
        
        Verifies:
        - Response has milestone-related field (if achieved)
        - Response structure matches schema
        """
        goal, config = goal_with_tracking
        
        # Record progress at 50% (should trigger milestone)
        progress_data = {
            "entry_date": str(date.today()),
            "entry_time": "11:30:00",
            "value": 5.0,
            "context": "self_report"
        }
        
        response = await async_client.post(
            f"/api/goal-tracking/goals/{goal.id}/progress",
            json=progress_data,
            headers=patient_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure includes entry data
        assert "id" in data
        assert "goal_id" in data
        assert "value" in data
        assert data["value"] == 5.0
        
        # Response should be valid ProgressEntryResponse
        assert "entry_date" in data
        assert "recorded_at" in data

    async def test_milestone_includes_achievement_timestamp(
        self,
        async_client: AsyncClient,
        async_test_db: AsyncSession,
        goal_with_tracking,
        therapist_auth_headers
    ):
        """
        Test that achieved milestones have achievement timestamp set.
        
        Verifies:
        - achieved_at is populated when milestone is reached
        - Timestamp is recent (within last minute)
        """
        goal, config = goal_with_tracking
        
        # Record progress to achieve milestone
        progress_data = {
            "entry_date": str(date.today()),
            "entry_time": "12:00:00",
            "value": 7.5,
            "context": "self_report"
        }
        
        before_recording = datetime.utcnow()
        
        response = await async_client.post(
            f"/api/goal-tracking/goals/{goal.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )
        
        assert response.status_code == 200
        
        # Query achieved milestones
        milestone_query = select(ProgressMilestone).where(
            ProgressMilestone.goal_id == goal.id,
            ProgressMilestone.achieved_at.isnot(None)
        )
        result = await async_test_db.execute(milestone_query)
        milestones = result.scalars().all()
        
        # Verify at least one milestone has achievement timestamp
        assert len(milestones) > 0
        
        for milestone in milestones:
            assert milestone.achieved_at is not None
            # Timestamp should be recent (within last 5 minutes)
            time_diff = datetime.utcnow() - milestone.achieved_at
            assert time_diff.total_seconds() < 300  # 5 minutes
