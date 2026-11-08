import random

from lifelog.insights import CONDITIONS, OUTCOMES, compare, detrend, find_insights


def _rows(n: int = 120, seed: int = 3) -> list[dict]:
    rng = random.Random(seed)
    rows, trained_yesterday = [], False
    for i in range(n):
        trained = rng.random() < 0.5
        mood = 3 + (0.8 if trained_yesterday else 0) + i * 0.01 + rng.gauss(0, 0.3)
        rows.append(
            {
                "event_count": 5,
                "exercise_minutes": 40 if trained else 0,
                "mood": mood,
                "is_weekend": False,
                "sleep_hours": 7.0,
            }
        )
        trained_yesterday = trained
    return rows


def test_detrend_removes_slow_trend() -> None:
    rows = [{"x": float(i)} for i in range(60)]
    deviations = detrend(rows, "x")[28:]  # once the 28-day window is full
    # a pure linear trend leaves only a constant offset (half the window), no growth
    assert max(deviations) - min(deviations) < 1e-9


def test_lagged_effect_is_found_and_same_day_is_not() -> None:
    rows = _rows()
    mood = next(o for o in OUTCOMES if o.key == "mood")
    dev = detrend(rows, "mood")
    lagged = next(c for c in CONDITIONS if c.key == "exercised_yesterday")
    same_day = next(c for c in CONDITIONS if c.key == "exercised")
    found = compare(rows, lagged, mood, dev)
    assert found is not None and found.positive
    assert found.details["ci95"][0] > 0
    assert compare(rows, same_day, mood, dev) is None


def test_find_insights_is_deterministic_and_sorted() -> None:
    rows = _rows()
    a, b = find_insights(rows), find_insights(rows)
    assert a == b
    assert [i["strength"] for i in a] == sorted((i["strength"] for i in a), reverse=True)
