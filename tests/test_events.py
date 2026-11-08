from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from lifelog.events import Area, Event, EventType

NOW = datetime(2026, 11, 8, 21, 0, tzinfo=UTC)


def make(**fields) -> Event:
    return Event(event_id="e1", occurred_at=NOW, source="manual", **fields)


def test_affect_event_valid_and_mapped_to_mind() -> None:
    e = make(type=EventType.AFFECT, valence=-1, arousal=2, emotions=["ansioso"])
    assert e.area == Area.MIND


def test_unknown_emotion_word_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown emotion"):
        make(type=EventType.AFFECT, valence=1, arousal=1, emotions=["blergh"])


def test_required_fields_per_type() -> None:
    with pytest.raises(ValidationError, match="needs"):
        make(type=EventType.NEEDS, autonomy=3, competence=3)


def test_sleep_diary_requires_clock_times() -> None:
    with pytest.raises(ValidationError, match="HH:MM"):
        make(type=EventType.SLEEP, hours=7, score=3, bedtime="11pm", wake_time="07:00")


@pytest.mark.parametrize(
    ("instrument", "responses", "ok"),
    [
        ("who5", [3, 3, 3, 3, 3], True),
        ("who5", [3, 3, 3, 3], False),
        ("who5", [6, 3, 3, 3, 3], False),
        ("pss10", [2] * 10, True),
        ("life_satisfaction", [11], False),
        ("phq9", [1] * 9, False),
    ],
)
def test_assessment_validation(instrument: str, responses: list[int], ok: bool) -> None:
    fields = {"type": EventType.ASSESSMENT, "instrument": instrument, "responses": responses}
    if ok:
        make(**fields)
    else:
        with pytest.raises(ValidationError):
            make(**fields)


def test_naive_datetime_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        Event(
            event_id="x", occurred_at=datetime(2026, 1, 1), type="energy", source="manual", score=3
        )
