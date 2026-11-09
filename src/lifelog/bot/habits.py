"""Habit definitions (name + if-then plan), stored next to the private events."""

import json
import re
from pathlib import Path

# "novo hábito: meditar 10 min — se eu terminar o café, então medito"
NEW_HABIT = re.compile(
    r"^\s*novo h[aá]bito\s*:\s*(?P<name>[^—\-|;]+?)\s*(?:[—\-|;]+\s*(?P<plan>se\b.+))?\s*$",
    re.IGNORECASE,
)


def parse_new_habit(text: str) -> dict[str, str] | None:
    m = NEW_HABIT.match(text)
    if not m:
        return None
    name = m.group("name").strip().rstrip(".").lower()
    plan = (m.group("plan") or "").strip()
    if plan:
        plan = plan[0].upper() + plan[1:]
        if not plan.endswith("."):
            plan += "."
    return {"name": name, "if_then": plan, "active": True}


class HabitStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, habits: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(habits, ensure_ascii=False, indent=1), encoding="utf-8")

    def upsert(self, habit: dict) -> list[dict]:
        habits = [h for h in self.load() if h["name"] != habit["name"]] + [habit]
        self.save(habits)
        return habits

    def deactivate(self, name: str) -> bool:
        habits = self.load()
        found = False
        for h in habits:
            if h["name"] == name.lower():
                h["active"], found = False, True
        self.save(habits)
        return found
