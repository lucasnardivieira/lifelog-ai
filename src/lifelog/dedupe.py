"""Spot events that were already logged the same day (e.g. sleep via buttons in the morning and
again in the evening voice summary). Sums like spending and minutes would otherwise double-count.

Rules are deliberately conservative: only flag when the same thing clearly repeats.
"""

from typing import Any

from lifelog.events import Event, EventType

# once per day by nature
ONCE_PER_DAY = {EventType.SLEEP, EventType.NEEDS}
# same day + same main value (+ same category/label when both have one)
BY_VALUE = {
    EventType.EXPENSE: "amount",
    EventType.INCOME: "amount",
    EventType.EXERCISE: "minutes",
    EventType.STUDY: "minutes",
    EventType.WORK: "minutes",
    EventType.READING: "pages",
    EventType.STRESS: "score",
    EventType.ENERGY: "score",
}
# same day + same text-ish identity
BY_TEXT = {
    EventType.SOCIAL: ("category", "label"),
    EventType.MEAL: ("category", "label"),
    EventType.GRATITUDE: ("note",),
    EventType.JOURNAL: ("note",),
    EventType.HABIT: ("habit",),
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _close(a: Any, b: Any) -> bool:
    try:
        return abs(float(a) - float(b)) < 0.01
    except (TypeError, ValueError):
        return False


def is_duplicate(new: Event, existing: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the already-logged event (as stored) that `new` repeats, if any."""
    same_type = [e for e in existing if e.get("type") == new.type.value]
    if not same_type:
        return None
    if new.type in ONCE_PER_DAY:
        return same_type[0]
    if new.type == EventType.ASSESSMENT:
        return next((e for e in same_type if e.get("instrument") == new.instrument), None)
    if new.type in BY_VALUE:
        key = BY_VALUE[new.type]
        for e in same_type:
            if not _close(e.get(key), getattr(new, key)):
                continue
            a, b = _norm(e.get("category")), _norm(new.category)
            if not a or not b or a == b:
                return e
        return None
    if new.type in BY_TEXT:
        keys = BY_TEXT[new.type]
        for e in same_type:
            if all(_norm(e.get(k)) == _norm(getattr(new, k)) for k in keys if getattr(new, k)):
                return e
        return None
    return None  # affect check-ins are naturally repeated during the day


ENRICHABLE: dict[EventType, tuple[str, ...]] = {
    EventType.SLEEP: (
        "bedtime",
        "wake_time",
        "sol_minutes",
        "awakenings",
        "waso_minutes",
        "score",
        "rested",
    ),  # fmt: skip
    EventType.EXPENSE: ("category", "label"),
    EventType.EXERCISE: ("category", "pleasure", "mastery"),
    EventType.STUDY: ("category", "pleasure", "mastery"),
}


def adds_detail(new: Event, old: dict[str, Any]) -> list[str]:
    """Fields the new event knows that the stored one doesn't (e.g. bedtime said later by voice)."""
    return [
        f
        for f in ENRICHABLE.get(new.type, ())
        if getattr(new, f) is not None and old.get(f) is None
    ]


def classify(new: Event, existing: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None]:
    """'new' | 'repeat' (already logged) | 'enrich' (repeat that completes the stored event)."""
    old = is_duplicate(new, existing)
    if old is None:
        return "new", None
    return ("enrich" if adds_detail(new, old) else "repeat"), old
