from datetime import datetime

from pydantic import BaseModel


class ScanResultResponse(BaseModel):
    id: str
    prediction: str
    confidence: float
    model_used: str
    pathology_scores: dict[str, float] | None = None
    op_threshs: dict[str, float] | None = None
    analyzed_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: str
    patient_id: str
    document_type: str
    filename: str
    uploaded_at: datetime
    scan_result: ScanResultResponse | None = None

    model_config = {"from_attributes": True}


class PatientDetailResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    documents: list[DocumentResponse]

    model_config = {"from_attributes": True}
