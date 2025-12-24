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

async def event_generator(patient_id: str, request: Request):
    """
    SSE event generator - streams pipeline events from database

    Yields events in SSE format:
    data: {"event": "wave1_complete", "session_id": "...", ...}

    Updated: Reads from pipeline_events table to support cross-process communication
    """
    last_event_id = None

    try:
        # Send initial connection event
        yield f"data: {json.dumps({'event': 'connected', 'patient_id': patient_id})}\n\n"
        print(f"[SSE] ✓ Connection confirmed by server", flush=True)

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

                response = query.execute()
                events = response.data or []

                # Send new events
                for event in events:
                    event_data = {
                        "patient_id": event["patient_id"],
                        "session_id": event.get("session_id"),
                        "session_date": event.get("session_date"),
                        "phase": event["phase"],
                        "event": event["event"],
                        "status": event["status"],
                        "message": event.get("message", ""),
                        "metadata": event.get("metadata", {})
                    }

                    yield f"data: {json.dumps(event_data)}\n\n"

                    # Mark event as consumed
                    db.table("pipeline_events").update({
                        "consumed": True
                    }).eq("id", event["id"]).execute()

                    # Update last seen event timestamp
                    last_event_id = event["created_at"]

                    print(f"[SSE] Sent event to patient {patient_id}: {event['phase']} {event['event']}", flush=True)

                # Keep-alive ping every iteration
                yield f": keepalive\n\n"

            except Exception as e:
                print(f"[SSE] Error querying events: {str(e)}", flush=True)
                # Continue polling despite errors

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
