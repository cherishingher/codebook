from datetime import UTC, datetime
from decimal import Decimal
import base64
import hashlib
import hmac
import json
import uuid

import httpx
import numpy as np

from agent.config import settings
from agent.face.types import FaceProfile


class ApiClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or settings.api_base_url
        self._signature_key = hashlib.sha256(settings.device_secret.encode("utf-8")).hexdigest()

    def heartbeat(self, camera_status: str) -> dict:
        payload = {
            "device_code": settings.device_code,
            "timestamp": datetime.now().isoformat(),
            "camera_status": camera_status,
        }
        body = self._json_body(payload)
        with httpx.Client(timeout=5) as client:
            response = client.post(
                f"{self.base_url}/device/heartbeat",
                content=body,
                headers=self._signed_json_headers(body),
            )
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
        body = self._json_body(payload)
        with httpx.Client(timeout=10) as client:
            response = client.post(
                f"{self.base_url}/device/punch-events",
                content=body,
                headers=self._signed_json_headers(body),
            )
            response.raise_for_status()
            return response.json()

    def fetch_face_profiles(self, updated_after: str | None = None) -> list[FaceProfile]:
        params = {"device_code": settings.device_code}
        if updated_after:
            params["updated_after"] = updated_after
        with httpx.Client(timeout=20) as client:
            response = client.get(
                f"{self.base_url}/device/face-profiles",
                params=params,
                headers=self._signed_headers(b""),
            )
            response.raise_for_status()
            items = response.json().get("items", [])
        profiles: list[FaceProfile] = []
        for item in items:
            raw = base64.b64decode(item["feature_data"])
            feature = np.frombuffer(raw, dtype=np.float32)
            profiles.append(FaceProfile(student_id=item["student_id"], feature=feature))
        return profiles

    def _json_body(self, payload: dict) -> bytes:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def _signed_json_headers(self, body: bytes) -> dict[str, str]:
        headers = self._signed_headers(body)
        headers["Content-Type"] = "application/json"
        return headers

    def _signed_headers(self, body: bytes) -> dict[str, str]:
        timestamp = datetime.now(UTC).isoformat()
        nonce = str(uuid.uuid4())
        signing_payload = f"{timestamp}.{nonce}.".encode("utf-8") + body
        signature = hmac.new(self._signature_key.encode("utf-8"), signing_payload, hashlib.sha256).hexdigest()
        return {
            "X-Codebook-Device-Code": settings.device_code,
            "X-Codebook-Timestamp": timestamp,
            "X-Codebook-Nonce": nonce,
            "X-Codebook-Signature": signature,
        }
