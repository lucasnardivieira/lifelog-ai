"""What Claude returns for a free-text message, and how it becomes contract `Event`s.

The JSON schema is written by hand (not generated) so it only uses features supported by
structured outputs: every field is required and nullable, enums are explicit, no numeric bounds
(bounds are enforced afterwards by the `Event` model, which rejects bad values).
"""

from datetime import date, datetime, time, timedelta
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ValidationError

from lifelog.emotions import EMOTIONS
from lifelog.events import Event, EventType
from lifelog.storage.jsonl import new_event_id

TZ = ZoneInfo("America/Sao_Paulo")

EXTRACTABLE = [
    "sleep", "exercise", "energy", "meal", "affect", "stress", "needs", "gratitude", "journal",
    "study", "reading", "work", "habit", "expense", "income", "social",
]  # fmt: skip

_INT = {"anyOf": [{"type": "integer"}, {"type": "null"}]}
_NUM = {"anyOf": [{"type": "number"}, {"type": "null"}]}
_STR = {"anyOf": [{"type": "string"}, {"type": "null"}]}
_BOOL = {"anyOf": [{"type": "boolean"}, {"type": "null"}]}

EVENT_FIELDS: dict[str, Any] = {
    "type": {"type": "string", "enum": EXTRACTABLE},
    "day_offset": {"type": "integer", "description": "0 = today, -1 = yesterday"},
    "time": {**_STR, "description": "HH:MM local time if mentioned"},
    "score": _INT,
    "hours": _NUM,
    "minutes": _INT,
    "pages": _INT,
    "amount": _NUM,
    "category": _STR,
    "label": _STR,
    "note": _STR,
    "valence": _INT,
    "arousal": _INT,
    "emotions": {"type": "array", "items": {"type": "string", "enum": list(EMOTIONS)}},
    "autonomy": _INT,
    "competence": _INT,
    "relatedness": _INT,
    "pleasure": _INT,
    "mastery": _INT,
    "bedtime": _STR,
    "wake_time": _STR,
    "sol_minutes": _INT,
    "awakenings": _INT,
    "waso_minutes": _INT,
    "rested": _INT,
    "habit": _STR,
    "done": _BOOL,
}

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": EVENT_FIELDS,
                "required": list(EVENT_FIELDS),
                "additionalProperties": False,
            },
        },
        "risk": {"type": "string", "enum": ["none", "concern", "crisis"]},
        "reply": {"type": "string"},
    },
    "required": ["events", "risk", "reply"],
    "additionalProperties": False,
}


class ExtractedEvent(BaseModel):
    type: str
    day_offset: int = 0
    time: str | None = None
    score: int | None = None
    hours: float | None = None
    minutes: int | None = None
    pages: int | None = None
    amount: float | None = None
    category: str | None = None
    label: str | None = None
    note: str | None = None
    valence: int | None = None
    arousal: int | None = None
    emotions: list[str] = []
    autonomy: int | None = None
    competence: int | None = None
    relatedness: int | None = None
    pleasure: int | None = None
    mastery: int | None = None
    bedtime: str | None = None
    wake_time: str | None = None
    sol_minutes: int | None = None
    awakenings: int | None = None
    waso_minutes: int | None = None
    rested: int | None = None
    habit: str | None = None
    done: bool | None = None


class Extraction(BaseModel):
    events: list[ExtractedEvent]
    risk: Literal["none", "concern", "crisis"] = "none"
    reply: str = ""


def _when(item: ExtractedEvent, now: datetime) -> datetime:
    day: date = (now + timedelta(days=max(-7, min(0, item.day_offset)))).date()
    if item.time:
        try:
            hh, mm = (int(x) for x in item.time.split(":"))
            return datetime.combine(day, time(hh, mm), tzinfo=now.tzinfo)
        except ValueError:
            pass
    if item.day_offset == 0:
        return now
    return datetime.combine(day, time(12, 0), tzinfo=now.tzinfo)


def to_events(
    extraction: Extraction, now: datetime, raw_text: str, source: str = "telegram"
) -> tuple[list[Event], list[str]]:
    """Validate each extracted item against the contract. Returns (events, problems)."""
    events: list[Event] = []
    problems: list[str] = []
    for item in extraction.events:
        fields = item.model_dump(exclude={"type", "day_offset", "time"}, exclude_none=True)
        if not fields.get("emotions"):
            fields.pop("emotions", None)
        if item.type in ("expense", "income"):
            fields.setdefault("currency", "BRL")
        try:
            occurred = _when(item, now)
            events.append(
                Event(
                    event_id=new_event_id(),
                    occurred_at=occurred,
                    logged_at=now if occurred.date() != now.date() else None,
                    type=EventType(item.type),
                    source=source,  # type: ignore[arg-type]
                    raw_text=raw_text,
                    **fields,
                )
            )
        except (ValidationError, ValueError) as exc:
            first = exc.errors()[0]["msg"] if isinstance(exc, ValidationError) else str(exc)
            problems.append(f"{item.type}: {first}")
    return events, problems
