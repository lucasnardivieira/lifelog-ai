"""Find patterns between life tracks and phrase them in Brazilian Portuguese.

Deliberately simple statistics (group means, Cohen's d, Pearson r) so every sentence on the
"Padrões" page is explainable. Only effects with enough days on both sides and a non-trivial
size are reported.
"""

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from statistics import correlation, fmean, pstdev
from typing import Any

Row = dict[str, Any]

MIN_DAYS = 10
MIN_EFFECT = 0.3  # Cohen's d
MIN_R = 0.3


@dataclass(frozen=True)
class Condition:
    key: str
    yes: str  # short label for the UI: "treinou"
    no: str
    clause: str  # opens the sentence: "Nos dias em que você treinou"
    test: Callable[[Row], bool | None]  # None = day not comparable


@dataclass(frozen=True)
class Outcome:
    key: str
    label: str  # "humor"
    article: str  # "seu" / "sua"
    unit: str  # " pts", " min"
    higher_is_better: bool = True
    decimals: int = 1


CONDITIONS = [
    Condition(
        "slept_7h",
        "dormiu 7h+",
        "dormiu menos de 7h",
        "Nos dias em que você dormiu 7h ou mais",
        lambda r: None if r["sleep_hours"] is None else r["sleep_hours"] >= 7,
    ),
    Condition(
        "exercised",
        "treinou",
        "não treinou",
        "Nos dias em que você treinou",
        lambda r: None if r["event_count"] is None else r["exercise_minutes"] > 0,
    ),
    Condition(
        "social",
        "com programa social",
        "sem programa social",
        "Nos dias em que você encontrou alguém",
        lambda r: None if r["event_count"] is None else r["social_count"] > 0,
    ),
    Condition(
        "deadline",
        "dia de prazo",
        "dia normal",
        "Nos dias de prazo apertado no trabalho",
        lambda r: None if r["is_weekend"] or r["event_count"] is None else bool(r["is_deadline"]),
    ),
    Condition(
        "weekend",
        "fim de semana",
        "dia de semana",
        "Nos fins de semana",
        lambda r: None if r["event_count"] is None else r["is_weekend"],
    ),
]

OUTCOMES = [
    Outcome("mood", "humor", "seu", " pts"),
    Outcome("energy", "energia", "sua", " pts"),
    Outcome("stress", "estresse", "seu", " pts", higher_is_better=False),
    Outcome("study_minutes", "tempo de estudo", "seu", " min", decimals=0),
    Outcome("spend_discretionary", "gasto variável", "seu", "", higher_is_better=False, decimals=0),
]

CORRELATIONS = [
    ("sleep_hours", "mood", "Horas de sono", "humor"),
    ("sleep_hours", "energy", "Horas de sono", "energia"),
    ("stress", "mood", "Estresse", "humor"),
    ("stress", "sleep_hours", "Estresse", "horas de sono"),
    ("exercise_minutes", "energy", "Minutos de exercício", "energia"),
]


@dataclass
class Insight:
    id: str
    kind: str  # "compare" | "correlation"
    text: str
    strength: float  # 0–1, for sorting and the UI bar
    positive: bool | None  # good news? None = neutral
    x: str
    y: str
    details: dict[str, Any]


def _fmt(value: float, decimals: int) -> str:
    text = f"{value:.{decimals}f}"
    return text.replace(".", ",")


def _money(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", ".")


def compare(rows: Sequence[Row], cond: Condition, out: Outcome) -> Insight | None:
    yes, no = [], []
    for row in rows:
        flag, value = cond.test(row), row.get(out.key)
        if flag is None or value is None:
            continue
        (yes if flag else no).append(float(value))
    if len(yes) < MIN_DAYS or len(no) < MIN_DAYS:
        return None
    pooled = pstdev(yes + no)
    if pooled == 0:
        return None
    diff = fmean(yes) - fmean(no)
    d = diff / pooled
    if abs(d) < MIN_EFFECT:
        return None

    more = "maior" if diff > 0 else "menor"
    if out.key == "spend_discretionary":
        amount = _money(abs(diff))
    else:
        amount = _fmt(abs(diff), out.decimals) + out.unit
    text = f"{cond.clause}, {out.article} {out.label} foi {amount} {more}"
    if out.key in ("mood", "energy", "stress"):
        text += f" ({_fmt(fmean(yes), 1)} vs {_fmt(fmean(no), 1)})"
    text += "."
    return Insight(
        id=f"{cond.key}__{out.key}",
        kind="compare",
        text=text,
        strength=min(abs(d) / 1.5, 1.0),
        positive=(diff > 0) == out.higher_is_better,
        x=cond.key,
        y=out.key,
        details={
            "yes": {"label": cond.yes, "mean": round(fmean(yes), 2), "days": len(yes)},
            "no": {"label": cond.no, "mean": round(fmean(no), 2), "days": len(no)},
            "effect_size": round(d, 2),
            "unit": out.unit.strip(),
            "outcome_label": out.label,
        },
    )


def correlate(rows: Sequence[Row], x: str, y: str, x_label: str, y_label: str) -> Insight | None:
    pairs = [(r[x], r[y]) for r in rows if r.get(x) is not None and r.get(y) is not None]
    if len(pairs) < MIN_DAYS * 2:
        return None
    xs, ys = zip(*pairs, strict=True)
    if pstdev(xs) == 0 or pstdev(ys) == 0:
        return None
    r = correlation(xs, ys)
    if abs(r) < MIN_R:
        return None
    strength = "forte" if abs(r) >= 0.6 else "moderada"
    together = (
        "andam juntos: quando um sobe, o outro sobe também"
        if r > 0
        else ("andam em direções opostas: quando um sobe, o outro cai")
    )
    return Insight(
        id=f"corr__{x}__{y}",
        kind="correlation",
        text=(f"{x_label} e {y_label} {together} (correlação {strength}, r = {_fmt(r, 2)})."),
        strength=min(abs(r), 1.0),
        positive=None,  # a correlation describes a link, not good or bad news
        x=x,
        y=y,
        details={"r": round(r, 3), "n": len(pairs), "points": [[a, b] for a, b in pairs]},
    )


def find_insights(rows: Sequence[Row]) -> list[dict[str, Any]]:
    found: list[Insight] = []
    for cond in CONDITIONS:
        for out in OUTCOMES:
            if (insight := compare(rows, cond, out)) is not None:
                found.append(insight)
    for x, y, xl, yl in CORRELATIONS:
        if (insight := correlate(rows, x, y, xl, yl)) is not None:
            found.append(insight)
    found.sort(key=lambda i: i.strength, reverse=True)
    return [asdict(i) for i in found]
