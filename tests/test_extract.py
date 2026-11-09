import json
from datetime import datetime
from types import SimpleNamespace

from lifelog.extract.claude import build_request, extract
from lifelog.extract.schema import SCHEMA, TZ, Extraction, to_events

NOW = datetime(2026, 11, 9, 21, 0, tzinfo=TZ)


def _item(**kw):
    base = {k: None for k in SCHEMA["properties"]["events"]["items"]["properties"]}
    base.update(day_offset=0, emotions=[])
    base.update(kw)
    return base


class FakeMessages:
    def __init__(self, payload: dict, stop_reason: str = "end_turn") -> None:
        self.payload, self.stop_reason, self.last = payload, stop_reason, None

    def create(self, **request):
        self.last = request
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=json.dumps(self.payload))],
        )


def test_schema_requires_every_field_and_forbids_extras() -> None:
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
    extraction = Extraction(
        events=[_item(type="affect", valence=5, arousal=1), _item(type="stress", score=3)],
        risk="none",
        reply="",
    )
    events, problems = to_events(extraction, NOW, "x")
    assert [e.type.value for e in events] == ["stress"]
    assert problems and problems[0].startswith("affect")


def test_refusal_becomes_concern_without_events() -> None:
    client = SimpleNamespace(messages=FakeMessages({}, stop_reason="refusal"))
    extraction = extract("…", NOW, client=client)
    assert extraction.events == [] and extraction.risk == "concern"
