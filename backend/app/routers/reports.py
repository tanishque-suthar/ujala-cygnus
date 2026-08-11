import io
import shutil
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.document import Document
from app.models.patient import Patient
from app.models.report_result import ReportResult
from app.schemas.report import OCRUploadResponse, ReportConfirmRequest, ReportConfirmResponse
from app.config import settings

router = APIRouter(prefix="/reports", tags=["reports"])

ALLOWED_MIMETYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

@router.post("/upload", response_model=OCRUploadResponse)
async def upload_report(request: Request, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
    
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    temp_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix
    temp_filename = f"{temp_id}{ext}"
    temp_path = settings.reports_dir / "temp" / temp_filename
    
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_path, "wb") as f:
        f.write(file_bytes)
        
    ocr_service = request.app.state.ocr_service
    page_count = 1
    
    if file.content_type == "application/pdf":
        raw_text, page_count = ocr_service.extract_from_pdf(file_bytes)
    else:
        image = Image.open(io.BytesIO(file_bytes))
        raw_text = ocr_service.extract_from_image(image)
        
    extracted_fields = ocr_service.extract_fields(raw_text)
    
    return OCRUploadResponse(
        temp_id=temp_id,
        filename=file.filename,
        extracted_patient_name=extracted_fields.pop("patient_name", None),
        extracted_report_date=extracted_fields.pop("report_date", None),
        extracted_report_type=None,
        extracted_doctor_name=extracted_fields.pop("doctor_name", None),
        extracted_facility_name=extracted_fields.pop("facility_name", None),
        extracted_fields=extracted_fields,
        raw_text=raw_text,
        page_count=page_count
    )

@router.post("/confirm", response_model=ReportConfirmResponse)
async def confirm_report(body: ReportConfirmRequest, db: AsyncSession = Depends(get_session)):
    temp_files = list((settings.reports_dir / "temp").glob(f"{body.temp_id}.*"))
    if not temp_files:
        raise HTTPException(status_code=404, detail="Temporary file not found")
        
    temp_path = temp_files[0]
    
    if body.patient_id:
        patient = (await db.execute(select(Patient).where(Patient.id == body.patient_id))).scalar_one_or_none()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
    else:
        patient = Patient(
            name=body.patient_name,
            age=body.patient_age,
            sex=body.patient_sex,
            date_of_birth=body.patient_dob,
            contact=body.patient_contact,
            mrn=body.patient_mrn,
            referring_physician=body.referring_physician
        )
        db.add(patient)
        await db.flush()
        
    document = Document(
        patient_id=patient.id,
        document_type="report",
        filename=temp_path.name,
        file_path=""  # Will update below
    )
    db.add(document)
    await db.flush()
    
    final_filename = f"{document.id}{temp_path.suffix}"
    final_path = settings.reports_dir / final_filename
    shutil.move(str(temp_path), str(final_path))
    
    document.file_path = f"reports/{final_filename}"
    
    report_result = ReportResult(
        document_id=document.id,
        report_type=body.report_type,
        report_date=body.report_date,
        raw_text=body.raw_text,
        extracted_fields=body.extracted_fields,
        doctor_name=body.doctor_name,
        facility_name=body.facility_name
    )
    db.add(report_result)
    await db.commit()
    
    return ReportConfirmResponse(
        document_id=document.id,
        patient_id=patient.id,
        patient_name=patient.name,
        report_type=report_result.report_type,
        report_date=report_result.report_date,
        raw_text=report_result.raw_text or "",
        extracted_fields=report_result.extracted_fields,
        timestamp=datetime.now(timezone.utc)
    )

@router.get("/{document_id}/file")
async def get_report_file(document_id: str, db: AsyncSession = Depends(get_session)):
    document = (await db.execute(select(Document).where(Document.id == document_id, Document.document_type == "report"))).scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    file_path = Path(settings.uploads_dir) / document.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    return FileResponse(file_path)

