from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.document import Document
from app.models.scan_result import ScanResult
from app.schemas.document import DocumentResponse

router = APIRouter(tags=["documents"])


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.scan_result))
        .options(selectinload(Document.report_result))
    )
    document = (await session.execute(stmt)).scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/heatmap/{scan_result_id}")
async def get_heatmap(
    scan_result_id: str,
    session: AsyncSession = Depends(get_session),
):
    scan_result = await session.get(ScanResult, scan_result_id)
    if scan_result is None or not scan_result.heatmap_path:
        raise HTTPException(status_code=404, detail="Heatmap not found")
    path = Path(scan_result.heatmap_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Heatmap file missing")
    return FileResponse(path, media_type="image/png")


@router.get("/image/{document_id}")
async def get_image(
    document_id: str,
    session: AsyncSession = Depends(get_session),
):
    document = await session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    path = Path(document.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file missing")
    suffix = path.suffix.lower()
    media_type = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
    return FileResponse(path, media_type=media_type)



@router.get("/patients/{patient_id}/documents", response_model=list[DocumentResponse])
async def list_patient_documents(
    patient_id: str,
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Document)
        .where(Document.patient_id == patient_id)
        .options(selectinload(Document.scan_result))
        .options(selectinload(Document.report_result))
        .order_by(Document.uploaded_at.desc())
    )
    docs = (await session.execute(stmt)).scalars().all()
    return list(docs)
