"""The event contract: one flat, typed record per thing that happened.

Both the synthetic generator and the Telegram bot emit exactly this shape (JSON Lines),
so everything downstream (dbt, export, dashboard) is agnostic to where data came from.
"""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Area(StrEnum):
    BODY = "body"
    MIND = "mind"
    GROWTH = "growth"
    MONEY_SOCIAL = "money_social"


class EventType(StrEnum):
    # body
    SLEEP = "sleep"
    EXERCISE = "exercise"
    ENERGY = "energy"
    MEAL = "meal"
    # mind
    MOOD = "mood"
    STRESS = "stress"
    GRATITUDE = "gratitude"
    JOURNAL = "journal"
    # growth
    STUDY = "study"
    READING = "reading"
    WORK = "work"
    # money & social
    EXPENSE = "expense"
    INCOME = "income"
    SOCIAL = "social"


AREA_OF: dict[EventType, Area] = {
    EventType.SLEEP: Area.BODY,
    EventType.EXERCISE: Area.BODY,
    EventType.ENERGY: Area.BODY,
    EventType.MEAL: Area.BODY,
    EventType.MOOD: Area.MIND,
    EventType.STRESS: Area.MIND,
    EventType.GRATITUDE: Area.MIND,
    EventType.JOURNAL: Area.MIND,
    EventType.STUDY: Area.GROWTH,
    EventType.READING: Area.GROWTH,
    EventType.WORK: Area.GROWTH,
    EventType.EXPENSE: Area.MONEY_SOCIAL,
    EventType.INCOME: Area.MONEY_SOCIAL,
    EventType.SOCIAL: Area.MONEY_SOCIAL,
}

# which measure each type must carry
REQUIRED_FIELD: dict[EventType, str] = {
    EventType.SLEEP: "hours",
    EventType.EXERCISE: "minutes",
    EventType.ENERGY: "score",
    EventType.MEAL: "category",
    EventType.MOOD: "score",
    EventType.STRESS: "score",
    EventType.GRATITUDE: "note",
    EventType.JOURNAL: "note",
    EventType.STUDY: "minutes",
    EventType.READING: "pages",
    EventType.WORK: "minutes",
    EventType.EXPENSE: "amount",
    EventType.INCOME: "amount",
    EventType.SOCIAL: "category",
}


class Event(BaseModel):
    event_id: str
    occurred_at: datetime = Field(description="timezone-aware local time")
    type: EventType
    source: Literal["synthetic", "telegram", "manual"]
    score: int | None = Field(default=None, ge=1, le=5)
    hours: float | None = Field(default=None, ge=0, le=24)
    minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    pages: int | None = Field(default=None, ge=0)
    amount: float | None = Field(default=None, ge=0)
    currency: str | None = None
    category: str | None = Field(default=None, description="topic, expense category, who…")
    label: str | None = Field(default=None, description="book, merchant, activity…")
    note: str | None = None
    raw_text: str | None = Field(default=None, description="the message as it was sent")

    @model_validator(mode="after")
    def _check(self) -> "Event":
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        if getattr(self, REQUIRED_FIELD[self.type]) is None:
            raise ValueError(f"{self.type} events need '{REQUIRED_FIELD[self.type]}'")
        return self

    @property
    def area(self) -> Area:
        return AREA_OF[self.type]
