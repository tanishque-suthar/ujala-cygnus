import base64
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.document import Document
from app.models.patient import Patient
from app.models.scan_result import ScanResult
from app.schemas.models import ErrorResponse, ScreenResponse
from app.services.model_client import ModelClient, ModelServerError

router = APIRouter()

ALLOWED_MIMETYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def _ext(content_type: str) -> str:
    return ".jpg" if content_type == "image/jpeg" else ".png"


@router.post(
    "/screen",
    responses={
        200: {"model": ScreenResponse},
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
async def screen(
    request: Request,
    file: UploadFile | None = None,
    patient_name: str = Form(...),
    patient_id: str | None = Form(None),
):
    if file is None:
        return JSONResponse(status_code=400, content={"error": "No file provided"})

    if file.content_type not in ALLOWED_MIMETYPES:
        return JSONResponse(status_code=400, content={"error": "File must be JPEG or PNG"})

    body = await file.read()
    if len(body) > MAX_FILE_SIZE:
        return JSONResponse(status_code=413, content={"error": "File exceeds 10 MB limit"})

    client: ModelClient = request.app.state.model_client

    try:
        result = await client.predict(body, file.filename or "image")
    except ModelServerError:
        return JSONResponse(status_code=502, content={"error": "Model server unavailable"})

    prediction = result["prediction"]
    confidence = result["confidence"]
    heatmap_b64: str = result["heatmap_base64"]
    pathology_scores: dict = result.get("pathology_scores")
    op_threshs: dict = result.get("op_threshs")

    doc_id = str(uuid.uuid4())
    scan_id = str(uuid.uuid4())
    ext = _ext(file.content_type)
    image_abs = settings.images_dir / f"{doc_id}{ext}"
    heatmap_abs = settings.heatmaps_dir / f"{scan_id}.png"

    image_abs.write_bytes(body)
    heatmap_abs.write_bytes(base64.b64decode(heatmap_b64))

    async with AsyncSessionLocal() as session:
        async with session.begin():
            if patient_id:
                patient = await session.get(Patient, patient_id)
                if patient is None:
                    patient = Patient(id=str(uuid.uuid4()), name=patient_name)
                    session.add(patient)
            else:
                patient = Patient(id=str(uuid.uuid4()), name=patient_name)
                session.add(patient)

            document = Document(
                id=doc_id,
                patient_id=patient.id,
                document_type="xray",
                file_path=str(image_abs),
                filename=file.filename or f"xray{ext}",
            )
            session.add(document)

            scan_result_row = ScanResult(
                id=scan_id,
                document_id=doc_id,
                prediction=prediction,
                confidence=confidence,
                model_used=settings.active_model_name,
                heatmap_path=str(heatmap_abs),
            )
            session.add(scan_result_row)

    return ScreenResponse(
        prediction=prediction,
        confidence=confidence,
        model_used=settings.active_model_name,
        heatmap_base64=heatmap_b64,
        pathology_scores=pathology_scores,
        op_threshs=op_threshs,
        timestamp=datetime.now(timezone.utc),
        document_id=doc_id,
        patient_id=patient.id,
        patient_name=patient.name,
    )
