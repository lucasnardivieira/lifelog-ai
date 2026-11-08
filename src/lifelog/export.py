"""Read the dbt marts and write the single JSON file the dashboard loads."""

import json
from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from lifelog.emotions import EMOTIONS, QUADRANTS, quadrant
from lifelog.insights import find_insights

AREAS = {
    "body": {"label": "Corpo", "emoji": "💪"},
    "mind": {"label": "Mente", "emoji": "🧠"},
    "growth": {"label": "Crescimento", "emoji": "📚"},
    "money_social": {"label": "Dinheiro & social", "emoji": "💸"},
}

INSTRUMENTS = {
    "who5": {
        "name": "WHO-5 — Índice de Bem-Estar",
        "max": 100,
        "higher_is_better": True,
        "reference": 52,
        "reference_label": "abaixo de 52: vale conversar com alguém",
        "source": "OMS; validação brasileira: de Souza & Hidalgo (2012)",
    },
    "pss10": {
        "name": "PSS-10 — Estresse Percebido",
        "max": 40,
        "higher_is_better": False,
        "source": "Cohen et al. (1983); validação brasileira: Reis et al. (2010)",
    },
    "life_satisfaction": {
        "name": "Satisfação com a vida",
        "max": 10,
        "higher_is_better": True,
        "source": "Item único 0–10 (Global Flourishing Study)",
    },
}

SUPPORT = {
    "title": "Precisa conversar?",
    "text": (
        "Este painel não faz diagnóstico. Se você está passando por um momento difícil, "
        "conversar ajuda."
    ),
    "contacts": [
        {
            "name": "CVV — Centro de Valorização da Vida",
            "detail": "ligue 188 (grátis, 24h)",
            "href": "tel:188",
        },
        {"name": "Chat do CVV", "detail": "cvv.org.br", "href": "https://cvv.org.br/chat/"},
        {"name": "Emergência — SAMU", "detail": "ligue 192", "href": "tel:192"},
    ],
}

# habit strength: exponentially weighted repetition; a missed day dents it, never resets it
HABIT_ALPHA = 0.06


def _clean(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 2)
    if isinstance(value, Decimal):
        return round(float(value), 2)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, datetime):
        return value.isoformat(timespec="minutes")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def _rows(con: duckdb.DuckDBPyConnection, query: str) -> list[dict[str, Any]]:
    rel = con.sql(query)
    cols = rel.columns
    return [{c: _clean(v) for c, v in zip(cols, row, strict=True)} for row in rel.fetchall()]


def _drop_nulls(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if v is not None} for row in rows]


def habit_series(habit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per habit: if-then plan, daily done flags and a 0–100 strength curve."""
    by_habit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in habit_rows:
        by_habit[row["habit"]].append(row)
    habits = []
    for name, rows in by_habit.items():
        strength, points = 0.0, []
        for row in rows:
            strength += HABIT_ALPHA * ((1.0 if row["done"] else 0.0) - strength)
            points.append(
                {"day": row["day"], "done": row["done"], "strength": round(100 * strength)}
            )
        habits.append(
            {
                "habit": name,
                "if_then": rows[-1]["if_then"],
                "started": rows[0]["day"],
                "days": len(rows),
                "completion": round(sum(r["done"] for r in rows) / len(rows), 2),
                "points": points,
            }
        )
    return habits


def build_payload(db_path: Path, *, sample: bool, goals: dict[str, float]) -> dict[str, Any]:
    with duckdb.connect(str(db_path), read_only=True) as con:
        days = _rows(con, "select * from fct_daily order by day")
        weeks = _rows(con, "select * from fct_weekly order by week_start")
        spending = _rows(con, "select * from fct_spending order by day, category")
        study = _rows(con, "select * from fct_study order by day, topic")
        affect = _rows(
            con,
            """select occurred_at_local as ts, day, valence, arousal, quadrant, emotions,
                      raw_text as text from fct_affect order by ts""",
        )
        emotions = _rows(con, "select * from fct_emotions order by week_start, mentions desc")
        assessments = _rows(
            con,
            """select day, instrument, score, max_score, low_wellbeing_flag
               from fct_assessments order by day, instrument""",
        )
        habit_rows = _rows(con, "select * from fct_habits order by habit, day")
        events = _rows(
            con,
            """select event_id as id, occurred_at_local as ts, day, event_type as type, area,
                      score, hours, minutes, pages, amount, category, label, note,
                      raw_text as text
               from fct_events order by ts, id""",
        )

    # habit flags per day (for within-person insights like "screens off → sleep onset")
    done_by_day: dict[str, dict[str, bool]] = defaultdict(dict)
    for row in habit_rows:
        done_by_day[row["day"]][f"habit__{row['habit']}"] = row["done"]
    for row in days:
        row.update(done_by_day.get(row["day"], {}))

    latest_who5 = next((a for a in reversed(assessments) if a["instrument"] == "who5"), None)
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "sample": sample,
        "range": {"start": days[0]["day"], "end": days[-1]["day"]} if days else None,
        "areas": AREAS,
        "goals": goals,
        "quadrants": QUADRANTS,
        "vocabulary": [
            {"word": w, "valence": v, "arousal": a, "quadrant": quadrant(v, a)}
            for w, (v, a) in EMOTIONS.items()
        ],
        "instruments": INSTRUMENTS,
        "support": SUPPORT
        | {
            "highlight": bool(latest_who5 and latest_who5["low_wellbeing_flag"]),
        },
        "days": _drop_nulls(days),
        "weeks": _drop_nulls(weeks),
        "spending": spending,
        "study": study,
        "affect": _drop_nulls(affect),
        "emotions": emotions,
        "assessments": assessments,
        "habits": habit_series(habit_rows),
        "events": _drop_nulls(events),
        "insights": find_insights(days),
    }


def write_payload(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
