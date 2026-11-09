from datetime import datetime

from lifelog.bot.flows import AFFECT, PSS10, SLEEP, WHO5, affect_grid, close_flow, sleep_hours
from lifelog.events import EventType
from lifelog.extract.schema import TZ

NOW = datetime(2026, 11, 9, 8, 0, tzinfo=TZ)


def test_sleep_hours_crosses_midnight() -> None:
    v = {"bedtime": "23:30", "wake_time": "07:00", "sol_minutes": 15, "waso_minutes": 15}
    assert sleep_hours(v) == 7.0


def test_sleep_flow_produces_valid_diary_event() -> None:
    v = {
        "bedtime": "00:30",
        "sol_minutes": 30,
        "awakenings": 1,
        "waso_minutes": 10,
        "wake_time": "08:00",
        "quality": 4,
        "rested": 3,
    }
    (event,) = SLEEP.finalize(v, NOW)
    assert event.type == EventType.SLEEP
    assert event.hours == 6.75 and event.bedtime == "00:30" and event.score == 4


def test_affect_grid_has_no_neutral_and_covers_four_quadrants() -> None:
    cells = affect_grid()
    assert len(cells) == 16
    pairs = [tuple(int(x) for x in value.split(",")) for _, value in cells]
    assert all(v != 0 and a != 0 for v, a in pairs)
    assert {label[0] for label, _ in cells} == {"🟨", "🟥", "🟦", "🟩"}


def test_affect_words_follow_the_chosen_quadrant() -> None:
    words = AFFECT.steps[1].choices({"grid": "-2,2"})
    assert ("ansioso", "ansioso") in words and ("calmo", "calmo") not in words
    (event,) = AFFECT.finalize({"grid": "-2,2", "words": ["ansioso", "tenso"]}, NOW)
    assert event.valence == -2 and event.arousal == 2 and event.emotions == ["ansioso", "tenso"]


def test_close_flow_logs_needs_stress_and_every_active_habit() -> None:
    habits = [
        {"name": "meditar", "if_then": "Se…", "active": True},
        {"name": "água", "active": False},
    ]
    flow = close_flow(habits)
    assert [s.key for s in flow.steps][-1] == "habits"
    events = flow.finalize(
        {"stress": 2, "autonomy": 4, "competence": 3, "relatedness": 5, "habits": []}, NOW
    )
    types = [e.type for e in events]
    assert types == [EventType.STRESS, EventType.NEEDS, EventType.HABIT]
    assert events[-1].habit == "meditar" and events[-1].done is False


def test_questionnaires_match_instrument_shapes() -> None:
    (who5,) = WHO5.finalize({f"q{i}": 3 for i in range(5)}, NOW)
    assert who5.instrument == "who5" and who5.responses == [3] * 5
    (pss,) = PSS10.finalize({f"q{i}": 2 for i in range(10)}, NOW)
    assert pss.instrument == "pss10" and len(pss.responses) == 10


def test_callback_data_fits_telegram_limit() -> None:
    # "f|<8-char token>|<index>" must stay under Telegram's 64-byte limit
    assert len(b"f|abcdef12|15") <= 64
