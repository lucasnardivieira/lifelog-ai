"""Generate realistic, fully fictional life-log events for the public demo.

The data has causal structure on purpose, so the "Padrões" view has something real to find:
- sleep (Consensus Sleep Diary fields) drives energy, arousal and valence
- SDT needs (autonomy, competence, relatedness) feed into valence; deadlines erode autonomy
- yesterday's enjoyable activities lift today's valence (behavioral activation finding)
- deadline weeks raise stress (high-arousal unpleasant affect), cut sleep and study
- habits strengthen gradually (Lally-style asymptotic curve) and survive missed days
- emotion vocabulary widens over the months (growing emotional granularity)
- weekly WHO-5 and monthly PSS-10 / life satisfaction follow the underlying state
"""

import math
import random
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from statistics import fmean
from zoneinfo import ZoneInfo

from lifelog.emotions import EMOTIONS, quadrant
from lifelog.events import Event, EventType

TZ = ZoneInfo("America/Sao_Paulo")

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
# (name, if-then plan, start day, base probability once established)
HABITS = [
    ("meditar 10 min", "Se eu terminar o café da manhã, então medito 10 minutos.", 20, 0.8),
    ("sem telas após 22h", "Se forem 22h, então deixo o celular carregando na sala.", 60, 0.7),
    ("2L de água", "Se eu sentar para trabalhar, então encho a garrafa de água.", 95, 0.85),
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
# structured journaling (what happened → what I felt → what I can do), not open rumination
JOURNAL_GOOD = [
    "Aconteceu: terminei o exercício de dbt. Senti: orgulho. Próximo passo: aplicar no projeto.",
    "Aconteceu: treino cedo + estudo. Senti: energia o dia todo. Próximo passo: repetir amanhã.",
    "Aconteceu: jantar com o namorado. Senti: leveza. Próximo passo: marcar mais vezes.",
]
JOURNAL_BAD = [
    "Aconteceu: dormi mal. Senti: irritação. Próximo passo: desligar telas às 22h.",
    "Aconteceu: prazo apertado. Senti: sobrecarga. Próximo passo: listar 3 prioridades amanhã.",
    "Aconteceu: pulei o estudo. Senti: culpa. Próximo passo: 25 min amanhã de manhã, sem cobrança.",
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
FIXED = [
    (1, "moradia", "aluguel", 2200.0),
    (10, "contas", "luz + internet", 310.0),
    (12, "assinaturas", "streaming + nuvem", 89.9),
]
SALARY_DAY = 5
PSS_REVERSED = {3, 4, 6, 7}  # 0-based positions of PSS-10 items 4, 5, 7, 8


@dataclass
class _State:
    rng: random.Random
    days: int
    deadline_days: set[int] = field(default_factory=set)
    book_index: int = 0
    book_pages_read: int = 0
    seq: int = 0
    habit_strength: dict[str, float] = field(default_factory=dict)
    yesterday_pleasure: float = 5.0
    screens_off_last_night: bool = False
    week_valence: list[float] = field(default_factory=list)
    week_energy: list[float] = field(default_factory=list)
    week_sleep: list[float] = field(default_factory=list)
    month_stress: list[float] = field(default_factory=list)
    month_valence: list[float] = field(default_factory=list)


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _likert(x: float, lo: int = 1, hi: int = 5) -> int:
    return int(round(_clip(x, lo, hi)))


def _topic(day_index: int) -> str:
    return [topic for start, topic in STUDY_PLAN if start <= day_index][-1]


def _weighted(rng: random.Random, items: list[tuple]) -> tuple:
    return rng.choices(items, weights=[item[-1] for item in items])[0]


def _at(day: date, hour: float) -> datetime:
    hour = _clip(hour, 0, 23.98)
    h = int(hour)
    return datetime.combine(day, time(h, int((hour - h) * 60)), tzinfo=TZ)


def _hhmm(hour: float) -> str:
    hour %= 24
    h = int(hour)
    return f"{h:02d}:{int(round((hour - h) * 60)) % 60:02d}"


def _fmt_hours(hours: float) -> str:
    h, m = int(hours), int(round((hours - int(hours)) * 60))
    return f"{h}h{m:02d}" if m else f"{h}h"


def _bipolar(x: float) -> int:
    """−2…+2 without a neutral point (like the Mood Meter): people pick a side."""
    magnitude = 2 if abs(x) >= 1.2 else 1
    return magnitude if x >= 0 else -magnitude


def _pick_emotions(rng: random.Random, valence: int, arousal: int, breadth: float) -> list[str]:
    """Words from the reported quadrant. Early on only the most common words are used; `breadth`
    (0–1) unlocks more specific ones, modelling growing emotional granularity."""
    words = [w for w, (v, a) in EMOTIONS.items() if quadrant(v, a) == quadrant(valence, arousal)]
    pool = words[: 2 + round(breadth * (len(words) - 2))]
    k = 1 if rng.random() < 0.7 - 0.35 * breadth else 2
    return rng.sample(pool, min(k, len(pool)))


def generate(end: date, days: int = 183, seed: int = 42) -> list[Event]:
    """Events for the ``days`` days ending on ``end`` (inclusive), deterministic for a seed."""
    rng = random.Random(seed)
    state = _State(rng=rng, days=days)
    for start in range(10, days, 30):
        offset = start + rng.randint(-4, 6)
        state.deadline_days.update(range(offset, offset + 5))

    events: list[Event] = []
    for i in range(days):
        day = end - timedelta(days=days - 1 - i)
        events.extend(_day_events(state, day, i))
    return events


def _day_events(st: _State, day: date, i: int) -> Iterator[Event]:
    rng = st.rng
    weekend = day.weekday() >= 5
    deadline = i in st.deadline_days
    progress = i / max(st.days - 1, 1)

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

    # --- habits (strength grows like Lally's asymptotic curve; misses don't reset) ---
    habits_done: dict[str, bool] = {}
    for name, _plan, start, base in HABITS:
        if i < start:
            continue
        s = st.habit_strength.get(name, 0.0)
        p = _clip(0.35 + (base - 0.35) * s - (0.25 if deadline else 0), 0.05, 0.97)
        done = rng.random() < p
        st.habit_strength[name] = s + 0.06 * ((1.0 if done else 0.0) - s * 0.8)
        habits_done[name] = done

    # --- sleep (Consensus Sleep Diary, logged in the morning about last night) ---
    # the morning entry describes last night, so yesterday's 22h habit is what matters
    screens_off = st.screens_off_last_night
    st.screens_off_last_night = habits_done.get("sem telas após 22h", False)
    bedtime = rng.gauss(
        23.6 + (0.9 if weekend else 0) + (0.5 if deadline else 0) - (0.4 if screens_off else 0),
        0.45,
    )
    sol = int(_clip(rng.gauss(20 + (14 if deadline else 0) - (8 if screens_off else 0), 8), 3, 90))
    awakenings = rng.choices([0, 1, 2, 3], weights=[4, 4, 2, 1 + (2 if deadline else 0)])[0]
    waso = int(_clip(awakenings * rng.gauss(14, 5) + rng.gauss(10, 4), 0, 150))
    wake = rng.gauss(8.6 if weekend else 7.0, 0.3) + 0.25 * math.sin(i / 20)
    tib = (wake + 24 - bedtime) % 24
    hours = round(_clip(tib - (sol + waso) / 60, 3.5, 10.5) * 4) / 4
    efficiency = hours / tib if tib else 1
    quality = _likert(3 + (hours - 7) * 0.7 + (efficiency - 0.88) * 8 + rng.gauss(0, 0.5))
    rested = _likert(quality + rng.gauss(0, 0.6))
    yield ev(
        EventType.SLEEP,
        wake + 0.3,
        f"dormi {_fmt_hours(hours)}, deitei {_hhmm(bedtime)}, acordei {_hhmm(wake)}"
        + (f", acordei {awakenings}x" if awakenings else ""),
        hours=hours,
        score=quality,
        bedtime=_hhmm(bedtime),
        wake_time=_hhmm(wake),
        sol_minutes=sol,
        awakenings=awakenings,
        waso_minutes=waso,
        rested=rested,
    )

    # --- body ---
    exercised = rng.random() < (0.35 if weekend else 0.5) - (0.2 if deadline else 0) + (
        0.1 if hours >= 7 else -0.1
    )
    activity_pleasure: list[float] = []
    if exercised:
        kind, base, _ = _weighted(rng, EXERCISES)
        minutes = int(_clip(rng.gauss(base, 12), 15, 120))
        pleasure = _likert(rng.gauss(6.5, 1.5), 0, 10)
        activity_pleasure.append(pleasure)
        yield ev(
            EventType.EXERCISE,
            6.5 + rng.random() if not weekend else 9 + rng.random() * 2,
            f"{kind} {minutes}min",
            minutes=minutes,
            category=kind,
            pleasure=pleasure,
            mastery=_likert(rng.gauss(6.5, 1.5), 0, 10),
        )

    energy = _likert(3 + (hours - 7) * 0.55 + (0.5 if exercised else 0) + rng.gauss(0, 0.6))
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

    study_p = (0.45 if weekend else 0.8) - (0.35 if deadline else 0) + (0.1 if hours >= 7 else -0.1)
    topic = _topic(i)
    studied = 0
    if rng.random() < study_p:
        for s in range(1 if weekend or rng.random() < 0.6 else 2):
            minutes = int(_clip(rng.gauss(60 if weekend else 50, 18), 20, 150))
            studied += minutes
            mastery = _likert(rng.gauss(5 + 2.5 * progress, 1.5), 0, 10)
            yield ev(
                EventType.STUDY,
                (20 if not weekend else 10) + s * 1.5 + rng.random(),
                f"estudei {topic} {minutes}min",
                minutes=minutes,
                category=topic,
                pleasure=_likert(rng.gauss(5.5, 1.5), 0, 10),
                mastery=mastery,
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

    for name, plan, _, _ in HABITS:
        if name in habits_done:
            done = habits_done[name]
            yield ev(
                EventType.HABIT,
                21.8 + rng.random() * 0.3,
                f"{'✓' if done else '✗'} {name}",
                habit=name,
                done=done,
                if_then=plan,
            )

    # --- money & social ---
    social_p = 0.65 if weekend else 0.15 + (0.1 if day.weekday() == 4 else 0)
    social = False
    if rng.random() < social_p:
        who, activities, _ = _weighted(rng, SOCIAL)
        activity = rng.choice(activities)
        social = True
        pleasure = _likert(rng.gauss(8 if who in ("namorado", "amigos") else 7, 1.2), 0, 10)
        activity_pleasure.append(pleasure)
        yield ev(
            EventType.SOCIAL,
            (19 if not weekend else 13) + rng.random() * 3,
            f"{activity} com {who}" if who != "família" else f"{activity} em família",
            category=who,
            label=activity,
            pleasure=pleasure,
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

    spend_boost = 1.4 if SALARY_DAY <= day.day <= SALARY_DAY + 6 else 1.0
    n_expenses = rng.choices([0, 1, 2, 3], weights=[2, 4, 3, 1])[0] + (1 if social else 0)
    for _ in range(n_expenses):
        cat = rng.choices(
            list(EXPENSES),
            weights=[
                5,
                1.2 if day.weekday() == 5 else 0.3,
                3,
                2 if weekend or social else 0.6,
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

    # --- mind ---
    stress = _likert(2.4 + (1.6 if deadline else 0) - (0.6 if weekend else 0) + rng.gauss(0, 0.6))
    autonomy = _likert(3.6 - (1.3 if deadline else 0) + (0.6 if weekend else 0) + rng.gauss(0, 0.6))
    competence = _likert(
        2.9
        + (0.5 if studied else 0)
        + (0.4 if exercised else 0)
        + 0.6 * progress
        + rng.gauss(0, 0.6)
    )
    relatedness = _likert(2.8 + (1.4 if social else 0) + rng.gauss(0, 0.6))
    meditated = habits_done.get("meditar 10 min", False)

    day_valence = (
        -0.05
        + (hours - 7) * 0.35
        + (0.35 if exercised else 0)
        + (autonomy - 3) * 0.25
        + (competence - 3) * 0.15
        + (relatedness - 3) * 0.25
        - (stress - 3) * 0.4
        + (st.yesterday_pleasure - 5) * 0.08
        + (0.15 if meditated else 0)
    )
    breadth = 0.05 + 0.9 * progress
    check_ins = [
        (8.2, 0.3 * (hours - 7) - 0.3),
        (14.5, 0.5 + (0.9 if deadline else 0)),
        (21.3, -0.6),
    ]
    valences: list[int] = []
    for hour, arousal_bias in check_ins:
        if rng.random() < (0.55 if hour < 20 else 0.95):
            v = _bipolar(day_valence + rng.gauss(0, 0.75))
            a = _bipolar(arousal_bias + (energy - 3) * 0.4 + rng.gauss(0, 0.75))
            words = _pick_emotions(rng, v, a, breadth)
            valences.append(v)
            yield ev(
                EventType.AFFECT,
                hour + rng.random() * 0.8,
                f"me sinto {' e '.join(words)}",
                valence=v,
                arousal=a,
                emotions=words,
            )

    yield ev(EventType.STRESS, 18.5 + rng.random(), f"estresse {stress}/5", score=stress)
    yield ev(
        EventType.NEEDS,
        22.2 + rng.random() * 0.3,
        f"autonomia {autonomy}, competência {competence}, vínculo {relatedness}",
        autonomy=autonomy,
        competence=competence,
        relatedness=relatedness,
    )

    if rng.random() < 0.2:
        thing = rng.choice(GRATITUDE)
        yield ev(EventType.GRATITUDE, 22 + rng.random(), f"grato por {thing}", note=thing)
    if rng.random() < 0.22:
        mean_v = fmean(valences) if valences else day_valence
        pool = (
            JOURNAL_GOOD
            if mean_v >= 0.5
            else JOURNAL_BAD
            if mean_v <= -0.5
            else (JOURNAL_GOOD + JOURNAL_BAD)
        )
        text = rng.choice(pool)
        yield ev(EventType.JOURNAL, 23 + rng.random() * 0.5, text, note=text)

    # --- validated instruments ---
    st.yesterday_pleasure = fmean(activity_pleasure) if activity_pleasure else 4.5
    st.week_valence.append(fmean(valences) if valences else day_valence)
    st.week_energy.append(energy)
    st.week_sleep.append(quality)
    st.month_stress.append(stress)
    st.month_valence.append(st.week_valence[-1])

    if day.weekday() == 6:  # Sunday: WHO-5 about the last 2 weeks (here: the week)
        base = 2.6 + fmean(st.week_valence) * 0.9 + (fmean(st.week_energy) - 3) * 0.4
        sleep_item = 2.6 + (fmean(st.week_sleep) - 3) * 0.8
        responses = [
            _likert(base + rng.gauss(0, 0.4), 0, 5),  # cheerful, good spirits
            _likert(base - 0.2 + rng.gauss(0, 0.4), 0, 5),  # calm and relaxed
            _likert(base - 0.1 + (fmean(st.week_energy) - 3) * 0.4 + rng.gauss(0, 0.4), 0, 5),
            _likert(sleep_item + rng.gauss(0, 0.4), 0, 5),  # woke up fresh and rested
            _likert(base + rng.gauss(0, 0.4), 0, 5),  # daily life filled with interesting things
        ]
        yield ev(
            EventType.ASSESSMENT,
            20.5,
            f"WHO-5: {sum(responses) * 4}/100",
            instrument="who5",
            responses=responses,
        )
        st.week_valence, st.week_energy, st.week_sleep = [], [], []

    if (day + timedelta(days=1)).month != day.month:  # last day of month
        stress_level = fmean(st.month_stress)  # 1–5
        responses = []
        for item in range(10):
            raw = (stress_level - 1) + rng.gauss(0, 0.6)  # 0–4 "how often stressed"
            responses.append(_likert(4 - raw if item in PSS_REVERSED else raw, 0, 4))
        yield ev(
            EventType.ASSESSMENT, 21.0, "PSS-10 do mês", instrument="pss10", responses=responses
        )
        ls = _likert(6.8 + fmean(st.month_valence) * 1.2 + rng.gauss(0, 0.5), 0, 10)
        yield ev(
            EventType.ASSESSMENT,
            21.1,
            f"satisfação com a vida {ls}/10",
            instrument="life_satisfaction",
            responses=[ls],
        )
        st.month_stress, st.month_valence = [], []


def to_jsonl(events: list[Event]) -> str:
    events = sorted(events, key=lambda e: (e.occurred_at, e.event_id))
    return "".join(e.model_dump_json(exclude_none=True) + "\n" for e in events)
