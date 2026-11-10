import json
from datetime import datetime
from types import SimpleNamespace

from lifelog.extract.claude import build_request, extract
from lifelog.extract.schema import SCHEMA, TZ, parse_extraction, to_events

NOW = datetime(2026, 11, 9, 21, 0, tzinfo=TZ)


def _item(type: str, day_offset: int = 0, time: str = "", emotions=None, **fields):
    """Wire-format event: typed values travel as {name, value} text pairs."""
    return {
        "type": type,
        "day_offset": day_offset,
        "time": time,
        "emotions": emotions or [],
        "fields": [{"name": k, "value": str(v)} for k, v in fields.items()],
    }


class FakeMessages:
    def __init__(self, payload: dict, stop_reason: str = "end_turn") -> None:
        self.payload, self.stop_reason, self.last = payload, stop_reason, None

    def create(self, **request):
        self.last = request
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=json.dumps(self.payload))],
        )


def _count_unions(node) -> int:
    if isinstance(node, dict):
        own = 1 if ("anyOf" in node or isinstance(node.get("type"), list)) else 0
        return own + sum(_count_unions(v) for v in node.values())
    if isinstance(node, list):
        return sum(_count_unions(v) for v in node)
    return 0


def test_schema_has_no_unions_and_forbids_extras() -> None:
    # structured outputs reject schemas with more than 16 union/nullable parameters
    assert _count_unions(SCHEMA) == 0
    item = SCHEMA["properties"]["events"]["items"]
    assert set(item["required"]) == set(item["properties"])
    assert item["additionalProperties"] is False


def test_request_uses_structured_output_and_cheap_model() -> None:
    req = build_request("oi", NOW)
    assert req["output_config"]["format"]["type"] == "json_schema"
    assert req["model"].startswith("claude-haiku")
    assert "2026-11-09 21:00" in req["messages"][0]["content"]


def test_extract_and_convert_multiple_events() -> None:
    payload = {
        "events": [
            _item(type="expense", amount=42, category="alimentação", label="restaurante"),
            _item(type="exercise", minutes=40, category="corrida", pleasure=8),
            _item(type="sleep", hours=5, day_offset=-1),
        ],
        "risk": "none",
        "reply": "Anotei!",
    }
    client = SimpleNamespace(messages=FakeMessages(payload))
    extraction = extract("gastei 42 no almoço, corri 40 min, ontem dormi 5h", NOW, client=client)
    events, problems = to_events(extraction, NOW, "texto")
    assert problems == []
    assert [e.type.value for e in events] == ["expense", "exercise", "sleep"]
    assert events[0].currency == "BRL"
    assert events[2].occurred_at.date().isoformat() == "2026-11-08"
    assert events[2].logged_at == NOW


def test_invalid_values_are_reported_not_saved() -> None:
    extraction = parse_extraction(
        {
            "events": [
                _item("affect", valence=5, arousal=1),
                _item("stress", score=3),
                _item("expense", amount="quarenta"),
            ],
            "risk": "none",
            "reply": "",
        }
    )
    events, problems = to_events(extraction, NOW, "x")
    assert [e.type.value for e in events] == ["stress"]
    assert any(p.startswith("affect") for p in problems)
    assert any("amount" in p for p in problems)


def test_wire_values_are_cast_to_types() -> None:
    ex = parse_extraction(
        {"events": [_item("sleep", hours="6,5", done="true")], "risk": "none", "reply": ""}
    )
    assert ex.events[0].hours == 6.5 and ex.events[0].done is True


def test_refusal_becomes_concern_without_events() -> None:
    client = SimpleNamespace(messages=FakeMessages({}, stop_reason="refusal"))
    extraction = extract("…", NOW, client=client)
    assert extraction.events == [] and extraction.risk == "concern"


def test_events_without_their_main_value_are_skipped_silently() -> None:
    ex = parse_extraction(
        {"events": [_item("work"), _item("sleep", hours=7)], "risk": "none", "reply": ""}
    )
    events, problems = to_events(ex, NOW, "dormi 7h e fui pro trabalho")
    assert [e.type.value for e in events] == ["sleep"]
    assert problems == []
