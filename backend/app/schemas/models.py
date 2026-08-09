from datetime import datetime

from pydantic import BaseModel


class ScreenResponse(BaseModel):
    prediction: str
    confidence: float
    model_used: str
    heatmap_base64: str
    pathology_scores: dict[str, float] | None = None
    op_threshs: dict[str, float] | None = None
    timestamp: datetime
    document_id: str
    patient_id: str
    patient_name: str


class HealthResponse(BaseModel):
    status: str
    model_server_reachable: bool


class ErrorResponse(BaseModel):
    error: str
