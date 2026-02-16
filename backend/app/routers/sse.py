"""
Server-Sent Events Router
Real-time pipeline event streaming
Updated: 2026-01-03 - Database-backed event queue for cross-process SSE
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.utils.pipeline_logger import PipelineLogger
from app.database import get_supabase
import asyncio
import json

router = APIRouter(prefix="/api/sse", tags=["sse"])

@router.options("/events/{patient_id}")
async def sse_preflight(patient_id: str):
    """Handle CORS preflight for SSE endpoint"""
    return {
        "message": "OK"
    }

async def event_generator(patient_id: str, request: Request):
    """
    SSE event generator - streams pipeline events from database

    Yields events in SSE format:
    data: {"event": "wave1_complete", "session_id": "...", ...}

    Updated: Reads from pipeline_events table to support cross-process communication
    """
    last_event_index = 0
    ping_counter = 0

    try:
        # Send initial connection event
        yield f"data: {json.dumps({'event': 'connected', 'patient_id': patient_id})}\n\n"

        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                print(f"[SSE] Client disconnected for patient {patient_id}", flush=True)
                break

            try:
                db = get_supabase()

                # Query unconsumed events for this patient
                query = (
                    db.table("pipeline_events")
                    .select("*")
                    .eq("patient_id", patient_id)
                    .eq("consumed", False)
                    .order("created_at", desc=False)
                )

                # If we've seen events before, only get newer ones
                if last_event_id:
                    query = query.gt("created_at", last_event_id)

                last_event_index = len(events)
            else:
                # Send keep-alive ping every 15 seconds to prevent Railway timeout
                ping_counter += 1
                if ping_counter >= 30:  # 30 * 0.5s = 15 seconds
                    yield ": keep-alive\n\n"
                    ping_counter = 0

            await asyncio.sleep(0.5)  # 500ms interval

    finally:
        print(f"[SSE] Connection closed for patient {patient_id}", flush=True)


@router.get("/events/{patient_id}")
async def stream_events(patient_id: str, request: Request):
    """
    SSE endpoint - connect to receive real-time pipeline events

    Usage:
        const eventSource = new EventSource('/api/sse/events/{patient_id}');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Pipeline event:', data);
        };

    Returns:
        StreamingResponse with text/event-stream content type
    """
    return StreamingResponse(
        event_generator(patient_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
