"""Button-driven check-ins as pure data + finalize functions (no Telegram imports, easy to test).

A Flow is a list of Steps; each answer is stored under the step key; `finalize(values, now)`
turns the answers into contract events. Item wording for WHO-5 and PSS-10 follows the published
Brazilian Portuguese versions (verify against the sources listed in the research note).
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from lifelog.emotions import QUADRANTS, quadrant, words_in
from lifelog.events import Event, EventType
from lifelog.storage.jsonl import new_event_id

Values = dict[str, Any]


@dataclass(frozen=True)
class Step:
    key: str
    question: str | Callable[[Values], str]
    options: list[tuple[str, Any]] | Callable[[Values], list[tuple[str, Any]]]
    columns: int = 3
    multi: bool = False  # multi-select with a "pronto" button
    max_selected: int = 3

    def text(self, values: Values) -> str:
        return self.question(values) if callable(self.question) else self.question

    def choices(self, values: Values) -> list[tuple[str, Any]]:
        return self.options(values) if callable(self.options) else self.options


@dataclass(frozen=True)
class Flow:
    key: str
    title: str
    steps: list[Step]
    finalize: Callable[[Values, datetime], list[Event]]
    done_message: str = "Registrado ✅"
    extra: dict[str, Any] = field(default_factory=dict)


def _ev(etype: EventType, now: datetime, raw: str, **fields: Any) -> Event:
    return Event(
        event_id=new_event_id(),
        occurred_at=now,
        type=etype,
        source="telegram",
        raw_text=raw,
        **fields,
    )


def _half_hours(start: float, end: float) -> list[tuple[str, str]]:
    out, h = [], start
    while h <= end:
        hh = int(h) % 24
        label = f"{hh:02d}:{int(round((h - int(h)) * 60)):02d}"
        out.append((label, label))
        h += 0.5
    return out


def _minutes_of(hhmm: str) -> int:
    hh, mm = (int(x) for x in hhmm.split(":"))
    return hh * 60 + mm


LIKERT5 = [("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)]
QUALITY = [("1 péssima", 1), ("2 ruim", 2), ("3 ok", 3), ("4 boa", 4), ("5 ótima", 5)]

# ---------------------------------------------------------------- sleep (Consensus Sleep Diary)


def sleep_hours(v: Values) -> float:
    in_bed = (_minutes_of(v["wake_time"]) - _minutes_of(v["bedtime"])) % 1440
    asleep = in_bed - v["sol_minutes"] - v["waso_minutes"]
    return round(max(asleep, 0) / 60 * 4) / 4


def _finalize_sleep(v: Values, now: datetime) -> list[Event]:
    hours = sleep_hours(v)
    raw = (
        f"deitei {v['bedtime']}, acordei {v['wake_time']}, {v['sol_minutes']} min para dormir, "
        f"{v['awakenings']} despertar(es)"
    )
    return [
        _ev(
            EventType.SLEEP,
            now,
            raw,
            hours=hours,
            bedtime=v["bedtime"],
            wake_time=v["wake_time"],
            sol_minutes=v["sol_minutes"],
            awakenings=v["awakenings"],
            waso_minutes=v["waso_minutes"],
            score=v["quality"],
            rested=v["rested"],
        )
    ]


SLEEP = Flow(
    key="sleep",
    title="😴 Diário de sono",
    steps=[
        Step("bedtime", "A que horas você <b>apagou a luz</b> ontem?", _half_hours(21.0, 26.5), 4),
        Step(
            "sol_minutes",
            "Quanto tempo levou para <b>pegar no sono</b>?",
            [
                ("5 min", 5),
                ("15 min", 15),
                ("30 min", 30),
                ("45 min", 45),
                ("1h", 60),
                ("1h30+", 90),
            ],
        ),
        Step(
            "awakenings",
            "Quantas vezes você <b>acordou</b> durante a noite?",
            [("0", 0), ("1", 1), ("2", 2), ("3+", 3)],
            4,
        ),
        Step(
            "waso_minutes",
            "Somando, quanto tempo ficou <b>acordado(a)</b> no meio da noite?",
            [("nada", 0), ("10 min", 10), ("20 min", 20), ("40 min", 40), ("1h+", 60)],
        ),
        Step("wake_time", "A que horas você <b>acordou de vez</b>?", _half_hours(4.5, 11.0), 4),
        Step("quality", "Como foi a <b>qualidade</b> do sono?", QUALITY, 3),
        Step("rested", "Quão <b>descansado(a)</b> você acordou? (1 nada · 5 muito)", LIKERT5, 5),
    ],
    finalize=_finalize_sleep,
    done_message="Sono registrado ✅",
)

# ---------------------------------------------------------------- affect (circumplex + words)

QUAD_SQUARE = {"yellow": "🟨", "red": "🟥", "blue": "🟦", "green": "🟩"}


def affect_grid() -> list[tuple[str, str]]:
    """4×4 grid, top row = most energy; columns = most unpleasant → most pleasant (no neutral)."""
    cells = []
    for arousal in (2, 1, -1, -2):
        for valence in (-2, -1, 1, 2):
            square = QUAD_SQUARE[quadrant(valence, arousal)]
            strength = "●" if abs(valence) == 2 and abs(arousal) == 2 else "•"
            cells.append((f"{square}{strength}", f"{valence},{arousal}"))
    return cells


AFFECT_HELP = (
    "Como você está <b>agora</b>?\n"
    "↔ desagradável … agradável · ↕ energia baixa … alta\n"
    "🟨 animado · 🟥 tenso · 🟦 pra baixo · 🟩 calmo  (● = bem intenso)"
)


def _words_for(v: Values) -> list[tuple[str, str]]:
    valence, arousal = (int(x) for x in v["grid"].split(","))
    return [(w, w) for w in words_in(quadrant(valence, arousal))]


def _words_question(v: Values) -> str:
    valence, arousal = (int(x) for x in v["grid"].split(","))
    q = quadrant(valence, arousal)
    return (
        f"{QUAD_SQUARE[q]} {QUADRANTS[q]['label']}.\n"
        "Qual palavra descreve melhor? Escolha até 3 e toque em <b>pronto</b>. "
        "Nomear com precisão ajuda a entender o que você sente."
    )


def _finalize_affect(v: Values, now: datetime) -> list[Event]:
    valence, arousal = (int(x) for x in v["grid"].split(","))
    words = list(v.get("words") or [])
    raw = f"me sinto {' e '.join(words)}" if words else "check-in de afeto"
    return [
        _ev(EventType.AFFECT, now, raw, valence=valence, arousal=arousal, emotions=words or None)
    ]


AFFECT = Flow(
    key="affect",
    title="◐ Check-in",
    steps=[
        Step("grid", AFFECT_HELP, lambda _: affect_grid(), 4),
        Step("words", _words_question, _words_for, 3, multi=True),
    ],
    finalize=_finalize_affect,
    done_message="Check-in registrado ✅",
)

# ---------------------------------------------------------------- end of day (on demand)


def close_flow(habits: list[dict[str, str]]) -> Flow:
    names = [h["name"] for h in habits if h.get("active", True)]

    def finalize(v: Values, now: datetime) -> list[Event]:
        events = [
            _ev(EventType.STRESS, now, f"estresse {v['stress']}/5", score=v["stress"]),
            _ev(
                EventType.NEEDS,
                now,
                f"autonomia {v['autonomy']}, competência {v['competence']}, vínculo {v['relatedness']}",
                autonomy=v["autonomy"],
                competence=v["competence"],
                relatedness=v["relatedness"],
            ),
        ]
        done = set(v.get("habits") or [])
        plans = {h["name"]: h.get("if_then") for h in habits}
        for name in names:
            events.append(
                _ev(
                    EventType.HABIT,
                    now,
                    f"{'✓' if name in done else '✗'} {name}",
                    habit=name,
                    done=name in done,
                    if_then=plans.get(name),
                )
            )
        return events

    steps = [
        Step("stress", "Quanto <b>estresse</b> hoje? (1 pouco · 5 muito)", LIKERT5, 5),
        Step(
            "autonomy",
            "Hoje você fez as coisas <b>por escolha própria</b>? (1 nada · 5 muito)",
            LIKERT5,
            5,
        ),
        Step(
            "competence",
            "Hoje você se sentiu <b>capaz e eficaz</b>? (1 nada · 5 muito)",
            LIKERT5,
            5,
        ),
        Step(
            "relatedness",
            "Hoje você se sentiu <b>próximo(a) de pessoas importantes</b>? (1–5)",
            LIKERT5,
            5,
        ),
    ]
    if names:
        steps.append(
            Step(
                "habits",
                "Quais <b>hábitos</b> você cumpriu hoje? Marque e toque em <b>pronto</b>.",
                [(n, n) for n in names],
                1,
                multi=True,
                max_selected=len(names),
            )
        )
    return Flow("close", "🌙 Fechamento do dia", steps, finalize, "Dia fechado ✅ Bom descanso.")


# ---------------------------------------------------------------- validated questionnaires

WHO5_ITEMS = [
    "Eu me senti alegre e de bom humor",
    "Eu me senti calmo(a) e tranquilo(a)",
    "Eu me senti ativo(a) e enérgico(a)",
    "Eu acordei me sentindo descansado(a) e revigorado(a)",
    "Meu dia a dia foi preenchido com coisas que me interessam",
]
WHO5_OPTIONS = [
    ("Todo o tempo", 5),
    ("A maior parte do tempo", 4),
    ("Mais da metade do tempo", 3),
    ("Menos da metade do tempo", 2),
    ("De vez em quando", 1),
    ("Nunca", 0),
]

PSS10_ITEMS = [
    "você ficou triste por causa de algo que aconteceu inesperadamente?",
    "você se sentiu incapaz de controlar as coisas importantes em sua vida?",
    "você se sentiu nervoso(a) e “estressado(a)”?",
    "você se sentiu confiante na sua habilidade de resolver problemas pessoais?",
    "você sentiu que as coisas estavam acontecendo de acordo com a sua vontade?",
    "você achou que não conseguiria lidar com todas as coisas que você tem que fazer?",
    "você foi capaz de controlar irritações em sua vida?",
    "você sentiu que as coisas estavam sob o seu controle?",
    "você ficou irritado(a) porque as coisas que aconteceram estavam fora do seu controle?",
    "você sentiu que as dificuldades se acumularam a ponto de você acreditar que não poderia superá-las?",
]
PSS10_OPTIONS = [
    ("Nunca", 0),
    ("Quase nunca", 1),
    ("Às vezes", 2),
    ("Pouco frequente", 3),
    ("Muito frequente", 4),
]


def _assessment(
    instrument: str, keys: list[str], label: str
) -> Callable[[Values, datetime], list[Event]]:
    def finalize(v: Values, now: datetime) -> list[Event]:
        responses = [int(v[k]) for k in keys]
        return [_ev(EventType.ASSESSMENT, now, label, instrument=instrument, responses=responses)]

    return finalize


WHO5 = Flow(
    key="who5",
    title="♡ WHO-5 — bem-estar",
    steps=[
        Step(f"q{i}", f"<b>Nas últimas duas semanas</b> ({i + 1}/5):\n{text}", WHO5_OPTIONS, 2)
        for i, text in enumerate(WHO5_ITEMS)
    ],
    finalize=_assessment("who5", [f"q{i}" for i in range(5)], "WHO-5 semanal"),
    done_message="Obrigado! WHO-5 registrado ✅ (é sobre bem-estar, não um diagnóstico)",
)

PSS10 = Flow(
    key="pss10",
    title="🌡️ PSS-10 — estresse percebido",
    steps=[
        Step(
            f"q{i}",
            f"<b>No último mês</b>, com que frequência ({i + 1}/10)…\n{text}",
            PSS10_OPTIONS,
            2,
        )
        for i, text in enumerate(PSS10_ITEMS)
    ],
    finalize=_assessment("pss10", [f"q{i}" for i in range(10)], "PSS-10 do mês"),
    done_message="PSS-10 registrado ✅",
)

LIFE_SATISFACTION = Flow(
    key="life",
    title="⭐ Satisfação com a vida",
    steps=[
        Step(
            "score",
            "No geral, <b>quão satisfeito(a) você está com sua vida</b> hoje? (0 nada · 10 totalmente)",
            [(str(i), i) for i in range(11)],
            6,
        )
    ],
    finalize=lambda v, now: [
        _ev(
            EventType.ASSESSMENT,
            now,
            f"satisfação com a vida {v['score']}/10",
            instrument="life_satisfaction",
            responses=[int(v["score"])],
        )
    ],
    done_message="Registrado ✅",
)

STATIC_FLOWS = {f.key: f for f in (SLEEP, AFFECT, WHO5, PSS10, LIFE_SATISFACTION)}


def is_last_day_of_month(now: datetime) -> bool:
    return (now + timedelta(days=1)).month != now.month
