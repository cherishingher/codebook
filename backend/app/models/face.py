from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class FaceProfile(TimestampMixin, Base):
    __tablename__ = "face_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    feature_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    feature_version: Mapped[str] = mapped_column(String(50), nullable=False)
    enrolled_image_path: Mapped[str | None] = mapped_column(String)
    consent_status: Mapped[str] = mapped_column(String(30), default="pending")
    status: Mapped[str] = mapped_column(String(20), default="active")
    enrolled_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

