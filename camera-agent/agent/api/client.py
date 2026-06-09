from datetime import datetime
from decimal import Decimal
import base64

import httpx
import numpy as np

from agent.config import settings
from agent.face.types import FaceProfile


class ApiClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or settings.api_base_url

    def heartbeat(self, camera_status: str) -> dict:
        payload = {
            "device_code": settings.device_code,
            "timestamp": datetime.now().isoformat(),
            "camera_status": camera_status,
        }
        with httpx.Client(timeout=5) as client:
            response = client.post(f"{self.base_url}/device/heartbeat", json=payload)
            response.raise_for_status()
            return response.json()

    def upload_punch_event(
        self,
        *,
        local_event_id: str,
        student_id: int | None,
        captured_at: datetime,
        confidence: float | None,
        snapshot_path: str | None,
    ) -> dict:
        payload = {
            "device_code": settings.device_code,
            "local_event_id": local_event_id,
            "student_id": student_id,
            "captured_at": captured_at.isoformat(),
            "confidence": str(Decimal(str(confidence))) if confidence is not None else None,
            "snapshot_path": snapshot_path,
        }
        with httpx.Client(timeout=10) as client:
            response = client.post(f"{self.base_url}/device/punch-events", json=payload)
            response.raise_for_status()
            return response.json()

    def fetch_face_profiles(self, updated_after: str | None = None) -> list[FaceProfile]:
        params = {"device_code": settings.device_code}
        if updated_after:
            params["updated_after"] = updated_after
        with httpx.Client(timeout=20) as client:
            response = client.get(f"{self.base_url}/device/face-profiles", params=params)
            response.raise_for_status()
            items = response.json().get("items", [])
        profiles: list[FaceProfile] = []
        for item in items:
            raw = base64.b64decode(item["feature_data"])
            feature = np.frombuffer(raw, dtype=np.float32)
            profiles.append(FaceProfile(student_id=item["student_id"], feature=feature))
        return profiles
