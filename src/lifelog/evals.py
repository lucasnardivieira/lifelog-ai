"""Extraction eval: run the golden set against the live model and score it.

    uv run --env-file .env lifelog eval        (costs a few cents with Haiku)

Scores: type recall/precision per message and field accuracy for the fields each case pins down.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from lifelog.extract.claude import MODEL, extract
from lifelog.extract.schema import TZ, ExtractedEvent

GOLDEN = Path("evals/golden.jsonl")
NOW = datetime(2026, 11, 9, 21, 0, tzinfo=TZ)  # fixed "now" so day_offset expectations are stable


def _match_field(item: ExtractedEvent, key: str, want: Any) -> bool:
    if key == "valence_sign":
        return item.valence is not None and (item.valence > 0) == (want > 0)
    if key == "arousal_sign":
        return item.arousal is not None and (item.arousal > 0) == (want > 0)
    if key == "emotions_any":
        return bool(set(item.emotions) & set(want))
    got = getattr(item, key)
    if isinstance(want, str) and isinstance(got, str):
        return got.strip().lower() == want.lower()
    if isinstance(want, int | float) and isinstance(got, int | float):
        return abs(got - want) < 0.01
    return got == want


def score_case(case: dict[str, Any], items: list[ExtractedEvent]) -> dict[str, Any]:
    if "expect_any_type" in case:
        ok = any(i.type in case["expect_any_type"] for i in items)
        return {"types_ok": ok, "fields_ok": 1 if ok else 0, "fields_total": 1}
    expected = case["expect"]
    got_types = sorted(i.type for i in items)
    want_types = sorted(e["type"] for e in expected)
    # extra events that are welcome (e.g. "acordei cansado" also yields an affect check-in)
    extras = list(got_types)
    for t in want_types:
        if t in extras:
            extras.remove(t)
    if all(t in case.get("allow_extra", []) for t in extras) and all(
        t in got_types for t in want_types
    ):
        got_types = want_types
    fields_ok = fields_total = 0
    for exp in expected:
        cand = [i for i in items if i.type == exp["type"]]
        for key, want in exp.items():
            if key == "type":
                continue
            fields_total += 1
            fields_ok += any(_match_field(c, key, want) for c in cand)
    return {
        "types_ok": got_types == want_types,
        "fields_ok": fields_ok,
        "fields_total": fields_total,
    }


def run(client: Any = None) -> dict[str, float]:
    cases = [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line]
    results = []
    for case in cases:
        extraction = extract(case["text"], NOW, client=client)
        r = score_case(case, extraction.events)
        results.append(r)
        mark = "✓" if r["types_ok"] and r["fields_ok"] == r["fields_total"] else "✗"
        print(f"{mark} {case['text'][:60]:<60} → {[i.type for i in extraction.events]}")
    type_acc = sum(r["types_ok"] for r in results) / len(results)
    fields = sum(r["fields_ok"] for r in results) / max(1, sum(r["fields_total"] for r in results))
    print(
        f"\nmodel {MODEL}: event types exact {type_acc:.0%} · field accuracy {fields:.0%} · {len(results)} cases"
    )
    return {"type_accuracy": type_acc, "field_accuracy": fields}
