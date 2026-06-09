from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class DeviceHeartbeatRequest(BaseModel):
    device_code: str
    timestamp: datetime
    camera_status: str


class PunchEventRequest(BaseModel):
    device_code: str
    local_event_id: str
    student_id: int | None = None
    captured_at: datetime
    confidence: Decimal | None = Field(default=None, ge=0, le=1)
    snapshot_path: str | None = None

