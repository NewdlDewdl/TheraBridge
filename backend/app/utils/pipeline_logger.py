"""
Pipeline Logger - Granular logging for demo pipeline
Supports stdout, file output, and SSE event emission
Updated: 2026-01-03 - Database-backed event queue for cross-process SSE
"""

import logging
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

# Log event types
class LogPhase(str, Enum):
    TRANSCRIPT = "TRANSCRIPT"
    WAVE1 = "WAVE1"
    WAVE2 = "WAVE2"

class LogEvent(str, Enum):
    START = "START"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    FILE_LOAD = "FILE_LOAD"
    DB_UPDATE = "DB_UPDATE"
    MOOD_ANALYSIS = "MOOD_ANALYSIS"
    TOPIC_EXTRACTION = "TOPIC_EXTRACTION"
    BREAKTHROUGH_DETECTION = "BREAKTHROUGH_DETECTION"
    DEEP_ANALYSIS = "DEEP_ANALYSIS"
    PROSE_GENERATION = "PROSE_GENERATION"

# Global event queue for SSE (in-memory)
_event_queue: Dict[str, list] = {}

class PipelineLogger:
    """Enhanced logger with structured output and event emission"""

    def __init__(self, patient_id: str, phase: LogPhase):
        self.patient_id = patient_id
        self.phase = phase
        self.logger = logging.getLogger(f"pipeline.{phase.value}")

        # Ensure log directory exists
        self.log_dir = Path(__file__).parent.parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # Create patient-specific log file
        self.log_file = self.log_dir / f"pipeline_{patient_id}.log"

        # Initialize event queue for this patient
        if patient_id not in _event_queue:
            _event_queue[patient_id] = []

    def log_event(
        self,
        event: LogEvent,
        session_id: Optional[str] = None,
        session_date: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ):
        """Log a structured event with timestamp"""

        timestamp = datetime.utcnow()

        # Build structured log entry
        log_entry = {
            "timestamp": timestamp.isoformat() + "Z",
            "patient_id": self.patient_id,
            "phase": self.phase.value,
            "event": event.value,
            "status": status,
        }

        if session_id:
            log_entry["session_id"] = session_id
        if session_date:
            log_entry["session_date"] = session_date
        if duration_ms is not None:
            log_entry["duration_ms"] = round(duration_ms, 2)
        if details:
            log_entry["details"] = details

        # Format for human readability (stdout)
        session_info = f"[{session_date}]" if session_date else ""
        duration_info = f"({duration_ms:.0f}ms)" if duration_ms else ""
        details_info = f" {json.dumps(details)}" if details else ""

        log_message = (
            f"[{self.phase.value}] {session_info} "
            f"{event.value} {status.upper()} {duration_info}{details_info}"
        )

        # Log to stdout (for Railway dashboard)
        if status == "failed":
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)

        # Write to file (structured JSON)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Write to database (with in-memory fallback)
        self._write_event_to_database(log_entry)

    def _write_event_to_database(self, log_entry: dict):
        """Write event to database with retry logic and in-memory fallback"""
        retry_mode = os.getenv("PIPELINE_EVENT_RETRY_MODE", "production")
        max_retries = 3 if retry_mode == "development" else 0

        success = False
        for attempt in range(max_retries + 1):
            try:
                from app.database import get_supabase
                db = get_supabase()

                # Insert event into pipeline_events table
                response = db.table("pipeline_events").insert({
                    "patient_id": log_entry["patient_id"],
                    "session_id": log_entry.get("session_id"),
                    "session_date": log_entry.get("session_date"),
                    "phase": log_entry["phase"],
                    "event": log_entry["event"],
                    "status": log_entry["status"],
                    "message": "",  # Optional message field
                    "metadata": log_entry.get("details", {}),
                    "consumed": False
                }).execute()

                if response.data:
                    print(f"[PipelineLogger] ✓ Event logged to DB: {log_entry['phase']} {log_entry['event']}", flush=True)
                    success = True
                    break
                else:
                    print(f"[PipelineLogger] DB insert returned no data (attempt {attempt + 1}/{max_retries + 1})", flush=True)

            except Exception as e:
                print(f"[PipelineLogger] DB write error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}", flush=True)

                if attempt < max_retries:
                    # Exponential backoff: 0.1s, 0.2s, 0.4s
                    wait_time = 0.1 * (2 ** attempt)
                    time.sleep(wait_time)

        # Fallback to in-memory queue if database write failed
        if not success:
            print(f"[PipelineLogger] ⚠️  Using in-memory fallback for event", flush=True)
            _event_queue[self.patient_id].append(log_entry)

    @staticmethod
    def get_events(patient_id: str) -> list:
        """Get all events for a patient (for SSE streaming)"""
        return _event_queue.get(patient_id, [])

    @staticmethod
    def clear_events(patient_id: str):
        """Clear event queue after SSE client disconnects"""
        if patient_id in _event_queue:
            _event_queue[patient_id] = []
