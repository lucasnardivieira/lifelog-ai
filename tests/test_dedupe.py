from datetime import datetime

from lifelog.dedupe import is_duplicate
from lifelog.events import Event, EventType
from lifelog.extract.schema import TZ
from lifelog.storage.jsonl import EventStore

NOW = datetime(2026, 11, 10, 21, 0, tzinfo=TZ)


def ev(type_: EventType, **fields) -> Event:
    return Event(event_id=f"n-{type_}", occurred_at=NOW, type=type_, source="telegram", **fields)


def stored(type_: str, **fields) -> dict:
    return {"event_id": "old", "occurred_at": "2026-11-10T08:00:00-03:00", "type": type_, **fields}


def test_sleep_and_needs_are_once_per_day() -> None:
    assert is_duplicate(ev(EventType.SLEEP, hours=7), [stored("sleep", hours=7.5)])
    assert is_duplicate(ev(EventType.SLEEP, hours=7), []) is None


def test_expense_repeats_only_with_same_amount_and_compatible_category() -> None:
    old = [stored("expense", amount=42.0, category="alimentação")]
    assert is_duplicate(ev(EventType.EXPENSE, amount=42, category="alimentação"), old)
    assert is_duplicate(ev(EventType.EXPENSE, amount=42), old)  # category unknown → still same
    assert is_duplicate(ev(EventType.EXPENSE, amount=42, category="mercado"), old) is None
    assert is_duplicate(ev(EventType.EXPENSE, amount=15, category="alimentação"), old) is None


def test_exercise_and_social_and_habits() -> None:
    assert is_duplicate(
        ev(EventType.EXERCISE, minutes=40, category="corrida"),
        [stored("exercise", minutes=40, category="Corrida")],
    )
    assert (
        is_duplicate(
            ev(EventType.EXERCISE, minutes=60, category="corrida"),
            [stored("exercise", minutes=40, category="corrida")],
        )
        is None
    )
    assert is_duplicate(
        ev(EventType.SOCIAL, category="namorado", label="jantar"),
        [stored("social", category="namorado", label="jantar")],
    )
    assert is_duplicate(
        ev(EventType.HABIT, habit="meditar", done=True),
        [stored("habit", habit="meditar", done=True)],
    )


def test_affect_checkins_are_never_duplicates() -> None:
    assert (
        is_duplicate(
            ev(EventType.AFFECT, valence=1, arousal=-1), [stored("affect", valence=1, arousal=-1)]
        )
        is None
    )


def test_store_events_on_ignores_retracted(tmp_path) -> None:
    store = EventStore(tmp_path / "e.jsonl")
    store.append([ev(EventType.SLEEP, hours=7)])
    assert [e["type"] for e in store.events_on("2026-11-10")] == ["sleep"]
    store.retract(["n-sleep"], NOW)
    assert store.events_on("2026-11-10") == []
