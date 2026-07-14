from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.document import Document
from app.models.patient import Patient
from app.schemas.document import DocumentResponse, PatientDetailResponse
from app.schemas.patient import PatientCreate, PatientListItem, PatientResponse

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(
    body: PatientCreate,
    session: AsyncSession = Depends(get_session),
):
    patient = Patient(name=body.name)
    session.add(patient)
    await session.commit()
    await session.refresh(patient)
    return patient


@router.get("", response_model=list[PatientListItem])
async def list_patients(session: AsyncSession = Depends(get_session)):
    count_sub = (
        select(Document.patient_id, func.count(Document.id).label("record_count"))
        .group_by(Document.patient_id)
        .subquery()
    )
    stmt = (
        select(Patient, func.coalesce(count_sub.c.record_count, 0).label("record_count"))
        .outerjoin(count_sub, Patient.id == count_sub.c.patient_id)
        .order_by(Patient.created_at.desc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        PatientListItem(
            id=patient.id,
            name=patient.name,
            created_at=patient.created_at,
            record_count=record_count,
        )
        for patient, record_count in rows
    ]


@router.get("/stats")
async def patient_stats(session: AsyncSession = Depends(get_session)):
    total_patients = (await session.execute(select(func.count(Patient.id)))).scalar_one()
    total_docs = (await session.execute(select(func.count(Document.id)))).scalar_one()
    return {"total_patients": total_patients, "total_documents": total_docs}


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient(
    patient_id: str,
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Patient)
        .where(Patient.id == patient_id)
        .options(selectinload(Patient.documents).selectinload(Document.scan_result))
    )
    patient = (await session.execute(stmt)).scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
