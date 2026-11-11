"""Turn a free-text (or transcribed voice) PT-BR message into contract events with Claude.

Uses structured outputs (`output_config.format` with a hand-written JSON schema) so the reply is
always parseable; everything is re-validated by `lifelog.events.Event` afterwards.
"""

import json
import os
from datetime import datetime
from typing import Any

from lifelog.emotions import QUADRANTS, words_in
from lifelog.extract.schema import SCHEMA, Extraction, parse_extraction

MODEL = os.environ.get("LIFELOG_MODEL", "claude-haiku-5-5")
EFFORT = os.environ.get("LIFELOG_EFFORT", "low")

_vocab = "\n".join(
    f"  - {q} ({QUADRANTS[q]['label']}): {', '.join(words_in(q))}" for q in QUADRANTS
)

SYSTEM_PROMPT = f"""You turn short personal-diary messages (Brazilian Portuguese) into structured events
for a private life-tracking dashboard. Extract only what the person actually said; never invent values.
One message may contain several events, or none (then return an empty list and a short reply).

Output format: for each event give type, day_offset, time ("" if not stated), emotions ([] unless affect)
and `fields`: a list of {{name, value}} pairs ONLY for values the person actually gave (value as text,
e.g. "6.5", "true", "corrida"). Omit everything else.

Only create an event when its main value is known (sleep needs hours; exercise/study/work need
minutes; reading needs pages; expense/income need amount; energy/stress need score). "Fui pro
trabalho" without a duration is not a work event.

Event types and their fields:
- sleep: hours slept (hours); optional bedtime/wake_time "HH:MM", sol_minutes (time to fall asleep),
  awakenings, waso_minutes, score = sleep quality 1–5, rested 1–5. A night is logged on the morning after.
- exercise: minutes, category = activity in Portuguese (corrida, academia, bike, caminhada, yoga…);
  optional pleasure and mastery 0–10 if they say how it felt.
- energy: score 1–5.  meal: category one of "saudável" | "ok" | "besteira", label = what they ate.
- affect: how they feel. valence −2…+2 (unpleasant…pleasant, never 0) and arousal −2…+2 (low…high
  energy, never 0). emotions = 1–3 words ONLY from this vocabulary (pick the closest; if none fits, leave []):
{_vocab}
- stress: score 1–5.
- needs: autonomy, competence, relatedness 1–5 (Self-Determination Theory) — only if they rate them.
- gratitude: note = what they are grateful for.  journal: note = their reflection, lightly cleaned.
- study: minutes, category = topic (e.g. dbt, Spark, SQL); optional pleasure/mastery 0–10.
- reading: pages, label = book title.  work: minutes, category "rotina" or "prazo" (deadline).
- habit: habit = habit name as the person names it, done true/false.
- expense: amount in BRL, category one of alimentação, mercado, transporte, lazer, saúde, compras,
  moradia, contas, assinaturas; label = merchant/place.  income: amount, category (salário, freela…).
- social: category = who (namorado, amigos, família, trabalho, or a short description),
  label = activity; optional pleasure 0–10.

Dates: day_offset 0 = today, -1 = yesterday ("ontem"), etc. Use time "HH:MM" only if stated or clearly
implied ("cheguei em casa às 17h30 exausto" → that feeling at 17:30).
Durations: "1h30" = 90 minutes; "meia hora" = 30.

Messages are often long voice transcriptions of a whole day. Read for meaning, not keywords:
- Feelings described in words map to vocabulary emotions, one affect event per distinct moment:
  "me senti reconhecido" → orgulhoso; "exausto" → esgotado; "aliviado" → aliviado; "reuniões chatas" →
  entediado/frustrado; "feliz com…" → alegre. Valence and arousal must agree with the words.
- Sleep: "dormi perto das 11, acordei às 7" → bedtime "23:00", wake_time "07:00", hours 8 (minus time to
  fall asleep / awake at night only if stated). Lying in bed AFTER waking is not sleep-onset latency.
- Work: only with an explicit duration or working interval ("trabalhei das 9 às 18" → 540 minutes). Leaving
  for work at 8 and getting home at 17:30 includes commuting: do not turn that into minutes.
- Meals: "almocei uma marmita" → meal, label "marmita", category "saudável" for homemade/light food,
  "besteira" for fast food/sweets, otherwise "ok".
- Stress: map clear statements ("muito estressado" → 4, "estressadíssimo" → 5, "tranquilo, zero estresse"
  → 1); otherwise only if rated.
- Needs (autonomy/competence/relatedness): ONLY when the person gives a rating; never infer them.
- Habits: if the person says they did / did not do one of their habits (list below), log habit with that
  exact name and done true/false. Absence of activity is not an event ("não fui na academia" → nothing,
  unless academia is one of their habits).
- Timed activities without a type of their own (meditação, yoga, alongamento, pilates) → exercise with
  that category and minutes (and also a habit event if it is one of their habits).
- Ignore filler, small talk and things with no field (naps, TV) — mention them briefly in the reply if useful.

risk: "crisis" if the message suggests suicidal thoughts, self-harm or being in danger; "concern" for
strong hopelessness or overwhelming distress without danger; otherwise "none".

reply: one short, warm sentence in Portuguese confirming what you understood (no advice, no diagnosis,
no emojis spam). If nothing could be extracted, ask briefly what they want to log."""


def _user_message(text: str, now: datetime, habits: list[str] | None = None) -> str:
    weekday = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"][now.weekday()]
    habit_line = (
        f"Hábitos da pessoa: {', '.join(habits)}.\n" if habits else "Hábitos da pessoa: nenhum.\n"
    )
    return f"Agora: {weekday}, {now:%Y-%m-%d %H:%M} (America/Sao_Paulo).\n{habit_line}\nMensagem:\n{text}"


def build_request(text: str, now: datetime, habits: list[str] | None = None) -> dict[str, Any]:
    return {
        "model": MODEL,
        # Haiku 5.5 thinks by default and thinking counts toward max_tokens
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "output_config": {"effort": EFFORT, "format": {"type": "json_schema", "schema": SCHEMA}},
        "messages": [{"role": "user", "content": _user_message(text, now, habits)}],
    }


def extract(
    text: str, now: datetime, client: Any = None, habits: list[str] | None = None
) -> Extraction:
    """Call Claude and parse the structured reply. Raises on API errors (the caller decides)."""
    if client is None:
        import anthropic

        client = anthropic.Anthropic()
    response = client.messages.create(**build_request(text, now, habits))
    if response.stop_reason == "refusal":
        return Extraction(events=[], risk="concern", reply="")
    body = next((b.text for b in response.content if b.type == "text"), "")
    return parse_extraction(json.loads(body))
