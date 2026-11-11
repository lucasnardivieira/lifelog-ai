"""Append-only JSON Lines event store. Corrections are new (retraction) events, never edits."""

import fcntl
import json
import uuid
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from lifelog.events import Event, EventType


def new_event_id(prefix: str = "tg") -> str:
    return f"{prefix}-{datetime.now():%Y%m%d%H%M%S}-{uuid.uuid4().hex[:6]}"


class EventStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, events: Iterable[Event]) -> list[str]:
        events = list(events)
        lines = "".join(e.model_dump_json(exclude_none=True) + "\n" for e in events)
        with self.path.open("a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(lines)
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        return [e.event_id for e in events]

    def retract(self, event_ids: Iterable[str], now: datetime) -> list[str]:
        return self.append(
            Event(
                event_id=new_event_id("rt"),
                occurred_at=now,
                type=EventType.RETRACTION,
                source="telegram",
                label=event_id,
            )
            for event_id in event_ids
        )

    def events_on(self, day: str) -> list[dict]:
        """Non-retracted events whose local date is `day` (YYYY-MM-DD)."""
        if not self.path.exists():
            return []
        rows = [
            json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line
        ]
        retracted = {r["label"] for r in rows if r["type"] == EventType.RETRACTION}
        return [
            r
            for r in rows
            if r["type"] != EventType.RETRACTION
            and r["occurred_at"][:10] == day
            and r["event_id"] not in retracted
        ]

    def count_today(self, event_type: EventType, today: str) -> int:
        """How many (non-retracted) events of a type were logged for a local date."""
        if not self.path.exists():
            return 0
        lines = self.path.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line]
        retracted = {r["label"] for r in rows if r["type"] == EventType.RETRACTION}
        return sum(
            1
            for r in rows
            if r["type"] == event_type
            and r["occurred_at"][:10] == today
            and r["event_id"] not in retracted
        )
