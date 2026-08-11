import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String, nullable=True)
    date_of_birth: Mapped[str | None] = mapped_column(String, nullable=True)
    contact: Mapped[str | None] = mapped_column(String, nullable=True)
    mrn: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    referring_physician: Mapped[str | None] = mapped_column(String, nullable=True)
    medical_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
