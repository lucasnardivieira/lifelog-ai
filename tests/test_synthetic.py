import csv
from collections import Counter
from datetime import date
from pathlib import Path
from statistics import correlation, fmean

import pytest

from lifelog.emotions import EMOTIONS, quadrant
from lifelog.synthetic import generate, to_jsonl

END = date(2026, 11, 8)


@pytest.fixture(scope="module")
def events():
    return generate(END, days=120, seed=7)


def test_deterministic() -> None:
    assert to_jsonl(generate(END, days=20, seed=1)) == to_jsonl(generate(END, days=20, seed=1))


def test_one_sleep_needs_and_stress_entry_per_day(events) -> None:
    per_type = Counter(e.type.value for e in events)
    assert per_type["sleep"] == per_type["needs"] == per_type["stress"] == 120


def test_all_four_affect_quadrants_present(events) -> None:
    quadrants = Counter(quadrant(e.valence, e.arousal) for e in events if e.type == "affect")
    assert set(quadrants) == {"yellow", "red", "blue", "green"}


def test_sleep_drives_valence(events) -> None:
    by_day: dict = {}
    for e in events:
        by_day.setdefault(e.occurred_at.date(), []).append(e)
    pairs = [
        (
            next(e.hours for e in evs if e.type == "sleep"),
            fmean(e.valence for e in evs if e.type == "affect"),
        )
        for evs in by_day.values()
        if any(e.type == "affect" for e in evs)
    ]
    assert correlation(*zip(*pairs, strict=True)) > 0.3


def test_emotion_vocabulary_grows(events) -> None:
    affect = [e for e in events if e.type == "affect"]
    first = {w for e in affect[: len(affect) // 3] for w in e.emotions}
    last = {w for e in affect[-len(affect) // 3 :] for w in e.emotions}
    assert len(last) > len(first)


def test_weekly_who5_on_sundays(events) -> None:
    who5 = [e for e in events if e.instrument == "who5"]
    assert who5 and all(e.occurred_at.weekday() == 6 for e in who5)


def test_dbt_seed_matches_vocabulary() -> None:
    seed = Path(__file__).parents[1] / "dbt/seeds/emotion_vocabulary.csv"
    with seed.open(encoding="utf-8") as f:
        rows = {
            r["word"]: (int(r["valence"]), int(r["arousal"]), r["quadrant"])
            for r in csv.DictReader(f)
        }
    assert rows == {w: (v, a, quadrant(v, a)) for w, (v, a) in EMOTIONS.items()}
