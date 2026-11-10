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

Dates: day_offset 0 = today, -1 = yesterday ("ontem"), etc. Use time "HH:MM" only if stated.
Durations: "1h30" = 90 minutes; "meia hora" = 30.

risk: "crisis" if the message suggests suicidal thoughts, self-harm or being in danger; "concern" for
strong hopelessness or overwhelming distress without danger; otherwise "none".

reply: one short, warm sentence in Portuguese confirming what you understood (no advice, no diagnosis,
no emojis spam). If nothing could be extracted, ask briefly what they want to log."""


def _user_message(text: str, now: datetime) -> str:
    weekday = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"][now.weekday()]
    return f"Agora: {weekday}, {now:%Y-%m-%d %H:%M} (America/Sao_Paulo).\n\nMensagem:\n{text}"


def build_request(text: str, now: datetime) -> dict[str, Any]:
    return {
        "model": MODEL,
        # Haiku 5.5 thinks by default and thinking counts toward max_tokens
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "output_config": {"effort": EFFORT, "format": {"type": "json_schema", "schema": SCHEMA}},
        "messages": [{"role": "user", "content": _user_message(text, now)}],
    }


def extract(text: str, now: datetime, client: Any = None) -> Extraction:
    """Call Claude and parse the structured reply. Raises on API errors (the caller decides)."""
    if client is None:
        import anthropic

        client = anthropic.Anthropic()
    response = client.messages.create(**build_request(text, now))
    if response.stop_reason == "refusal":
        return Extraction(events=[], risk="concern", reply="")
    body = next((b.text for b in response.content if b.type == "text"), "")
    return parse_extraction(json.loads(body))
