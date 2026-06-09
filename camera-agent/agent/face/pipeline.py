from datetime import datetime
from uuid import uuid4

import numpy as np

from agent.api.client import ApiClient
from agent.face.liveness import LivenessChecker
from agent.face.quality import FaceQualityChecker
from agent.face.recognizer import FaceRecognizer
from agent.queue.dedup import DedupCache
from agent.queue.offline_queue import OfflineQueue, QueuedEvent


class RecognitionPipeline:
    def __init__(self, api: ApiClient) -> None:
        self.api = api
        self.recognizer = FaceRecognizer()
        self.quality = FaceQualityChecker()
        self.liveness = LivenessChecker()
        self.dedup = DedupCache()
        self.queue = OfflineQueue()
        self.sync_profiles()

    def sync_profiles(self) -> None:
        try:
            profiles = self.api.fetch_face_profiles()
        except Exception:
            return
        self.recognizer.update_profiles(profiles)

    def process_frame(self, frame: np.ndarray) -> None:
        self.flush_queued_events()
        if not self.quality.is_usable(frame):
            return
        if not self.liveness.is_live_candidate(frame):
            return

        for match in self.recognizer.recognize(frame):
            if self.dedup.seen_recently(match.student_id):
                continue
            self.dedup.mark(match.student_id)
            event = QueuedEvent(
                local_event_id=str(uuid4()),
                student_id=match.student_id,
                captured_at=datetime.now(),
                confidence=match.confidence,
                snapshot_path=None,
            )
            self._upload_or_queue(event)

    def flush_queued_events(self) -> None:
        for event in self.queue.peek():
            try:
                self.api.upload_punch_event(
                    local_event_id=event.local_event_id,
                    student_id=event.student_id,
                    captured_at=event.captured_at,
                    confidence=event.confidence,
                    snapshot_path=event.snapshot_path,
                )
            except Exception:
                return
            self.queue.mark_uploaded(event.local_event_id)

    def _upload_or_queue(self, event: QueuedEvent) -> None:
        try:
            self.api.upload_punch_event(
                local_event_id=event.local_event_id,
                student_id=event.student_id,
                captured_at=event.captured_at,
                confidence=event.confidence,
                snapshot_path=event.snapshot_path,
            )
        except Exception:
            self.queue.push(event)
