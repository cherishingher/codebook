from datetime import datetime, timedelta

from agent.config import settings


class DedupCache:
    def __init__(self) -> None:
        self._seen: dict[int, datetime] = {}

    def seen_recently(self, student_id: int) -> bool:
        last_seen = self._seen.get(student_id)
        if last_seen is None:
            return False
        return datetime.now() - last_seen < timedelta(seconds=settings.dedup_seconds)

    def mark(self, student_id: int) -> None:
        self._seen[student_id] = datetime.now()

