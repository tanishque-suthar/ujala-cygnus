from datetime import datetime
from pydantic import BaseModel

class OCRUploadResponse(BaseModel):
    """Returned after OCR extraction, before user confirmation."""
    temp_id: str                          # temp file reference for confirm step
    filename: str
    extracted_patient_name: str | None = None
    extracted_report_date: str | None = None
    extracted_report_type: str | None = None
    extracted_doctor_name: str | None = None
    extracted_facility_name: str | None = None
    extracted_fields: dict[str, str] | None = None
    raw_text: str
    page_count: int = 1
    ocr_confidence: float | None = None

class ReportConfirmRequest(BaseModel):
    """User-verified fields sent back to persist."""
    temp_id: str
    patient_name: str
    patient_id: str | None = None        # link to existing patient, or create new
    report_type: str                      # "lab_panel" | "discharge_summary" | "referral_letter" | "other"
    report_date: str | None = None
    doctor_name: str | None = None
    facility_name: str | None = None
    extracted_fields: dict[str, str] | None = None
    raw_text: str
    # optional patient demographics for new patients
    patient_age: int | None = None
    patient_sex: str | None = None
    patient_dob: str | None = None
    patient_contact: str | None = None
    patient_mrn: str | None = None
    referring_physician: str | None = None

class ReportConfirmResponse(BaseModel):
    document_id: str
    patient_id: str
    patient_name: str
    report_type: str
    report_date: str | None = None
    raw_text: str
    extracted_fields: dict[str, str] | None = None
    timestamp: datetime

class ReportResultResponse(BaseModel):
    id: str
    report_type: str
    report_date: str | None = None
    raw_text: str | None = None
    extracted_fields: dict[str, str] | None = None
    doctor_name: str | None = None
    facility_name: str | None = None
    processed_at: datetime
    model_config = {"from_attributes": True}
