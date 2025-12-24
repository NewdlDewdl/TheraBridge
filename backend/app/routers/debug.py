"""
Debug endpoints for testing pipeline functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
import subprocess
import sys
import logging
from pathlib import Path

from app.database import get_db
from app.middleware.demo_auth import require_demo_auth

router = APIRouter(prefix="/api/debug", tags=["debug"])
logger = logging.getLogger(__name__)


@router.post("/populate-transcripts/{patient_id}")
async def debug_populate_transcripts(
    patient_id: str,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Synchronously populate transcripts for debugging
    Shows detailed error messages
    """
    try:
        # Get Python executable
        python_exe = sys.executable
        script_path = Path(__file__).parent.parent.parent / "scripts" / "seed_all_sessions.py"

        logger.info(f"Running transcript population for patient {patient_id}")
        logger.info(f"Python: {python_exe}")
        logger.info(f"Script: {script_path}")
        logger.info(f"Script exists: {script_path.exists()}")

        # Run synchronously to see errors
        result = subprocess.run(
            [python_exe, str(script_path), patient_id],
            capture_output=True,
            text=True,
            timeout=60
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "python_exe": python_exe,
            "script_path": str(script_path),
            "script_exists": script_path.exists()
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Script timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/check-paths")
async def debug_check_paths():
    """Check if required files and directories exist"""
    try:
        repo_root = Path(__file__).parent.parent.parent.parent
        mock_data_dir = repo_root / "mock-therapy-data" / "sessions"
        script_dir = repo_root / "backend" / "scripts"

        return {
            "repo_root": str(repo_root),
            "repo_root_exists": repo_root.exists(),
            "mock_data_dir": str(mock_data_dir),
            "mock_data_exists": mock_data_dir.exists(),
            "script_dir": str(script_dir),
            "script_dir_exists": script_dir.exists(),
            "session_files": list(mock_data_dir.glob("*.json")) if mock_data_dir.exists() else [],
            "cwd": str(Path.cwd())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
