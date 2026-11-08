"""Find within-person patterns between life tracks and phrase them in Brazilian Portuguese.

Method (see docs/research/psychology-foundations.md §8):
- **Within-person, detrended:** each outcome is compared to *your own* trailing 28-day average
  (excluding the day itself), so slow trends aren't mistaken for effects (Curran & Bauer, 2011).
- **Lag-aware:** a condition on day D can be tested against the outcome on day D+1
  (e.g. "screens off tonight" → tomorrow's sleep-onset latency).
- **Honest uncertainty:** effect size (Cohen's d), bootstrap 95% CI of the difference, minimum
  days per group; only effects whose CI excludes zero are reported, always as association.
"""

import random
import zlib
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from statistics import correlation, fmean, pstdev
from typing import Any

Row = dict[str, Any]

MIN_DAYS = 10
MIN_EFFECT = 0.25  # Cohen's d
MIN_R = 0.3
BASELINE_DAYS = 28
BOOTSTRAP = 1000


@dataclass(frozen=True)
class Condition:
    key: str
    yes: str  # short UI label
    no: str
    clause: str  # opens the sentence
    test: Callable[[Row], bool | None]  # None = day not comparable
    lag: int = 0  # 1 = compare against the next day's outcome
    construct: str = ""  # psychology reference shown in the UI
    skip: frozenset[str] = frozenset()  # outcomes that would be tautological for this condition


@dataclass(frozen=True)
class Outcome:
    key: str
    label: str
    article: str  # "seu" / "sua"
    unit: str
    higher_is_better: bool = True
    decimals: int = 1


def _has_data(r: Row) -> bool:
    return r.get("event_count") is not None


CONDITIONS = [
    Condition(
        "slept_7h",
        "dormiu 7h+",
        "dormiu menos de 7h",
        "Nos dias em que você dormiu 7h ou mais",
        lambda r: None if r.get("sleep_hours") is None else r["sleep_hours"] >= 7,
        construct="sono",
    ),
    Condition(
        "exercised",
        "treinou",
        "não treinou",
        "Nos dias em que você treinou",
        lambda r: None if not _has_data(r) else (r.get("exercise_minutes") or 0) > 0,
        construct="atividade física",
    ),
    Condition(
        "exercised_yesterday",
        "treinou ontem",
        "não treinou ontem",
        "No dia seguinte a um treino",
        lambda r: None if not _has_data(r) else (r.get("exercise_minutes") or 0) > 0,
        lag=1,
        construct="atividade física",
    ),
    Condition(
        "pleasant_yesterday",
        "atividades prazerosas ontem",
        "ontem sem muito prazer",
        "No dia seguinte a atividades que te deram prazer (7+/10)",
        lambda r: None if r.get("activity_pleasure") is None else r["activity_pleasure"] >= 7,
        lag=1,
        construct="ativação comportamental",
    ),
    Condition(
        "social",
        "com programa social",
        "sem programa social",
        "Nos dias em que você encontrou alguém",
        lambda r: None if not _has_data(r) else (r.get("social_count") or 0) > 0,
        construct="vínculo",
    ),
    Condition(
        "low_autonomy",
        "pouca autonomia",
        "autonomia ok",
        "Nos dias em que você sentiu pouca autonomia (≤ 2/5)",
        lambda r: None if r.get("autonomy") is None else r["autonomy"] <= 2,
        construct="autodeterminação",
    ),
    Condition(
        "high_relatedness",
        "muito vínculo",
        "vínculo normal",
        "Nos dias em que você se sentiu muito conectado(a) às pessoas (≥ 4/5)",
        lambda r: None if r.get("relatedness") is None else r["relatedness"] >= 4,
        construct="autodeterminação",
    ),
    Condition(
        "deadline",
        "dia de prazo",
        "dia normal",
        "Nos dias de prazo apertado no trabalho",
        lambda r: None if r.get("is_weekend") or not _has_data(r) else bool(r.get("is_deadline")),
        construct="estresse",
    ),
    Condition(
        "screens_off",
        "sem telas às 22h",
        "com telas à noite",
        "Depois das noites sem telas após as 22h",
        lambda r: r.get("habit__sem telas após 22h"),
        lag=1,
        construct="higiene do sono",
    ),
    Condition(
        "meditated",
        "meditou",
        "não meditou",
        "Nos dias em que você meditou",
        lambda r: r.get("habit__meditar 10 min"),
        construct="hábitos",
    ),
    Condition(
        "weekend",
        "fim de semana",
        "dia de semana",
        "Nos fins de semana",
        lambda r: None if not _has_data(r) else r["is_weekend"],
    ),
]

OUTCOMES = [
    Outcome("mood", "humor", "seu", " pts"),
    Outcome("energy", "energia", "sua", " pts"),
    Outcome("stress", "estresse", "seu", " pts", higher_is_better=False),
    Outcome(
        "sleep_onset_minutes",
        "tempo para pegar no sono",
        "seu",
        " min",
        higher_is_better=False,
        decimals=0,
    ),
    Outcome("sleep_efficiency", "eficiência do sono", "sua", " p.p.", decimals=1),
    Outcome("study_minutes", "tempo de estudo", "seu", " min", decimals=0),
    Outcome("spend_discretionary", "gasto variável", "seu", "", higher_is_better=False, decimals=0),
]

CORRELATIONS = [
    ("sleep_hours", "mood", "Horas de sono", "humor"),
    ("sleep_hours", "energy", "Horas de sono", "energia"),
    ("stress", "mood", "Estresse", "humor"),
    ("autonomy", "mood", "Autonomia", "humor"),
    ("relatedness", "mood", "Vínculo", "humor"),
    ("competence", "mood", "Competência", "humor"),
    ("stress", "sleep_onset_minutes", "Estresse", "tempo para pegar no sono"),
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
    construct: str
    details: dict[str, Any]


def _fmt(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def _money(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", ".")


def detrend(rows: Sequence[Row], key: str, window: int = BASELINE_DAYS) -> list[float | None]:
    """Value minus the mean of the previous ``window`` days (needs ≥ 7 of them)."""
    out: list[float | None] = []
    for i, row in enumerate(rows):
        value = row.get(key)
        past = [r[key] for r in rows[max(0, i - window) : i] if r.get(key) is not None]
        out.append(None if value is None or len(past) < 7 else float(value) - fmean(past))
    return out


def _bootstrap_ci(yes: list[float], no: list[float], seed: int) -> tuple[float, float]:
    rng = random.Random(seed)
    diffs = sorted(
        fmean(rng.choices(yes, k=len(yes))) - fmean(rng.choices(no, k=len(no)))
        for _ in range(BOOTSTRAP)
    )
    return diffs[int(0.025 * BOOTSTRAP)], diffs[int(0.975 * BOOTSTRAP) - 1]


def compare(
    rows: Sequence[Row], cond: Condition, out: Outcome, deviations: list[float | None]
) -> Insight | None:
    yes, no = [], []
    for i, row in enumerate(rows):
        j = i + cond.lag
        if j >= len(rows):
            break
        flag, value = cond.test(row), deviations[j]
        if flag is None or value is None:
            continue
        (yes if flag else no).append(value)
    if len(yes) < MIN_DAYS or len(no) < MIN_DAYS:
        return None
    pooled = pstdev(yes + no)
    if pooled == 0:
        return None
    diff = fmean(yes) - fmean(no)
    d = diff / pooled
    if abs(d) < MIN_EFFECT:
        return None
    lo, hi = _bootstrap_ci(yes, no, seed=zlib.crc32(f"{cond.key}/{out.key}".encode()))
    if lo <= 0 <= hi:
        return None

    more = "maior" if diff > 0 else "menor"
    if out.key == "spend_discretionary":
        amount = _money(abs(diff))
    else:
        amount = _fmt(abs(diff), out.decimals) + out.unit
    text = f"{cond.clause}, {out.article} {out.label} ficou {amount} {more} do que nos outros dias."
    return Insight(
        id=f"{cond.key}__{out.key}",
        kind="compare",
        text=text,
        strength=min(abs(d) / 1.2, 1.0),
        positive=(diff > 0) == out.higher_is_better,
        x=cond.key,
        y=out.key,
        construct=cond.construct,
        details={
            "yes": {"label": cond.yes, "mean_deviation": round(fmean(yes), 2), "days": len(yes)},
            "no": {"label": cond.no, "mean_deviation": round(fmean(no), 2), "days": len(no)},
            "difference": round(diff, 2),
            "ci95": [round(lo, 2), round(hi, 2)],
            "effect_size": round(d, 2),
            "lag_days": cond.lag,
            "unit": out.unit.strip(),
            "outcome_label": out.label,
        },
    )


def correlate(rows: Sequence[Row], x: str, y: str, x_label: str, y_label: str) -> Insight | None:
    dx, dy = detrend(rows, x), detrend(rows, y)
    pairs = [(a, b) for a, b in zip(dx, dy, strict=True) if a is not None and b is not None]
    if len(pairs) < MIN_DAYS * 3:
        return None
    xs, ys = zip(*pairs, strict=True)
    if pstdev(xs) == 0 or pstdev(ys) == 0:
        return None
    r = correlation(xs, ys)
    if abs(r) < MIN_R:
        return None
    strength = "forte" if abs(r) >= 0.6 else "moderada"
    together = (
        "andam juntos: quando um sobe acima do seu normal, o outro tende a subir"
        if r > 0
        else "andam em direções opostas: quando um sobe, o outro tende a cair"
    )
    raw = [(row[x], row[y]) for row in rows if row.get(x) is not None and row.get(y) is not None]
    return Insight(
        id=f"corr__{x}__{y}",
        kind="correlation",
        text=f"{x_label} e {y_label} {together} (correlação {strength}, r = {_fmt(r, 2)}).",
        strength=min(abs(r), 1.0),
        positive=None,
        x=x,
        y=y,
        construct="",
        details={"r": round(r, 3), "n": len(pairs), "points": [[a, b] for a, b in raw]},
    )


def find_insights(rows: Sequence[Row]) -> list[dict[str, Any]]:
    deviations = {out.key: detrend(rows, out.key) for out in OUTCOMES}
    found: list[Insight] = []
    for cond in CONDITIONS:
        for out in OUTCOMES:
            if out.key in cond.skip:
                continue
            insight = compare(rows, cond, out, deviations[out.key])
            if insight is not None:
                found.append(insight)
    for x, y, xl, yl in CORRELATIONS:
        if (insight := correlate(rows, x, y, xl, yl)) is not None:
            found.append(insight)
    found.sort(key=lambda i: i.strength, reverse=True)
    return [asdict(i) for i in found]
