from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sqlite3

from agent.config import settings


@dataclass(frozen=True)
class QueuedEvent:
    local_event_id: str
    student_id: int | None
    captured_at: datetime
    confidence: float | None
    snapshot_path: str | None


class OfflineQueue:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or settings.queue_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def push(self, event: QueuedEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO queued_events
                    (local_event_id, student_id, captured_at, confidence, snapshot_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event.local_event_id,
                    event.student_id,
                    event.captured_at.isoformat(),
                    event.confidence,
                    event.snapshot_path,
                ),
            )

    def peek(self, limit: int = 50) -> list[QueuedEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT local_event_id, student_id, captured_at, confidence, snapshot_path
                FROM queued_events
                ORDER BY id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            QueuedEvent(
                local_event_id=row[0],
                student_id=row[1],
                captured_at=datetime.fromisoformat(row[2]),
                confidence=row[3],
                snapshot_path=row[4],
            )
            for row in rows
        ]

    def mark_uploaded(self, local_event_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM queued_events WHERE local_event_id = ?", (local_event_id,))

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS queued_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    local_event_id TEXT NOT NULL UNIQUE,
                    student_id INTEGER,
                    captured_at TEXT NOT NULL,
                    confidence REAL,
                    snapshot_path TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
