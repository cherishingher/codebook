from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Device(TimestampMixin, Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False, index=True)
    device_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str] = mapped_column(String(30), default="mac_mini")
    location_type: Mapped[str] = mapped_column(String(30), default="frontdesk")
    location_name: Mapped[str | None] = mapped_column(String(100))
    secret_hash: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DeviceNonce(TimestampMixin, Base):
    __tablename__ = "device_nonces"
    __table_args__ = (UniqueConstraint("device_id", "nonce", name="uq_device_nonce"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False, index=True)
    nonce: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
