"""
Demo Authentication Middleware
Handles demo token extraction from headers and user lookup
"""

from fastapi import Request, HTTPException
from typing import Optional
import logging
from supabase import Client

from app.database import get_supabase

logger = logging.getLogger(__name__)


async def get_demo_user(request: Request) -> Optional[dict]:
    """
    Extract demo token from request headers and fetch demo user

    Headers checked (in order):
    1. X-Demo-Token: <uuid>
    2. Authorization: Demo <uuid>

    Returns:
        Demo user dict if valid token, None otherwise
    """
    demo_token = None

    # Check X-Demo-Token header
    if "x-demo-token" in request.headers:
        demo_token = request.headers["x-demo-token"]

    # Check Authorization header (format: "Demo <uuid>")
    elif "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        if auth_header.startswith("Demo "):
            demo_token = auth_header[5:]  # Strip "Demo " prefix

    if not demo_token:
        return None

    # Validate token format (basic UUID check)
    try:
        from uuid import UUID
        UUID(demo_token)
    except ValueError:
        logger.warning(f"Invalid demo token format: {demo_token}")
        return None

    # Lookup demo user
    db: Client = get_supabase()
    try:
        response = db.table("users").select("*").eq("demo_token", demo_token).eq("is_demo", True).single().execute()

        if not response.data:
            logger.warning(f"Demo token not found: {demo_token}")
            return None

        demo_user = response.data

        # Check expiry
        from datetime import datetime
        if demo_user.get("demo_expires_at"):
            expiry = datetime.fromisoformat(demo_user["demo_expires_at"].replace("Z", "+00:00"))
            if expiry < datetime.now(expiry.tzinfo):
                logger.warning(f"Demo token expired: {demo_token}")
                return None

        return demo_user

    except Exception as e:
        logger.error(f"Error fetching demo user: {e}")
        return None


def require_demo_auth(request: Request) -> dict:
    """
    Dependency that requires valid demo token
    Raises 401 if token missing or invalid
    """
    import asyncio
    demo_user = asyncio.run(get_demo_user(request))

    if not demo_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing demo token. Initialize demo first."
        )

    return demo_user
