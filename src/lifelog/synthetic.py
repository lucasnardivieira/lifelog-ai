"""Generate realistic, fully fictional life-log events for the public demo.

The data has causal structure on purpose, so the "patterns" view has something real to find:
- sleep drives next-day energy and mood; exercise and social time lift mood; stress lowers it
- work weeks have deadline spikes (more stress, less sleep, less study)
- study topics follow a learning roadmap; weekends are more social; payday shows up in spending
"""

import math
import random
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from lifelog.events import Event, EventType

TZ = ZoneInfo("America/Sao_Paulo")

# (start offset in days, topic) — the study roadmap moves on every few weeks
STUDY_PLAN = [
    (0, "SQL"),
    (21, "Docker"),
    (45, "Terraform"),
    (70, "dbt"),
    (100, "Spark"),
    (130, "Kafka"),
    (155, "RAG"),
]
BOOKS = [
    ("Fundamentals of Data Engineering", 450),
    ("The Data Warehouse Toolkit", 600),
    ("Atomic Habits", 320),
    ("AI Engineering", 530),
    ("O Hobbit", 300),
]
EXERCISES = [
    ("corrida", 35, 0.35),
    ("academia", 60, 0.4),
    ("bike", 50, 0.15),
    ("caminhada", 40, 0.1),
]
SOCIAL = [
    ("namorado", ["jantar a dois", "filme em casa", "cinema", "passeio no parque"], 0.45),
    ("amigos", ["happy hour", "churrasco", "jogos de tabuleiro", "show"], 0.3),
    ("família", ["almoço de domingo", "aniversário", "ligação longa"], 0.2),
    ("trabalho", ["café com o time", "almoço com colegas"], 0.05),
]
GRATITUDE = [
    "o café da manhã com calma",
    "uma conversa boa com o namorado",
    "ter terminado um módulo de estudo",
    "o dia de sol",
    "a saúde da família",
    "um treino que rendeu",
    "um elogio no trabalho",
    "ter dormido bem",
]
JOURNAL_GOOD = [
    "Dia produtivo, consegui focar de manhã.",
    "Me senti leve hoje. Treino + estudo fizeram diferença.",
    "Aprendi algo novo e consegui aplicar no projeto.",
]
JOURNAL_BAD = [
    "Cansado, rendi pouco. Preciso dormir mais cedo.",
    "Semana pesada no trabalho, cabeça cheia.",
    "Ansioso com prazos, deixei o estudo de lado.",
]
MEALS = [("saudável", 0.5), ("ok", 0.35), ("besteira", 0.15)]
EXPENSES = {
    "alimentação": (18, 60, ["padaria", "restaurante", "lanchonete", "iFood"]),
    "mercado": (120, 420, ["mercado", "hortifruti"]),
    "transporte": (8, 45, ["Uber", "metrô", "combustível"]),
    "lazer": (30, 180, ["cinema", "bar", "show", "livraria"]),
    "saúde": (40, 250, ["farmácia", "consulta"]),
    "compras": (40, 400, ["loja online", "roupa"]),
}
FIXED = [  # (day of month, category, label, amount)
    (1, "moradia", "aluguel", 2200.0),
    (10, "contas", "luz + internet", 310.0),
    (12, "assinaturas", "streaming + nuvem", 89.9),
]
SALARY_DAY = 5


@dataclass
class _State:
    rng: random.Random
    deadline_days: set[int] = field(default_factory=set)
    book_index: int = 0
    book_pages_read: int = 0
    seq: int = 0


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _score(x: float) -> int:
    return int(round(_clip(x, 1, 5)))


def _topic(day_index: int) -> str:
    return [topic for start, topic in STUDY_PLAN if start <= day_index][-1]


def _weighted(rng: random.Random, items: list[tuple]) -> tuple:
    return rng.choices(items, weights=[item[-1] for item in items])[0]


def _at(day: date, hour: float) -> datetime:
    h = int(hour)
    m = int((hour - h) * 60)
    return datetime.combine(day, time(h % 24, m), tzinfo=TZ)


def _fmt_hours(hours: float) -> str:
    h, m = int(hours), int(round((hours - int(hours)) * 60))
    return f"{h}h{m:02d}" if m else f"{h}h"


def generate(end: date, days: int = 183, seed: int = 42) -> list[Event]:
    """Events for the ``days`` days ending on ``end`` (inclusive), deterministic for a seed."""
    rng = random.Random(seed)
    state = _State(rng=rng)
    # ~1 deadline week per month
    for start in range(10, days, 30):
        offset = start + rng.randint(-4, 6)
        state.deadline_days.update(range(offset, offset + 5))

    events: list[Event] = []
    prev_sleep = 7.0
    for i in range(days):
        day = end - timedelta(days=days - 1 - i)
        events.extend(_day_events(state, day, i, prev_sleep))
        prev_sleep = next(e.hours for e in events[::-1] if e.type == EventType.SLEEP)
    return events


def _day_events(st: _State, day: date, i: int, prev_sleep: float) -> Iterator[Event]:
    rng = st.rng
    weekend = day.weekday() >= 5
    deadline = i in st.deadline_days

    def ev(etype: EventType, hour: float, raw: str, **fields) -> Event:
        st.seq += 1
        return Event(
            event_id=f"syn-{day:%Y%m%d}-{st.seq:05d}",
            occurred_at=_at(day, hour),
            type=etype,
            source="synthetic",
            raw_text=raw,
            **fields,
        )

    # --- body: sleep (logged in the morning, about last night) ---
    season = 0.25 * math.sin(i / 20)  # slow drift so trends are visible
    sleep = rng.gauss(7.0 + (0.7 if weekend else 0) - (0.9 if deadline else 0) + season, 0.75)
    sleep = round(_clip(sleep, 4.0, 10.0) * 4) / 4
    quality = _score(3 + (sleep - 7) * 0.8 + rng.gauss(0, 0.6))
    yield ev(
        EventType.SLEEP,
        7.5 + rng.random(),
        f"dormi {_fmt_hours(sleep)}" + (", acordei cansado" if quality <= 2 else ""),
        hours=sleep,
        score=quality,
    )

    exercised = rng.random() < (0.35 if weekend else 0.5) - (0.2 if deadline else 0) + (
        0.1 if sleep >= 7 else -0.1
    )
    if exercised:
        kind, base, _ = _weighted(rng, EXERCISES)
        minutes = int(_clip(rng.gauss(base, 12), 15, 120))
        yield ev(
            EventType.EXERCISE,
            6.5 + rng.random() if not weekend else 9 + rng.random() * 2,
            f"{kind} {minutes}min",
            minutes=minutes,
            category=kind,
        )

    energy = _score(3 + (sleep - 7) * 0.55 + (0.5 if exercised else 0) + rng.gauss(0, 0.6))
    yield ev(EventType.ENERGY, 11 + rng.random(), f"energia {energy}/5", score=energy)

    for meal_hour in (12.5, 20):
        if rng.random() < 0.6:
            kind = _weighted(rng, MEALS)[0]
            if deadline and rng.random() < 0.4:
                kind = "besteira"
            yield ev(
                EventType.MEAL,
                meal_hour + rng.random(),
                f"{'almoço' if meal_hour < 15 else 'jantar'} {kind}",
                category=kind,
            )

    # --- growth ---
    if not weekend:
        work = int(_clip(rng.gauss(500 if deadline else 450, 35), 300, 660))
        yield ev(
            EventType.WORK,
            18 + rng.random(),
            f"trabalhei {_fmt_hours(work / 60)}",
            minutes=work,
            category="prazo" if deadline else "rotina",
        )

    study_p = (0.45 if weekend else 0.8) - (0.35 if deadline else 0) + (0.1 if sleep >= 7 else -0.1)
    topic = _topic(i)
    if rng.random() < study_p:
        sessions = 1 if weekend or rng.random() < 0.6 else 2
        for s in range(sessions):
            minutes = int(_clip(rng.gauss(60 if weekend else 50, 18), 20, 150))
            yield ev(
                EventType.STUDY,
                (20 if not weekend else 10) + s * 1.5 + rng.random(),
                f"estudei {topic} {minutes}min",
                minutes=minutes,
                category=topic,
            )

    if rng.random() < 0.55 and st.book_index < len(BOOKS):
        title, total = BOOKS[st.book_index]
        pages = int(_clip(rng.gauss(25 if weekend else 15, 8), 4, 70))
        st.book_pages_read += pages
        yield ev(
            EventType.READING,
            22.5 + rng.random() * 0.8,
            f"li {pages} páginas de {title}",
            pages=pages,
            label=title,
        )
        if st.book_pages_read >= total:
            st.book_index += 1
            st.book_pages_read = 0

    # --- money & social ---
    social_p = 0.65 if weekend else 0.15 + (0.1 if day.weekday() == 4 else 0)
    social_events = []
    if rng.random() < social_p:
        who, activities, _ = _weighted(rng, SOCIAL)
        activity = rng.choice(activities)
        social_events.append(who)
        yield ev(
            EventType.SOCIAL,
            (19 if not weekend else 13) + rng.random() * 3,
            f"{activity} com {who}" if who != "família" else f"{activity} em família",
            category=who,
            label=activity,
        )

    if day.day == SALARY_DAY:
        yield ev(
            EventType.INCOME,
            9.0,
            "caiu o salário",
            amount=9800.0,
            currency="BRL",
            category="salário",
        )
    for dom, cat, label, amount in FIXED:
        if day.day == dom:
            yield ev(
                EventType.EXPENSE,
                10 + rng.random(),
                f"paguei {label} R$ {amount:.0f}",
                amount=amount,
                currency="BRL",
                category=cat,
                label=label,
            )

    # payday week spends more
    spend_boost = 1.4 if SALARY_DAY <= day.day <= SALARY_DAY + 6 else 1.0
    n_expenses = rng.choices([0, 1, 2, 3], weights=[2, 4, 3, 1])[0]
    if social_events:
        n_expenses += 1
    for _ in range(n_expenses):
        cat = rng.choices(
            list(EXPENSES),
            weights=[
                5,
                1.2 if day.weekday() == 5 else 0.3,
                3,
                2 if weekend or social_events else 0.6,
                0.4,
                0.6,
            ],
        )[0]
        lo, hi, merchants = EXPENSES[cat]
        amount = round(rng.uniform(lo, hi) * (spend_boost if cat in ("lazer", "compras") else 1), 2)
        merchant = rng.choice(merchants)
        yield ev(
            EventType.EXPENSE,
            11 + rng.random() * 10,
            f"gastei {amount:.0f} no {merchant}",
            amount=amount,
            currency="BRL",
            category=cat,
            label=merchant,
        )

    # --- mind (end of day, depends on everything above) ---
    stress = _score(2.4 + (1.6 if deadline else 0) - (0.6 if weekend else 0) + rng.gauss(0, 0.6))
    mood_x = (
        3.1
        + (sleep - 7) * 0.45
        + (prev_sleep - 7) * 0.15
        + (0.45 if exercised else 0)
        + (0.55 if social_events else 0)
        - (stress - 3) * 0.35
        + rng.gauss(0, 0.5)
    )
    mood = _score(mood_x)
    yield ev(EventType.STRESS, 18.5 + rng.random(), f"estresse {stress}/5", score=stress)
    yield ev(EventType.MOOD, 21.5 + rng.random(), f"humor {mood}/5", score=mood)

    if rng.random() < 0.35:
        thing = rng.choice(GRATITUDE)
        yield ev(EventType.GRATITUDE, 22 + rng.random(), f"grato por {thing}", note=thing)
    if rng.random() < 0.25:
        text = rng.choice(
            JOURNAL_GOOD if mood >= 4 else JOURNAL_BAD if mood <= 2 else JOURNAL_GOOD + JOURNAL_BAD
        )
        yield ev(EventType.JOURNAL, 23 + rng.random() * 0.5, text, note=text)


def to_jsonl(events: list[Event]) -> str:
    events = sorted(events, key=lambda e: (e.occurred_at, e.event_id))
    return "".join(e.model_dump_json(exclude_none=True) + "\n" for e in events)
