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

# Field name → Python type. Values travel as text in {name, value} pairs, so the JSON schema has
# no nullable/union types at all (structured outputs cap unions at 16) and Claude only emits the
# fields the person actually mentioned — fewer output tokens, lower cost.
FIELD_TYPES: dict[str, type] = {
    "score": int, "hours": float, "minutes": int, "pages": int, "amount": float,
    "category": str, "label": str, "note": str, "valence": int, "arousal": int,
    "autonomy": int, "competence": int, "relatedness": int, "pleasure": int, "mastery": int,
    "bedtime": str, "wake_time": str, "sol_minutes": int, "awakenings": int,
    "waso_minutes": int, "rested": int, "habit": str, "done": bool,
}  # fmt: skip

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": EXTRACTABLE},
                    "day_offset": {"type": "integer"},
                    "time": {"type": "string"},
                    "emotions": {
                        "type": "array",
                        "items": {"type": "string", "enum": list(EMOTIONS)},
                    },
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "enum": list(FIELD_TYPES)},
                                "value": {"type": "string"},
                            },
                            "required": ["name", "value"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["type", "day_offset", "time", "emotions", "fields"],
                "additionalProperties": False,
            },
        },
        "risk": {"type": "string", "enum": ["none", "concern", "crisis"]},
        "reply": {"type": "string"},
    },
    "required": ["events", "risk", "reply"],
    "additionalProperties": False,
}


def _cast(kind: type, value: str) -> Any:
    value = value.strip()
    if kind is bool:
        return value.lower() in ("true", "sim", "1", "yes")
    if kind is int:
        return int(round(float(value.replace(",", "."))))
    if kind is float:
        return float(value.replace(",", "."))
    return value


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
    problems: list[str] = []


def parse_extraction(raw: dict[str, Any]) -> Extraction:
    """Wire format ({name, value} pairs) → typed ExtractedEvents; bad values become problems."""
    events, problems = [], []
    for item in raw.get("events", []):
        kwargs: dict[str, Any] = {
            "type": item["type"],
            "day_offset": item.get("day_offset", 0),
            "time": item.get("time") or None,
            "emotions": item.get("emotions") or [],
        }
        for pair in item.get("fields", []):
            name, value = pair["name"], pair["value"]
            if name in FIELD_TYPES and value.strip() and value.strip().lower() != "null":
                try:
                    kwargs[name] = _cast(FIELD_TYPES[name], value)
                except ValueError:
                    problems.append(f"{item['type']}: {name}={value!r}")
        events.append(ExtractedEvent(**kwargs))
    return Extraction(
        events=events, risk=raw.get("risk", "none"), reply=raw.get("reply", ""), problems=problems
    )


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
    problems: list[str] = list(extraction.problems)
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
            if "events need" in first:
                continue  # mentioned without its main value ("fui pro trabalho"): not an error
            problems.append(f"{item.type}: {first}")
    return events, problems
