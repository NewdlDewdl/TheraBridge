#!/usr/bin/env python3
"""
Seed Script: Populate All 10 Sessions with Transcripts
========================================================
Reads all 10 session JSON files from mock-therapy-data/sessions/
and populates the transcript field in the database.

This script should be run AFTER seed_demo_v4() creates 10 sessions.

Usage:
    python backend/scripts/seed_all_sessions.py <patient_id>

Example:
    python backend/scripts/seed_all_sessions.py 550e8400-e29b-41d4-a716-446655440000

Author: System
Date: 2025-12-23
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import os
import asyncio
from typing import Tuple, Dict, Any

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_supabase_admin
from app.utils.pipeline_logger import PipelineLogger, LogPhase, LogEvent


# Session file mapping (ordered by date)
SESSION_FILES = [
    ("session_01_crisis_intake.json", "2025-01-10"),
    ("session_02_emotional_regulation.json", "2025-01-17"),
    ("session_03_adhd_discovery.json", "2025-01-31"),
    ("session_04_medication_start.json", "2025-02-14"),
    ("session_05_family_conflict.json", "2025-02-28"),
    ("session_06_spring_break_hope.json", "2025-03-14"),
    ("session_07_dating_anxiety.json", "2025-04-04"),
    ("session_08_relationship_boundaries.json", "2025-04-18"),
    ("session_09_coming_out_preparation.json", "2025-05-02"),
    ("session_10_coming_out_aftermath.json", "2025-05-09"),
]


def load_transcript_from_file(filename: str) -> dict:
    """
    Load transcript JSON from mock-therapy-data/sessions/

    Args:
        filename: Name of JSON file (e.g., "session_01_crisis_intake.json")

    Returns:
        Dictionary with transcript segments and metadata
    """
    # Find the mock-therapy-data directory (now in backend/)
    backend_root = Path(__file__).parent.parent
    sessions_dir = backend_root / "mock-therapy-data" / "sessions"

    file_path = sessions_dir / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Transcript file not found: {file_path}")

    with open(file_path, "r") as f:
        data = json.load(f)

    return data


async def populate_session_transcript(
    patient_id: str,
    session_date: str,
    transcript_data: dict
) -> bool:
    """
    Update a session's transcript field in the database (async)

    Args:
        patient_id: UUID of the patient
        session_date: Date of session (YYYY-MM-DD)
        transcript_data: Full JSON data from transcript file

    Returns:
        True if successful, False otherwise
    """
    # Run database operation in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    def _update_db():
        db = get_supabase_admin()

        try:
            # Extract just the segments array (what we store in DB)
            segments = transcript_data.get("segments", [])

            # Also extract duration from metadata for accuracy
            duration_seconds = transcript_data.get("metadata", {}).get("duration", 3600)
            duration_minutes = int(duration_seconds / 60)

            # Update the session
            response = db.table("therapy_sessions").update({
                "transcript": segments,
                "duration_minutes": duration_minutes,
                "updated_at": datetime.now().isoformat()
            }).eq("patient_id", patient_id).eq("session_date", session_date).execute()

            if response.data:
                return True
            else:
                print(f"  ⚠️  No session found for date {session_date}")
                return False

        except Exception as e:
            print(f"  ❌ Error updating session {session_date}: {e}")
            return False

    return await loop.run_in_executor(None, _update_db)


async def process_single_session(
    patient_id: str,
    filename: str,
    session_date: str,
    index: int,
    total: int
) -> Tuple[bool, str]:
    """Process a single session file (async) with granular logging"""

    logger = PipelineLogger(patient_id, LogPhase.TRANSCRIPT)
    session_id = f"session_{session_date}"  # Temporary ID for logging

    try:
        # START event
        logger.log_event(
            LogEvent.START,
            session_id=session_id,
            session_date=session_date,
            details={"index": index, "total": total, "filename": filename}
        )

        # FILE_LOAD start
        load_start = datetime.now()
        loop = asyncio.get_event_loop()
        transcript_data = await loop.run_in_executor(
            None, load_transcript_from_file, filename
        )
        load_duration = (datetime.now() - load_start).total_seconds() * 1000

        segment_count = len(transcript_data.get("segments", []))
        duration = transcript_data.get("metadata", {}).get("duration", 0) / 60

        # FILE_LOAD complete
        logger.log_event(
            LogEvent.FILE_LOAD,
            session_id=session_id,
            session_date=session_date,
            duration_ms=load_duration,
            details={
                "segments": segment_count,
                "duration_minutes": round(duration, 1),
                "file_size_kb": round(len(json.dumps(transcript_data)) / 1024, 2)
            }
        )

        print(f"[{index}/{total}] ✓ Loaded {filename}: {segment_count} segments, {duration:.0f} min")

        # DB_UPDATE start
        db_start = datetime.now()
        if await populate_session_transcript(patient_id, session_date, transcript_data):
            db_duration = (datetime.now() - db_start).total_seconds() * 1000

            # DB_UPDATE complete
            logger.log_event(
                LogEvent.DB_UPDATE,
                session_id=session_id,
                session_date=session_date,
                duration_ms=db_duration
            )

            print(f"[{index}/{total}] ✓ Updated session {session_date}")

            # COMPLETE event
            total_duration = load_duration + db_duration
            logger.log_event(
                LogEvent.COMPLETE,
                session_id=session_id,
                session_date=session_date,
                duration_ms=total_duration
            )

            return (True, f"Success: {filename}")
        else:
            logger.log_event(
                LogEvent.FAILED,
                session_id=session_id,
                session_date=session_date,
                status="failed",
                details={"error": "No session found in database"}
            )
            return (False, f"Failed: No session found for {session_date}")

    except FileNotFoundError as e:
        logger.log_event(
            LogEvent.FAILED,
            session_id=session_id,
            session_date=session_date,
            status="failed",
            details={"error": f"File not found: {filename}"}
        )
        return (False, f"File not found: {filename}")
    except Exception as e:
        logger.log_event(
            LogEvent.FAILED,
            session_id=session_id,
            session_date=session_date,
            status="failed",
            details={"error": str(e)}
        )
        return (False, f"Error processing {filename}: {e}")


async def seed_all_sessions_async(patient_id: str):
    """
    Main async function: Load all transcripts and populate database in parallel

    Args:
        patient_id: UUID of the patient to populate sessions for

    Returns:
        0 if all successful, 1 if any failures
    """
    print("=" * 70)
    print("🌱 Seeding All Sessions with Transcripts (Parallel)")
    print("=" * 70)
    print(f"Patient ID: {patient_id}")
    print(f"Total sessions: {len(SESSION_FILES)}")
    print(f"Concurrency: {len(SESSION_FILES)} parallel operations")
    print()

    # Create tasks for all sessions (dynamic parallelization)
    tasks = [
        process_single_session(patient_id, filename, session_date, i, len(SESSION_FILES))
        for i, (filename, session_date) in enumerate(SESSION_FILES, 1)
    ]

    # Run all tasks concurrently
    print(f"🚀 Starting parallel processing of {len(tasks)} sessions...")
    print()
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count successes and failures
    success_count = sum(1 for r in results if isinstance(r, tuple) and r[0])
    fail_count = len(results) - success_count

    # Summary
    print()
    print("=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print(f"✓ Success: {success_count}/{len(SESSION_FILES)} sessions")
    print(f"✗ Failed:  {fail_count}/{len(SESSION_FILES)} sessions")
    print()

    if success_count == len(SESSION_FILES):
        print("🎉 All sessions populated successfully!")
        return 0
    else:
        print("⚠️  Some sessions failed. Check errors above.")
        return 1


def seed_all_sessions(patient_id: str):
    """
    Synchronous wrapper for async seed function (for backward compatibility)

    Args:
        patient_id: UUID of the patient to populate sessions for

    Returns:
        0 if all successful, 1 if any failures
    """
    return asyncio.run(seed_all_sessions_async(patient_id))


def main():
    """CLI entry point"""
    if len(sys.argv) != 2:
        print("Usage: python seed_all_sessions.py <patient_id>")
        print()
        print("Example:")
        print("  python seed_all_sessions.py 550e8400-e29b-41d4-a716-446655440000")
        sys.exit(1)

    patient_id = sys.argv[1]

    # Validate UUID format
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    if not uuid_pattern.match(patient_id):
        print(f"❌ Invalid UUID format: {patient_id}")
        sys.exit(1)

    # Run seeding
    exit_code = seed_all_sessions(patient_id)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
