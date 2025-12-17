"""
Cleanup API Router

Endpoints for manual cleanup operations and cleanup status.

Security:
- All endpoints require authentication
- Admin/therapist role required for cleanup operations
- Dry-run mode available for testing
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.database import get_db
from app.services.cleanup import AudioCleanupService, CleanupConfig
from app.auth.dependencies import get_current_user
from app.models.schemas import UserRole
from app.models.db_models import User

logger = logging.getLogger(__name__)

router = APIRouter()


def require_admin_or_therapist(current_user: User = Depends(get_current_user)):
    """
    Dependency to ensure user has admin or therapist role

    Args:
        current_user: Current authenticated user

    Raises:
        HTTPException: If user doesn't have required role
    """
    if current_user.role not in [UserRole.THERAPIST, UserRole.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Only therapists and admins can perform cleanup operations",
        )
    return current_user


@router.post("/cleanup/orphaned-files")
async def cleanup_orphaned_files(
    dry_run: bool = Query(
        False, description="If true, only report what would be deleted without actually deleting"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_therapist),
):
    """
    Clean up orphaned audio files not referenced in database

    This endpoint finds audio files in the upload directory that are not
    referenced by any session in the database and deletes them if they're
    older than the configured retention period.

    **Security:** Requires therapist or admin role

    **Safety Features:**
    - Only deletes files older than configured retention period
    - Dry-run mode available for testing
    - Comprehensive logging of all operations

    **Parameters:**
    - `dry_run`: If true, only reports what would be deleted without actually deleting

    **Returns:**
    - Details of cleanup operation including files deleted and space freed
    """
    logger.info(
        f"Orphaned file cleanup requested by user {current_user.id} (dry_run={dry_run})"
    )

    try:
        cleanup_service = AudioCleanupService(db=db)
        result = await cleanup_service.cleanup_orphaned_files(dry_run=dry_run)

        return {
            "success": True,
            "message": "Orphaned file cleanup completed",
            "result": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Orphaned file cleanup failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Cleanup failed: {str(e)}"
        )


@router.post("/cleanup/failed-sessions")
async def cleanup_failed_sessions(
    dry_run: bool = Query(
        False, description="If true, only report what would be deleted without actually deleting"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_therapist),
):
    """
    Clean up audio files from failed sessions

    This endpoint finds sessions with status='failed' that are older than the
    configured retention period and deletes their associated audio files.

    **Security:** Requires therapist or admin role

    **Safety Features:**
    - Only deletes files from sessions older than configured retention period
    - Dry-run mode available for testing
    - Session records are preserved for audit trail

    **Parameters:**
    - `dry_run`: If true, only reports what would be deleted without actually deleting

    **Returns:**
    - Details of cleanup operation including sessions cleaned and space freed
    """
    logger.info(
        f"Failed session cleanup requested by user {current_user.id} (dry_run={dry_run})"
    )

    try:
        cleanup_service = AudioCleanupService(db=db)
        result = await cleanup_service.cleanup_failed_sessions(dry_run=dry_run)

        return {
            "success": True,
            "message": "Failed session cleanup completed",
            "result": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Failed session cleanup failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Cleanup failed: {str(e)}"
        )


@router.post("/cleanup/all")
async def cleanup_all(
    dry_run: bool = Query(
        False, description="If true, only report what would be deleted without actually deleting"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_therapist),
):
    """
    Run all cleanup operations

    This endpoint runs both orphaned file cleanup and failed session cleanup
    in a single operation.

    **Security:** Requires therapist or admin role

    **Safety Features:**
    - Only deletes files older than configured retention periods
    - Dry-run mode available for testing
    - Comprehensive logging and error reporting

    **Parameters:**
    - `dry_run`: If true, only reports what would be deleted without actually deleting

    **Returns:**
    - Combined details of all cleanup operations
    """
    logger.info(
        f"Full cleanup requested by user {current_user.id} (dry_run={dry_run})"
    )

    try:
        cleanup_service = AudioCleanupService(db=db)
        result = await cleanup_service.cleanup_all(dry_run=dry_run)

        return {
            "success": True,
            "message": "Full cleanup completed",
            "result": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Full cleanup failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/cleanup/config")
async def get_cleanup_config(
    current_user: User = Depends(require_admin_or_therapist),
):
    """
    Get current cleanup configuration

    Returns the current cleanup configuration including retention periods
    and upload directory settings.

    **Security:** Requires therapist or admin role

    **Returns:**
    - Current cleanup configuration settings
    """
    return {
        "failed_session_retention_days": CleanupConfig.FAILED_SESSION_RETENTION_DAYS,
        "orphaned_file_retention_hours": CleanupConfig.ORPHANED_FILE_RETENTION_HOURS,
        "upload_dir": CleanupConfig.UPLOAD_DIR,
        "auto_cleanup_on_startup": CleanupConfig.AUTO_CLEANUP_ON_STARTUP,
        "cleanup_schedule_hour": CleanupConfig.CLEANUP_SCHEDULE_HOUR,
    }


@router.get("/cleanup/status")
async def get_cleanup_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_therapist),
):
    """
    Get cleanup status and statistics

    Returns information about potential cleanup targets without performing
    any deletions. Useful for monitoring and planning cleanup operations.

    **Security:** Requires therapist or admin role

    **Returns:**
    - Statistics about orphaned files and failed sessions
    """
    try:
        cleanup_service = AudioCleanupService(db=db)

        # Run dry-run to get statistics
        result = await cleanup_service.cleanup_all(dry_run=True)

        return {
            "success": True,
            "message": "Cleanup status retrieved",
            "potential_cleanup": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Failed to get cleanup status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get cleanup status: {str(e)}"
        )
