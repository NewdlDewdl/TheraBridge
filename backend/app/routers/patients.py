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

router = APIRouter()


@router.post("/", response_model=PatientResponse)
async def create_patient(
    patient: PatientCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new patient"""
    new_patient = db_models.Patient(
        name=patient.name,
        email=patient.email,
        phone=patient.phone,
        therapist_id=patient.therapist_id
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
    """Get patient by ID"""
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
    """List all patients"""
    query = select(db_models.Patient).order_by(db_models.Patient.created_at.desc())

    if therapist_id:
        query = query.where(db_models.Patient.therapist_id == therapist_id)

    query = query.limit(limit)

    result = await db.execute(query)
    patients = result.scalars().all()

    return [PatientResponse.model_validate(p) for p in patients]
