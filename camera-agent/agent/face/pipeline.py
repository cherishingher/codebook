from datetime import datetime
from uuid import uuid4

import numpy as np

from agent.api.client import ApiClient
from agent.face.liveness import LivenessChecker
from agent.face.quality import FaceQualityChecker
from agent.face.recognizer import FaceRecognizer
from agent.queue.dedup import DedupCache


class RecognitionPipeline:
    def __init__(self, api: ApiClient) -> None:
        self.api = api
        self.recognizer = FaceRecognizer()
        self.quality = FaceQualityChecker()
        self.liveness = LivenessChecker()
        self.dedup = DedupCache()

    def process_frame(self, frame: np.ndarray) -> None:
        if not self.quality.is_usable(frame):
            return
        if not self.liveness.is_live_candidate(frame):
            return

        for match in self.recognizer.recognize(frame):
            if self.dedup.seen_recently(match.student_id):
                continue
            self.dedup.mark(match.student_id)
            self.api.upload_punch_event(
                local_event_id=str(uuid4()),
                student_id=match.student_id,
                captured_at=datetime.now(),
                confidence=match.confidence,
                snapshot_path=None,
            )

