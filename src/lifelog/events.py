"""The event contract: one flat, typed record per thing that happened.

Both the synthetic generator and the Telegram bot emit exactly this shape (JSON Lines),
so everything downstream (dbt, export, dashboard) is agnostic to where data came from.
Psychological grounding for each field: docs/research/psychology-foundations.md.
"""

import re
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from lifelog.emotions import EMOTIONS


class Area(StrEnum):
    BODY = "body"
    MIND = "mind"
    GROWTH = "growth"
    MONEY_SOCIAL = "money_social"


class EventType(StrEnum):
    # body
    SLEEP = "sleep"  # Consensus Sleep Diary (morning)
    EXERCISE = "exercise"
    ENERGY = "energy"
    MEAL = "meal"
    # mind
    AFFECT = "affect"  # circumplex check-in: valence × arousal + emotion words
    MOOD = "mood"  # legacy 1–5 score; dbt maps it onto valence
    STRESS = "stress"
    NEEDS = "needs"  # SDT: autonomy, competence, relatedness
    ASSESSMENT = "assessment"  # validated questionnaires (WHO-5, PSS-10, life satisfaction)
    GRATITUDE = "gratitude"
    JOURNAL = "journal"
    # growth
    STUDY = "study"
    READING = "reading"
    WORK = "work"
    HABIT = "habit"  # habit check-in with its if-then plan
    # money & social
    EXPENSE = "expense"
    INCOME = "income"
    SOCIAL = "social"
    # bookkeeping: append-only correction — `label` holds the retracted event_id
    RETRACTION = "retraction"


AREA_OF: dict[EventType, Area] = {
    EventType.SLEEP: Area.BODY,
    EventType.EXERCISE: Area.BODY,
    EventType.ENERGY: Area.BODY,
    EventType.MEAL: Area.BODY,
    EventType.AFFECT: Area.MIND,
    EventType.MOOD: Area.MIND,
    EventType.STRESS: Area.MIND,
    EventType.NEEDS: Area.MIND,
    EventType.ASSESSMENT: Area.MIND,
    EventType.GRATITUDE: Area.MIND,
    EventType.JOURNAL: Area.MIND,
    EventType.STUDY: Area.GROWTH,
    EventType.READING: Area.GROWTH,
    EventType.WORK: Area.GROWTH,
    EventType.HABIT: Area.GROWTH,
    EventType.EXPENSE: Area.MONEY_SOCIAL,
    EventType.INCOME: Area.MONEY_SOCIAL,
    EventType.SOCIAL: Area.MONEY_SOCIAL,
}

# fields each type must carry
REQUIRED: dict[EventType, tuple[str, ...]] = {
    EventType.SLEEP: ("hours",),
    EventType.EXERCISE: ("minutes",),
    EventType.ENERGY: ("score",),
    EventType.MEAL: ("category",),
    EventType.AFFECT: ("valence", "arousal"),
    EventType.MOOD: ("score",),
    EventType.STRESS: ("score",),
    EventType.NEEDS: ("autonomy", "competence", "relatedness"),
    EventType.ASSESSMENT: ("instrument", "responses"),
    EventType.GRATITUDE: ("note",),
    EventType.JOURNAL: ("note",),
    EventType.STUDY: ("minutes",),
    EventType.READING: ("pages",),
    EventType.WORK: ("minutes",),
    EventType.HABIT: ("habit", "done"),
    EventType.EXPENSE: ("amount",),
    EventType.INCOME: ("amount",),
    EventType.SOCIAL: ("category",),
    EventType.RETRACTION: ("label",),
}

# validated instruments: number of items and allowed response range
INSTRUMENTS: dict[str, tuple[int, int, int]] = {
    "who5": (5, 0, 5),
    "pss10": (10, 0, 4),
    "life_satisfaction": (1, 0, 10),
}

_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
Bipolar = int  # −2…+2
Likert5 = int  # 1…5
Rating10 = int  # 0…10


class Event(BaseModel):
    event_id: str
    occurred_at: datetime = Field(description="timezone-aware local time")
    type: EventType
    source: Literal["synthetic", "telegram", "manual"]
    logged_at: datetime | None = Field(default=None, description="when it was recorded, if later")

    # generic measures
    score: Likert5 | None = Field(default=None, ge=1, le=5)
    hours: float | None = Field(default=None, ge=0, le=24)
    minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    pages: int | None = Field(default=None, ge=0)
    amount: float | None = Field(default=None, ge=0)
    currency: str | None = None
    category: str | None = Field(default=None, description="topic, expense category, who…")
    label: str | None = Field(default=None, description="book, merchant, activity…")
    note: str | None = None
    raw_text: str | None = Field(default=None, description="the message as it was sent")

    # sleep diary (Carney et al., 2012) — score = sleep quality 1–5
    bedtime: str | None = Field(default=None, description="HH:MM, lights out")
    wake_time: str | None = Field(default=None, description="HH:MM, final awakening")
    sol_minutes: int | None = Field(default=None, ge=0, le=600, description="sleep-onset latency")
    awakenings: int | None = Field(default=None, ge=0, le=30)
    waso_minutes: int | None = Field(default=None, ge=0, le=600, description="wake after onset")
    rested: Likert5 | None = Field(default=None, ge=1, le=5)

    # core affect (Russell) + emotion words (granularity)
    valence: Bipolar | None = Field(default=None, ge=-2, le=2)
    arousal: Bipolar | None = Field(default=None, ge=-2, le=2)
    emotions: list[str] | None = None

    # self-determination theory, end-of-day
    autonomy: Likert5 | None = Field(default=None, ge=1, le=5)
    competence: Likert5 | None = Field(default=None, ge=1, le=5)
    relatedness: Likert5 | None = Field(default=None, ge=1, le=5)

    # behavioral activation ratings on activities
    pleasure: Rating10 | None = Field(default=None, ge=0, le=10)
    mastery: Rating10 | None = Field(default=None, ge=0, le=10)

    # questionnaires
    instrument: str | None = None
    responses: list[int] | None = None

    # habits & implementation intentions
    habit: str | None = None
    done: bool | None = None
    if_then: str | None = None

    @field_validator("bedtime", "wake_time")
    @classmethod
    def _hhmm(cls, value: str | None) -> str | None:
        if value is not None and not _HHMM.match(value):
            raise ValueError("expected HH:MM")
        return value

    @field_validator("emotions")
    @classmethod
    def _known_emotions(cls, value: list[str] | None) -> list[str] | None:
        if value is not None:
            unknown = [w for w in value if w not in EMOTIONS]
            if unknown:
                raise ValueError(f"unknown emotion words: {unknown}")
        return value

    @model_validator(mode="after")
    def _check(self) -> "Event":
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        missing = [f for f in REQUIRED[self.type] if getattr(self, f) is None]
        if missing:
            raise ValueError(f"{self.type} events need {missing}")
        if self.type == EventType.ASSESSMENT:
            if self.instrument not in INSTRUMENTS:
                raise ValueError(f"unknown instrument {self.instrument!r}")
            n, lo, hi = INSTRUMENTS[self.instrument]
            assert self.responses is not None
            if len(self.responses) != n or not all(lo <= r <= hi for r in self.responses):
                raise ValueError(f"{self.instrument} needs {n} responses in [{lo}, {hi}]")
        return self

    @property
    def area(self) -> Area | None:
        return AREA_OF.get(self.type)
