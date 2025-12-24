"""
Demo Mode API Router
Handles demo initialization, reset, and status
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List
from uuid import uuid4
from datetime import datetime
import logging

from app.database import get_db
from app.middleware.demo_auth import get_demo_user, require_demo_auth
from supabase import Client

router = APIRouter(prefix="/api/demo", tags=["demo"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class DemoInitResponse(BaseModel):
    """Response for demo initialization"""
    demo_token: str
    patient_id: str
    session_ids: List[str]
    expires_at: str
    message: str


class DemoResetResponse(BaseModel):
    """Response for demo reset"""
    patient_id: str
    session_ids: List[str]
    message: str


class DemoStatusResponse(BaseModel):
    """Response for demo status check"""
    demo_token: str
    patient_id: str
    session_count: int
    created_at: str
    expires_at: str
    is_expired: bool


# ============================================================================
# Demo Endpoints
# ============================================================================

@router.post("/initialize", response_model=DemoInitResponse)
async def initialize_demo(db: Client = Depends(get_db)):
    """
    Initialize a new demo user with 10 pre-loaded therapy sessions

    This endpoint:
    1. Generates a unique demo token (UUID)
    2. Calls seed_demo_user_sessions() SQL function
    3. Returns demo token for localStorage storage

    Returns:
        DemoInitResponse with token and session IDs
    """
    # Generate unique demo token
    demo_token = str(uuid4())

    logger.info(f"Initializing demo user with token: {demo_token}")

    try:
        # Call SQL function to seed demo data
        response = db.rpc("seed_demo_user_sessions", {"p_demo_token": demo_token}).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to create demo user and sessions"
            )

        result = response.data[0]
        patient_id = result["patient_id"]
        session_ids = result["session_ids"]

        # Fetch demo user to get expiry
        user_response = db.table("users").select("demo_expires_at").eq("id", patient_id).single().execute()
        expires_at = user_response.data["demo_expires_at"]

        logger.info(f"✓ Demo user created: {patient_id} with {len(session_ids)} sessions")

        return DemoInitResponse(
            demo_token=demo_token,
            patient_id=patient_id,
            session_ids=[str(sid) for sid in session_ids],
            expires_at=expires_at,
            message=f"Demo initialized with {len(session_ids)} sessions. Data expires in 24 hours."
        )

    except Exception as e:
        logger.error(f"Demo initialization error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize demo: {str(e)}"
        )


@router.post("/reset", response_model=DemoResetResponse)
async def reset_demo(
    request: Request,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Reset demo user by deleting all sessions and re-seeding with fresh 10 sessions

    This endpoint:
    1. Validates demo token
    2. Deletes all existing sessions for demo user
    3. Calls seed function to recreate 10 sessions
    4. Extends expiry by 24 hours

    Returns:
        DemoResetResponse with new session IDs
    """
    demo_token = demo_user["demo_token"]
    patient_id = demo_user["id"]

    logger.info(f"Resetting demo for user: {patient_id}")

    try:
        # Delete existing sessions
        db.table("therapy_sessions").delete().eq("patient_id", patient_id).execute()

        # Re-seed sessions using SQL function
        response = db.rpc("seed_demo_user_sessions", {"p_demo_token": demo_token}).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset demo sessions"
            )

        result = response.data[0]
        session_ids = result["session_ids"]

        logger.info(f"✓ Demo reset complete: {len(session_ids)} sessions recreated")

        return DemoResetResponse(
            patient_id=patient_id,
            session_ids=[str(sid) for sid in session_ids],
            message=f"Demo reset with {len(session_ids)} fresh sessions"
        )

    except Exception as e:
        logger.error(f"Demo reset error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset demo: {str(e)}"
        )


@router.get("/status", response_model=DemoStatusResponse)
async def get_demo_status(
    request: Request,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Get current demo user status

    Returns:
        DemoStatusResponse with user info and session count
    """
    patient_id = demo_user["id"]

    # Count sessions
    session_response = db.table("therapy_sessions").select("id", count="exact").eq("patient_id", patient_id).execute()
    session_count = session_response.count or 0

    # Check if expired
    from datetime import datetime
    expires_at = datetime.fromisoformat(demo_user["demo_expires_at"].replace("Z", "+00:00"))
    is_expired = expires_at < datetime.now(expires_at.tzinfo)

    return DemoStatusResponse(
        demo_token=demo_user["demo_token"],
        patient_id=patient_id,
        session_count=session_count,
        created_at=demo_user["demo_created_at"],
        expires_at=demo_user["demo_expires_at"],
        is_expired=is_expired
    )
