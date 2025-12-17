"""
Patient management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List

from app.database import get_db
from app.models.schemas import PatientCreate, PatientResponse
from app.models import db_models
from app.validators import (
    validate_email,
    validate_phone,
    validate_required_string,
    validate_therapist_exists,
    validate_positive_int
)

router = APIRouter()


@router.post("/", response_model=PatientResponse)
async def create_patient(
    patient: PatientCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new patient record with comprehensive validation.

    Adds a patient to the database and associates them with a therapist.
    The created patient can then have therapy sessions scheduled.

    Validation:
        - Name is required and must be 1-255 characters
        - Email format must be valid (RFC 5322 compliant)
        - Phone number must be valid international format
        - Therapist ID must exist and reference a user with role='therapist'

    Args:
        patient: PatientCreate schema with name, email, phone, and therapist_id
        db: AsyncSession database dependency

    Returns:
        PatientResponse: The newly created patient object with assigned UUID

    Raises:
        HTTPException 400: If validation fails (invalid email/phone format, missing name)
        HTTPException 404: If therapist_id not found
    """
    # Validate required fields
    validated_name = validate_required_string(
        patient.name,
        field_name="name",
        min_length=1,
        max_length=255
    )

    # Validate email format (optional field)
    validated_email = validate_email(patient.email, field_name="email")

    # Validate phone format (optional field)
    validated_phone = validate_phone(patient.phone, field_name="phone")

    # Validate therapist exists and has correct role
    therapist = await validate_therapist_exists(patient.therapist_id, db)

    # Create patient with validated data
    new_patient = db_models.Patient(
        name=validated_name,
        email=validated_email,
        phone=validated_phone,
        therapist_id=therapist.id
    )

    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)

    return PatientResponse.model_validate(new_patient)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a patient record by ID.

    Args:
        patient_id: UUID of the patient to retrieve
        db: AsyncSession database dependency

    Returns:
        PatientResponse: Patient object with all fields

    Raises:
        HTTPException 404: If patient with given ID not found
    """
    result = await db.execute(
        select(db_models.Patient).where(db_models.Patient.id == patient_id)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(404, f"Patient {patient_id} not found")

    return PatientResponse.model_validate(patient)


@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    therapist_id: UUID = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all patients with optional filtering by therapist.

    Retrieves patient records ordered by creation date (newest first).
    Can be filtered to show only patients assigned to a specific therapist.

    Validation:
        - limit must be between 1 and 1000

    Args:
        therapist_id: Optional UUID to filter patients by assigned therapist
        limit: Maximum number of results to return (default 100)
        db: AsyncSession database dependency

    Returns:
        List[PatientResponse]: List of patient records matching filters

    Raises:
        HTTPException 400: If limit is invalid

    Query Examples:
        GET /patients - all patients in database
        GET /patients?therapist_id=<uuid> - all patients for a therapist
        GET /patients?therapist_id=<uuid>&limit=25 - paginated results
    """
    # Validate limit parameter
    validated_limit = validate_positive_int(
        limit,
        field_name="limit",
        max_value=1000
    )

    query = select(db_models.Patient).order_by(db_models.Patient.created_at.desc())

    if therapist_id:
        # Validate therapist exists (optional: only validate if filtering)
        await validate_therapist_exists(therapist_id, db)
        query = query.where(db_models.Patient.therapist_id == therapist_id)

    query = query.limit(validated_limit)

    result = await db.execute(query)
    patients = result.scalars().all()

    return [PatientResponse.model_validate(p) for p in patients]
