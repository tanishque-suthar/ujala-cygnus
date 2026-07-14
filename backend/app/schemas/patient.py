from datetime import datetime

from pydantic import BaseModel


class PatientCreate(BaseModel):
    name: str


class PatientResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PatientListItem(BaseModel):
    id: str
    name: str
    created_at: datetime
    record_count: int

    model_config = {"from_attributes": True}
