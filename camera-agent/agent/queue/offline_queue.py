from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class QueuedEvent:
    local_event_id: str
    student_id: int | None
    captured_at: datetime
    confidence: float | None
    snapshot_path: str | None


class OfflineQueue:
    def __init__(self) -> None:
        self._items: list[QueuedEvent] = []

    def push(self, event: QueuedEvent) -> None:
        self._items.append(event)

    def pop_all(self) -> list[QueuedEvent]:
        items = self._items
        self._items = []
        return items

