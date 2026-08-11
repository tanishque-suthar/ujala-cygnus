from datetime import datetime

from pydantic import BaseModel


class PatientCreate(BaseModel):
    name: str
    age: int | None = None
    sex: str | None = None
    date_of_birth: str | None = None
    contact: str | None = None
    mrn: str | None = None
    referring_physician: str | None = None
    medical_history: str | None = None


class PatientResponse(BaseModel):
    id: str
    name: str
    age: int | None = None
    sex: str | None = None
    date_of_birth: str | None = None
    contact: str | None = None
    mrn: str | None = None
    referring_physician: str | None = None
    medical_history: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PatientListItem(BaseModel):
    id: str
    name: str
    created_at: datetime
    record_count: int

    model_config = {"from_attributes": True}
