"""Read the dbt marts and write the single JSON file the dashboard loads."""

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from lifelog.insights import find_insights

AREAS = {
    "body": {"label": "Corpo", "emoji": "💪"},
    "mind": {"label": "Mente", "emoji": "🧠"},
    "growth": {"label": "Crescimento", "emoji": "📚"},
    "money_social": {"label": "Dinheiro & social", "emoji": "💸"},
}


def _clean(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 2)
    if isinstance(value, Decimal):
        return round(float(value), 2)
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, datetime):
        return value.isoformat(timespec="minutes")
    if isinstance(value, date):
        return value.isoformat()
    return value


def _rows(con: duckdb.DuckDBPyConnection, query: str) -> list[dict[str, Any]]:
    rel = con.sql(query)
    cols = rel.columns
    return [{c: _clean(v) for c, v in zip(cols, row, strict=True)} for row in rel.fetchall()]


def _drop_nulls(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if v is not None} for row in rows]


def build_payload(db_path: Path, *, sample: bool, goals: dict[str, float]) -> dict[str, Any]:
    with duckdb.connect(str(db_path), read_only=True) as con:
        days = _rows(con, "select * from fct_daily order by day")
        weeks = _rows(con, "select * from fct_weekly order by week_start")
        spending = _rows(con, "select * from fct_spending order by day, category")
        study = _rows(con, "select * from fct_study order by day, topic")
        events = _rows(
            con,
            """select event_id as id, occurred_at_local as ts, day, event_type as type, area,
                      score, hours, minutes, pages, amount, category, label, note, raw_text as text
               from fct_events order by ts, id""",
        )
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "sample": sample,
        "range": {"start": days[0]["day"], "end": days[-1]["day"]} if days else None,
        "areas": AREAS,
        "goals": goals,
        "days": _drop_nulls(days),
        "weeks": weeks,
        "spending": spending,
        "study": study,
        "events": _drop_nulls(events),
        "insights": find_insights(days),
    }


def write_payload(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
