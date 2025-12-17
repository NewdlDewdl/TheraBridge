"""
Session management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from typing import List, Optional
import os
import shutil
from pathlib import Path
import asyncio
import hashlib
import logging

from app.database import get_db
from app.models.schemas import (
    SessionCreate, SessionResponse, SessionStatus,
    ExtractedNotes, ExtractNotesResponse
)
from app.models import db_models
from app.services.note_extraction import get_extraction_service, NoteExtractionService
from app.services.transcription import transcribe_audio_file
from app.validators import (
    sanitize_filename,
    validate_audio_file_header,
    validate_patient_exists,
    validate_session_exists,
    validate_positive_int
)
from app.middleware.rate_limit import limiter

# Configure logger for upload operations
logger = logging.getLogger(__name__)

router = APIRouter()

# File upload configuration
UPLOAD_DIR = Path("uploads/audio")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_AUDIO_MIME_TYPES = {
    "audio/mpeg",      # .mp3
    "audio/wav",       # .wav
    "audio/x-wav",     # .wav (alternative)
    "audio/mp4",       # .m4a
    "audio/mpeg4",     # .m4a (alternative)
    "video/mp4",       # .mp4
    "audio/mpg",       # .mpeg
    "audio/mpeg3",     # .mpeg (alternative)
    "audio/x-mpeg",    # .mpeg (alternative)
    "audio/webm",      # .webm
    "video/webm"       # .webm (alternative)
}
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}


async def validate_audio_upload(file: UploadFile) -> None:
    """
    Validate audio file for upload.

    Checks:
    - File size does not exceed MAX_FILE_SIZE
    - File extension is in ALLOWED_EXTENSIONS
    - MIME type is audio/* or video/* (for container formats)

    Raises HTTPException with descriptive error message if validation fails.
    """
    # Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not supported. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Validate MIME type
    if file.content_type:
        if not (file.content_type.startswith("audio/") or file.content_type.startswith("video/")):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid MIME type: {file.content_type}. Only audio files are accepted."
            )
        if file.content_type not in ALLOWED_AUDIO_MIME_TYPES:
            raise HTTPException(
                status_code=415,  # 415 Unsupported Media Type
                detail=f"MIME type '{file.content_type}' not supported. Allowed: audio/mpeg, audio/wav, audio/mp4, audio/webm, etc."
            )

    # Validate file size
    # Note: file.size is set for in-memory files; for streamed files, we validate during write
    if file.size and file.size > MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
        file_size_mb = file.size / (1024 * 1024)
        raise HTTPException(
            status_code=413,  # 413 Payload Too Large
            detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb:.0f}MB)"
        )


async def process_audio_pipeline(
    session_id: UUID,
    audio_path: str,
    db: AsyncSession
):
    """
    Background task to orchestrate audio processing pipeline.

    Executes the complete workflow: transcription -> note extraction -> database update.
    Updates session status at each stage and handles errors gracefully.

    Args:
        session_id: UUID of the session being processed
        audio_path: Absolute file system path to the audio file
        db: AsyncSession database connection for updates

    Processing Stages:
        1. Transcribing: Convert audio to text with timestamps
        2. Transcribed: Save transcript and segments to database
        3. Extracting Notes: Generate structured clinical notes from transcript
        4. Processed: Save extracted notes and update final status
        5. Failed: Capture error message if any stage fails

    Returns:
        None (updates database and status only)
    """
    try:
        # Update status: transcribing
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.transcribing.value)
        )
        await db.commit()

        # Step 1: Transcribe audio
        logger.info("Starting transcription", extra={"session_id": str(session_id)})
        transcript_result = await transcribe_audio_file(audio_path)

        # Save transcript to database
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                transcript_text=transcript_result["full_text"],
                transcript_segments=transcript_result["segments"],
                duration_seconds=int(transcript_result.get("duration", 0)),
                status=SessionStatus.transcribed.value
            )
        )
        await db.commit()

        # Step 2: Extract notes
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.extracting_notes.value)
        )
        await db.commit()

        logger.info("Starting note extraction", extra={"session_id": str(session_id)})
        extraction_service = get_extraction_service()
        notes = await extraction_service.extract_notes_from_transcript(
            transcript=transcript_result["full_text"],
            segments=transcript_result.get("segments")
        )

        # Save extracted notes
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                extracted_notes=notes.model_dump(),
                therapist_summary=notes.therapist_notes,
                patient_summary=notes.patient_summary,
                risk_flags=[flag.model_dump() for flag in notes.risk_flags],
                status=SessionStatus.processed.value
            )
        )
        await db.commit()

        logger.info("Session processing completed", extra={"session_id": str(session_id)})

        # Cleanup audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.debug("Audio file cleaned up", extra={"audio_path": audio_path})

    except Exception as e:
        logger.error("Pipeline processing failed", extra={"session_id": str(session_id), "error": str(e)}, exc_info=True)

        # Update status to failed
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                status=SessionStatus.failed.value,
                error_message=str(e)
            )
        )
        await db.commit()


@router.post("/upload", response_model=SessionResponse)
@limiter.limit("10/hour")
async def upload_audio_session(
    request: Request,
    patient_id: UUID,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an audio file and create a new therapy session record.

    Creates a session in the database and begins background processing (transcription
    and note extraction). Returns immediately with status="uploading"; client can poll
    the session endpoint to track progress.

    Rate Limit:
        - 10 uploads per hour per IP address
        - Prevents API quota exhaustion from excessive processing

    Validation:
        - Patient ID must exist in database
        - File size must not exceed 500MB
        - File extension must be in ALLOWED_EXTENSIONS
        - MIME type must be audio/* or video/* (for container formats)
        - File header (magic bytes) must match expected audio format
        - File must be at least 1KB in size

    Args:
        patient_id: UUID of the patient associated with this session
        file: Audio file upload (UploadFile from form-data)
        background_tasks: FastAPI BackgroundTasks for async processing
        db: AsyncSession database dependency

    Returns:
        SessionResponse: Newly created session with status="uploading"

    Raises:
        HTTPException 400: Invalid filename, unsupported extension, invalid MIME type, or file too small
        HTTPException 404: Patient ID not found
        HTTPException 413: File size exceeds 500MB
        HTTPException 415: Unsupported MIME type or file header doesn't match audio format
        HTTPException 429: Rate limit exceeded (too many uploads)
        HTTPException 500: No therapist found or file save failed
    """
    # Validate file early before database operations
    await validate_audio_upload(file)

    # Validate patient exists in database (prevents orphaned sessions)
    patient = await validate_patient_exists(patient_id, db)
    logger.info(f"[Upload] Validated patient: {patient.name} (ID: {patient_id})")

    # Get therapist (for MVP, use the seeded therapist)
    therapist_result = await db.execute(
        select(db_models.User).where(db_models.User.role == "therapist").limit(1)
    )
    therapist = therapist_result.scalar_one_or_none()
    if not therapist:
        raise HTTPException(500, "No therapist found in database")

    # Create session in database
    from datetime import datetime

    new_session = db_models.Session(
        patient_id=patient.id,
        therapist_id=therapist.id,
        session_date=datetime.utcnow(),
        audio_filename=file.filename,
        status=SessionStatus.uploading.value
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    # Save audio file with enhanced streaming, progress tracking, and checksum verification
    file_path = UPLOAD_DIR / f"{new_session.id}{Path(file.filename).suffix.lower()}"
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")

    try:
        # Write file with streaming size validation, progress tracking, and checksum
        bytes_written = 0
        chunk_count = 0
        sha256_hash = hashlib.sha256()
        chunk_size = 1024 * 1024  # 1MB chunks

        logger.info(f"[Upload] Starting upload for session {new_session.id}: {file.filename}")

        with open(temp_path, "wb") as buffer:
            while True:
                try:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break

                    chunk_count += 1
                    bytes_written += len(chunk)

                    # Check file size during write (runtime validation for streamed uploads)
                    if bytes_written > MAX_FILE_SIZE:
                        buffer.close()
                        temp_path.unlink(missing_ok=True)
                        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
                        file_size_mb = bytes_written / (1024 * 1024)
                        logger.warning(
                            f"[Upload] File size exceeded: {file_size_mb:.1f}MB > {max_size_mb:.0f}MB"
                        )
                        raise HTTPException(
                            status_code=413,
                            detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb:.0f}MB)"
                        )

                    # Write chunk and update checksum
                    buffer.write(chunk)
                    sha256_hash.update(chunk)

                    # Log progress every 50MB
                    if bytes_written % (50 * 1024 * 1024) < chunk_size:
                        progress_mb = bytes_written / (1024 * 1024)
                        logger.info(f"[Upload] Progress: {progress_mb:.1f}MB uploaded")

                except asyncio.TimeoutError:
                    buffer.close()
                    temp_path.unlink(missing_ok=True)
                    logger.error(f"[Upload] Timeout reading chunk {chunk_count}")
                    raise HTTPException(
                        status_code=408,
                        detail="Upload timeout - connection lost during file transfer"
                    )
                except Exception as chunk_error:
                    buffer.close()
                    temp_path.unlink(missing_ok=True)
                    logger.error(f"[Upload] Error reading chunk {chunk_count}: {str(chunk_error)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Upload failed during chunk {chunk_count}: {str(chunk_error)}"
                    )

        # Verify minimum file size (at least 1KB to ensure valid audio)
        if bytes_written < 1024:
            temp_path.unlink(missing_ok=True)
            logger.warning(f"[Upload] File too small: {bytes_written} bytes")
            raise HTTPException(
                status_code=400,
                detail=f"File too small ({bytes_written} bytes). Audio file must be at least 1KB."
            )

        # Move temp file to final location (atomic operation)
        temp_path.rename(file_path)

        # Validate file header (magic bytes) to ensure it's actually an audio file
        # This prevents attacks where malicious files are renamed with audio extensions
        try:
            detected_mime_type = validate_audio_file_header(file_path)
            logger.info(f"[Upload] File header validated: {detected_mime_type}")
        except HTTPException as header_error:
            # File header validation failed - delete the file and fail the upload
            file_path.unlink(missing_ok=True)
            logger.error(f"[Upload] File header validation failed: {header_error.detail}")
            raise

        file_checksum = sha256_hash.hexdigest()
        file_size_mb = bytes_written / (1024 * 1024)

        logger.info(
            "Audio file saved and validated",
            extra={
                "session_id": str(new_session.id),
                "file_size_mb": round(file_size_mb, 1),
                "file_path": str(file_path),
                "file_checksum": file_checksum,
                "chunk_count": chunk_count,
                "mime_type": detected_mime_type
            }
        )

        # Update session with file path
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == new_session.id)
            .values(audio_url=str(file_path))
        )
        await db.commit()

        # Start background processing
        background_tasks.add_task(
            process_audio_pipeline,
            session_id=new_session.id,
            audio_path=str(file_path),
            db=db
        )

        return SessionResponse.model_validate(new_session)

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, size limits, etc.)
        # Clean up any partial uploads
        temp_path.unlink(missing_ok=True)
        file_path.unlink(missing_ok=True)

        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == new_session.id)
            .values(
                status=SessionStatus.failed.value,
                error_message="Upload validation failed"
            )
        )
        await db.commit()
        raise

    except Exception as e:
        # Clean up on unexpected error
        logger.error(f"[Upload] Unexpected error for session {new_session.id}: {str(e)}")
        temp_path.unlink(missing_ok=True)
        file_path.unlink(missing_ok=True)

        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == new_session.id)
            .values(
                status=SessionStatus.failed.value,
                error_message=f"Upload failed: {str(e)}"
            )
        )
        await db.commit()

        raise HTTPException(500, f"Failed to save audio file: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a complete session record by ID.

    Fetches the full session data including transcript, extracted notes,
    and processing status from the database.

    Args:
        session_id: UUID of the session to retrieve
        db: AsyncSession database dependency

    Returns:
        SessionResponse: Complete session object with all data

    Raises:
        HTTPException 404: If session with given ID not found
    """
    result = await db.execute(
        select(db_models.Session).where(db_models.Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    return SessionResponse.model_validate(session)


@router.get("/{session_id}/notes", response_model=ExtractedNotes)
async def get_session_notes(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve extracted clinical notes for a specific session.

    Returns only the structured note extraction (without raw transcript).
    Useful for reading notes without the full session data.

    Args:
        session_id: UUID of the session
        db: AsyncSession database dependency

    Returns:
        ExtractedNotes: Structured clinical notes object

    Raises:
        HTTPException 404: If session not found or notes not yet extracted
    """
    result = await db.execute(
        select(db_models.Session).where(db_models.Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    if not session.extracted_notes:
        raise HTTPException(404, "Notes not yet extracted for this session")

    return ExtractedNotes(**session.extracted_notes)


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    patient_id: Optional[UUID] = None,
    status: Optional[SessionStatus] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    List therapy sessions with optional filtering.

    Retrieves sessions ordered by date (newest first) with optional
    filtering by patient and processing status.

    Validation:
        - limit must be between 1 and 1000
        - patient_id must exist if provided

    Args:
        patient_id: Optional UUID to filter sessions by patient
        status: Optional SessionStatus to filter by processing status
        limit: Maximum number of results to return (default 50, max 1000)
        db: AsyncSession database dependency

    Returns:
        List[SessionResponse]: List of session records matching filters

    Raises:
        HTTPException 400: If limit is invalid
        HTTPException 404: If patient_id not found

    Query Examples:
        GET /sessions?patient_id=<uuid> - all sessions for a patient
        GET /sessions?status=processed - only completed sessions
        GET /sessions?patient_id=<uuid>&status=failed - failed sessions for a patient
    """
    # Validate limit parameter
    validated_limit = validate_positive_int(
        limit,
        field_name="limit",
        max_value=1000
    )

    query = select(db_models.Session).order_by(db_models.Session.session_date.desc())

    if patient_id:
        # Validate patient exists when filtering
        await validate_patient_exists(patient_id, db)
        query = query.where(db_models.Session.patient_id == patient_id)

    if status:
        query = query.where(db_models.Session.status == status.value)

    query = query.limit(validated_limit)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [SessionResponse.model_validate(s) for s in sessions]


@router.post("/{session_id}/extract-notes", response_model=ExtractNotesResponse)
@limiter.limit("20/hour")
async def manually_extract_notes(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    extraction_service: NoteExtractionService = Depends(get_extraction_service)
):
    """
    Manually trigger note extraction for a transcribed session.

    Useful for re-processing a session or if automatic extraction failed.
    Session must have transcript_text before extraction is possible.

    Rate Limit:
        - 20 extractions per hour per IP address
        - Prevents OpenAI API quota exhaustion from excessive re-processing

    Args:
        session_id: UUID of session to extract notes from
        db: AsyncSession database dependency
        extraction_service: NoteExtractionService injected dependency

    Returns:
        ExtractNotesResponse: Extracted notes and processing time

    Raises:
        HTTPException 404: If session not found
        HTTPException 400: If session has no transcript_text yet
        HTTPException 429: Rate limit exceeded (too many extractions)
    """
    result = await db.execute(
        select(db_models.Session).where(db_models.Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    if not session.transcript_text:
        raise HTTPException(400, "Session must be transcribed before extracting notes")

    # Extract notes
    import time
    start_time = time.time()

    notes = await extraction_service.extract_notes_from_transcript(
        transcript=session.transcript_text,
        segments=session.transcript_segments
    )

    processing_time = time.time() - start_time

    # Save to database
    await db.execute(
        update(db_models.Session)
        .where(db_models.Session.id == session_id)
        .values(
            extracted_notes=notes.model_dump(),
            therapist_summary=notes.therapist_notes,
            patient_summary=notes.patient_summary,
            risk_flags=[flag.model_dump() for flag in notes.risk_flags],
            status=SessionStatus.processed.value
        )
    )
    await db.commit()

    return ExtractNotesResponse(
        extracted_notes=notes,
        processing_time=processing_time
    )
