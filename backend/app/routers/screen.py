from datetime import datetime, timezone

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas.models import ErrorResponse, ScreenResponse
from app.services.model_client import ModelClient, ModelServerError

router = APIRouter()

ALLOWED_MIMETYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def _map_priority(prediction: str, confidence: float) -> str:
    if prediction == "pneumonia":
        if confidence >= 0.85:
            return "high"
        if confidence >= 0.6:
            return "moderate"
    return "low"


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
    priority = _map_priority(prediction, confidence)

    return ScreenResponse(
        prediction=prediction,
        confidence=confidence,
        priority=priority,
        model_used=settings.active_model_name,
        heatmap_base64=result["heatmap_base64"],
        timestamp=datetime.now(timezone.utc),
    )
