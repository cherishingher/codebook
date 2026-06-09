from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(50))
    default_duration: Mapped[int] = mapped_column(default=90)
    default_hour_cost: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("1.00"))
    status: Mapped[str] = mapped_column(String(20), default="active")

