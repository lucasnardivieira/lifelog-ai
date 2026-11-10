from datetime import datetime

import pytest

from lifelog.bot.app import brl, describe, explain_api_error
from lifelog.bot.habits import HabitStore, parse_new_habit
from lifelog.evals import score_case
from lifelog.events import Event, EventType
from lifelog.extract.schema import TZ, ExtractedEvent
from lifelog.safety import keyword_risk
from lifelog.storage.jsonl import EventStore

NOW = datetime(2026, 11, 9, 21, 0, tzinfo=TZ)


@pytest.mark.parametrize(
    ("text", "risky"),
    [
        ("às vezes penso em suicídio", True),
        ("NÃO QUERO MAIS VIVER", True),
        ("quero me machucar", True),
        ("hoje o prazo me matou de cansaço", False),
        ("dia ruim, mas tô bem", False),
    ],
)
def test_keyword_risk(text: str, risky: bool) -> None:
    assert keyword_risk(text) is risky


def test_parse_new_habit_with_if_then_plan() -> None:
    h = parse_new_habit("Novo hábito: Meditar 10 min — se eu terminar o café, então medito")
    assert h == {
        "name": "meditar 10 min",
        "if_then": "Se eu terminar o café, então medito.",
        "active": True,
    }
    assert parse_new_habit("novo hábito: ler") == {"name": "ler", "if_then": "", "active": True}
    assert parse_new_habit("estudei dbt") is None


def test_habit_store_upsert_and_pause(tmp_path) -> None:
    store = HabitStore(tmp_path / "habits.json")
    store.upsert({"name": "ler", "if_then": "", "active": True})
    store.upsert({"name": "ler", "if_then": "Se…", "active": True})
    assert len(store.load()) == 1
    assert store.deactivate("LER") and store.load()[0]["active"] is False


def test_store_is_append_only_and_retractions_hide_events(tmp_path) -> None:
    store = EventStore(tmp_path / "events.jsonl")
    e = Event(event_id="a1", occurred_at=NOW, type=EventType.SLEEP, source="telegram", hours=7)
    store.append([e])
    assert store.count_today(EventType.SLEEP, "2026-11-09") == 1
    store.retract(["a1"], NOW)
    assert store.count_today(EventType.SLEEP, "2026-11-09") == 0
    assert len((tmp_path / "events.jsonl").read_text().splitlines()) == 2


def test_describe_and_brl() -> None:
    e = Event(
        event_id="x",
        occurred_at=NOW,
        type=EventType.EXPENSE,
        source="telegram",
        amount=1234.5,
        category="mercado",
        label="hortifruti",
    )
    assert brl(1234.5) == "R$ 1.234,50"
    assert describe(e) == "💸 R$ 1.234,50 mercado · hortifruti"


def test_eval_scoring() -> None:
    case = {"expect": [{"type": "affect", "valence_sign": -1, "emotions_any": ["ansioso"]}]}
    good = [ExtractedEvent(type="affect", valence=-2, arousal=2, emotions=["ansioso"])]
    bad = [ExtractedEvent(type="stress", score=4)]
    assert score_case(case, good) == {"types_ok": True, "fields_ok": 2, "fields_total": 2}
    assert score_case(case, bad)["types_ok"] is False


def test_explain_api_error_messages() -> None:
    import anthropic
    import httpx

    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    no_credit = anthropic.BadRequestError(
        "Your credit balance is too low", response=httpx.Response(400, request=req), body=None
    )
    assert "sem créditos" in explain_api_error(no_credit)
    assert "erro na API" in explain_api_error(RuntimeError("boom"))
