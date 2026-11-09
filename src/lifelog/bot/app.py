"""Telegram bot — runs on your own machine (long polling), talks only to your chat id.

    uv run --env-file .env lifelog bot

Everything is stored append-only in data/private/events.jsonl (gitignored). Buttons never leave
the machine; free text goes to Claude for extraction; voice is transcribed locally (faster-whisper).
"""

import asyncio
import html
import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime
from datetime import time as dtime
from pathlib import Path
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from lifelog import safety, voice
from lifelog.bot.flows import (
    LIFE_SATISFACTION,
    PSS10,
    STATIC_FLOWS,
    Flow,
    close_flow,
    is_last_day_of_month,
)
from lifelog.bot.habits import HabitStore, parse_new_habit
from lifelog.events import Event, EventType
from lifelog.extract.claude import extract
from lifelog.extract.schema import TZ, to_events
from lifelog.storage.jsonl import EventStore

log = logging.getLogger("lifelog.bot")

DATA_DIR = Path(os.environ.get("LIFELOG_DATA_DIR", "data/private"))
EVENTS = DATA_DIR / "events.jsonl"
HABITS = DATA_DIR / "habits.json"

ICON = {
    "sleep": "😴", "exercise": "🏃", "energy": "⚡", "meal": "🍽️", "affect": "◐", "stress": "🌡️",
    "needs": "△", "gratitude": "🙏", "journal": "✎", "study": "📚", "reading": "📖", "work": "💼",
    "habit": "↗", "expense": "💸", "income": "💰", "social": "👥", "assessment": "📋",
}  # fmt: skip

HELP = """<b>Trilhos — seu diário</b>
Escreva ou mande um 🎤 áudio do jeito que quiser:
• <i>dormi 6h30, acordei cansado</i>
• <i>estudei dbt 1h e treinei 40 min de corrida</i>
• <i>gastei 42 no almoço</i> · <i>jantar com meu namorado, foi ótimo</i>
• <i>me sinto ansioso e sobrecarregado</i>
Eu mostro o que entendi e você confirma.

<b>Check-ins com botões</b>
/sono — diário de sono · /checkin — como você está agora
/fechar — estresse, necessidades e hábitos do dia
/who5 · /pss10 · /satisfacao — questionários

<b>Hábitos</b>
<i>novo hábito: meditar 10 min — se eu terminar o café, então medito</i>
/habitos — lista · /parar_habito nome

<b>Outros</b>
/desfazer — desfaz o último registro · /painel — atualiza o dashboard · /cancelar

💬 Precisa conversar? CVV 188 (grátis, 24h) · SAMU 192"""


def _now() -> datetime:
    return datetime.now(TZ).replace(second=0, microsecond=0)


def _allowed_chat() -> int | None:
    raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID", "").strip()
    return int(raw) if raw.lstrip("-").isdigit() else None


def brl(amount: float) -> str:
    """R$ 1.234,56"""
    return "R$ " + f"{amount:,.2f}".translate(str.maketrans(",.", ".,"))


def describe(e: Event) -> str:
    """One-line PT-BR summary of an event for previews."""
    i = ICON.get(e.type.value, "•")
    t = e.type.value
    if t == "sleep":
        extra = f" ({e.bedtime}→{e.wake_time})" if e.bedtime and e.wake_time else ""
        return f"{i} sono {e.hours:g}h{extra}" + (f", qualidade {e.score}/5" if e.score else "")
    if t == "affect":
        words = ", ".join(e.emotions or []) or "sem palavra"
        return f"{i} afeto {e.valence:+d}/{e.arousal:+d}: {words}"
    if t in ("exercise", "study", "work"):
        return f"{i} {e.category or t} {e.minutes} min"
    if t in ("energy", "stress"):
        return f"{i} {'energia' if t == 'energy' else 'estresse'} {e.score}/5"
    if t == "needs":
        return f"{i} autonomia {e.autonomy} · competência {e.competence} · vínculo {e.relatedness}"
    if t in ("expense", "income"):
        where = f" · {e.label}" if e.label else ""
        return f"{i} {brl(e.amount or 0)} {e.category or ''}{where}"
    if t == "reading":
        return f"{i} {e.pages} páginas de {e.label or 'leitura'}"
    if t == "social":
        return f"{i} {e.label or 'encontro'} com {e.category}"
    if t == "habit":
        return f"{i} {'✓' if e.done else '✗'} {e.habit}"
    if t == "meal":
        return f"{i} refeição {e.category}" + (f" ({e.label})" if e.label else "")
    if t in ("gratitude", "journal"):
        return f"{i} {e.note}"
    return f"{i} {t}"


class LifelogBot:
    def __init__(self) -> None:
        self.store = EventStore(EVENTS)
        self.habits = HabitStore(HABITS)
        self.allowed = _allowed_chat()

    # ------------------------------------------------------------------ guard

    async def _authorized(self, update: Update) -> bool:
        chat = update.effective_chat
        if chat is None:
            return False
        if self.allowed is None or chat.id != self.allowed:
            if update.message and update.message.text and update.message.text.startswith("/start"):
                await update.message.reply_text(
                    f"Olá! Seu chat id é <code>{chat.id}</code>.\n"
                    "Coloque em TELEGRAM_ALLOWED_CHAT_ID no .env e reinicie o bot.",
                    parse_mode=ParseMode.HTML,
                )
            log.warning("ignored message from chat %s", chat.id)
            return False
        return True

    # ------------------------------------------------------------------ flows

    def _keyboard(self, flow: Flow, state: dict[str, Any]) -> InlineKeyboardMarkup:
        step = flow.steps[state["step"]]
        token = state["token"]
        choices = step.choices(state["values"])
        rows: list[list[InlineKeyboardButton]] = []
        row: list[InlineKeyboardButton] = []
        for idx, (label, _) in enumerate(choices):
            selected = idx in state["selected"]
            text = f"✓ {label}" if (step.multi and selected) else label
            row.append(InlineKeyboardButton(text, callback_data=f"f|{token}|{idx}"))
            if len(row) == step.columns:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        controls = [InlineKeyboardButton("✖ cancelar", callback_data=f"x|{token}")]
        if step.multi:
            controls.insert(0, InlineKeyboardButton("pronto ➜", callback_data=f"d|{token}"))
        rows.append(controls)
        return InlineKeyboardMarkup(rows)

    def _text(self, flow: Flow, state: dict[str, Any]) -> str:
        step = flow.steps[state["step"]]
        return f"<b>{flow.title}</b> · {state['step'] + 1}/{len(flow.steps)}\n\n{step.text(state['values'])}"

    async def start_flow(
        self, chat_id: int, flow: Flow, context: ContextTypes.DEFAULT_TYPE, intro: str = ""
    ) -> None:
        state = {"token": uuid.uuid4().hex[:8], "step": 0, "values": {}, "selected": []}
        context.application.chat_data[chat_id]["flow"] = (flow, state)
        await context.bot.send_message(
            chat_id,
            (intro + "\n\n" if intro else "") + self._text(flow, state),
            parse_mode=ParseMode.HTML,
            reply_markup=self._keyboard(flow, state),
        )

    async def on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not await self._authorized(update) or query is None or query.data is None:
            return
        await query.answer()
        kind, token, *rest = query.data.split("|")
        chat_data = context.chat_data

        if kind in ("save", "drop"):
            await self._resolve_preview(query, chat_data, token, save=kind == "save")
            return

        current = chat_data.get("flow")
        if not current or current[1]["token"] != token:
            await query.edit_message_text("Esse check-in expirou. Comece de novo pelo menu /ajuda.")
            return
        flow, state = current
        step = flow.steps[state["step"]]
        choices = step.choices(state["values"])

        if kind == "x":
            chat_data.pop("flow", None)
            await query.edit_message_text(f"{flow.title}: cancelado.")
            return
        if kind == "f":
            idx = int(rest[0])
            if step.multi:
                sel = state["selected"]
                if idx in sel:
                    sel.remove(idx)
                elif len(sel) < step.max_selected:
                    sel.append(idx)
                await query.edit_message_reply_markup(self._keyboard(flow, state))
                return
            state["values"][step.key] = choices[idx][1]
        if kind == "d":
            state["values"][step.key] = [choices[i][1] for i in state["selected"]]

        state["step"] += 1
        state["selected"] = []
        if state["step"] < len(flow.steps):
            await query.edit_message_text(
                self._text(flow, state),
                parse_mode=ParseMode.HTML,
                reply_markup=self._keyboard(flow, state),
            )
            return

        chat_data.pop("flow", None)
        events = flow.finalize(state["values"], _now())
        chat_data["last_batch"] = self.store.append(events)
        summary = "\n".join(html.escape(describe(e)) for e in events)
        await query.edit_message_text(
            f"{flow.done_message}\n\n{summary}", parse_mode=ParseMode.HTML
        )
        if flow is PSS10:  # end-of-month pair
            await self.start_flow(update.effective_chat.id, LIFE_SATISFACTION, context)

    # ------------------------------------------------------------------ free text & voice

    async def _handle_text(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, via_voice: bool
    ) -> None:
        msg = update.effective_message
        habit = parse_new_habit(text)
        if habit:
            self.habits.upsert(habit)
            plan = (
                f"\nPlano: <i>{html.escape(habit['if_then'])}</i>"
                if habit["if_then"]
                else (
                    "\nDica: inclua um plano “se …, então …”. Isso aumenta bastante a chance de cumprir."
                )
            )
            await msg.reply_text(
                f"↗ Hábito <b>{html.escape(habit['name'])}</b> criado.{plan}\nVou perguntar dele no /fechar.",
                parse_mode=ParseMode.HTML,
            )
            return

        support_sent = False
        if safety.keyword_risk(text):
            await msg.reply_text(
                safety.SUPPORT_MESSAGE, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )
            support_sent = True

        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        now = _now()
        try:
            extraction = await asyncio.to_thread(extract, text, now)
        except Exception:  # API down, no credits, invalid key…
            log.exception("extraction failed")
            await msg.reply_text(
                "Não consegui interpretar agora 😕 Tente de novo daqui a pouco ou use os botões: /checkin, /sono, /fechar."
            )
            return

        if extraction.risk in ("concern", "crisis") and not support_sent:
            await msg.reply_text(
                safety.SUPPORT_MESSAGE, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )

        raw = f"🎤 {text}" if via_voice else text
        events, problems = to_events(extraction, now, raw)
        if not events:
            await msg.reply_text(
                extraction.reply
                or "Não encontrei nada para registrar. Pode me dizer de outro jeito?"
            )
            return

        pid = uuid.uuid4().hex[:8]
        context.chat_data.setdefault("pending", {})[pid] = events
        lines = "\n".join(html.escape(describe(e)) for e in events)
        heard = f"🎤 <i>{html.escape(text)}</i>\n\n" if via_voice else ""
        warn = f"\n\n⚠️ Não entendi: {html.escape('; '.join(problems))}" if problems else ""
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ salvar", callback_data=f"save|{pid}"),
                    InlineKeyboardButton("✖ descartar", callback_data=f"drop|{pid}"),
                ]
            ]
        )
        await msg.reply_text(
            f"{heard}{html.escape(extraction.reply)}\n\n{lines}{warn}",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    async def _resolve_preview(self, query: Any, chat_data: dict, pid: str, save: bool) -> None:
        events = chat_data.get("pending", {}).pop(pid, None)
        if events is None:
            await query.edit_message_reply_markup(None)
            return
        if save:
            chat_data["last_batch"] = self.store.append(events)
            await query.edit_message_text(
                query.message.text_html + "\n\n✅ salvo", parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text(
                query.message.text_html + "\n\n✖ descartado", parse_mode=ParseMode.HTML
            )

    async def on_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await self._authorized(update) and update.message and update.message.text:
            await self._handle_text(update, context, update.message.text, via_voice=False)

    async def on_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._authorized(update) or not update.message:
            return
        if not voice.available():
            await update.message.reply_text(
                "Para áudios, instale o Whisper local: uv sync --extra voice"
            )
            return
        media = update.message.voice or update.message.audio
        tmp = DATA_DIR / "tmp" / f"{uuid.uuid4().hex}.ogg"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        try:
            file = await context.bot.get_file(media.file_id)
            await file.download_to_drive(tmp)
            text = await asyncio.to_thread(voice.transcribe, tmp)
        finally:
            tmp.unlink(missing_ok=True)  # audio is never kept
        if not text:
            await update.message.reply_text("Não consegui entender o áudio. Pode repetir?")
            return
        await self._handle_text(update, context, text, via_voice=True)

    # ------------------------------------------------------------------ commands

    def _flow_command(self, key: str):
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if await self._authorized(update):
                flow = close_flow(self.habits.load()) if key == "close" else STATIC_FLOWS[key]
                await self.start_flow(update.effective_chat.id, flow, context)

        return handler

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await self._authorized(update):
            await update.message.reply_text(
                HELP, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )

    async def cmd_undo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._authorized(update):
            return
        batch = context.chat_data.pop("last_batch", None)
        if not batch:
            await update.message.reply_text("Não há registro recente para desfazer.")
            return
        self.store.retract(batch, _now())
        await update.message.reply_text(
            f"↩️ Desfeito ({len(batch)} registro(s)). Nada é apagado: fica anotado como correção."
        )

    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await self._authorized(update):
            context.chat_data.pop("flow", None)
            await update.message.reply_text("Ok, cancelado.")

    async def cmd_habits(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._authorized(update):
            return
        habits = [h for h in self.habits.load() if h.get("active", True)]
        if not habits:
            await update.message.reply_text(
                "Nenhum hábito ainda. Ex.: novo hábito: meditar 10 min — se eu terminar o café, então medito"
            )
            return
        lines = [
            f"↗ <b>{html.escape(h['name'])}</b>"
            + (f"\n   <i>{html.escape(h['if_then'])}</i>" if h.get("if_then") else "")
            for h in habits
        ]
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

    async def cmd_stop_habit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._authorized(update):
            return
        name = " ".join(context.args or []).strip()
        ok = bool(name) and self.habits.deactivate(name)
        await update.message.reply_text(
            f"Hábito “{name}” pausado." if ok else "Use: /parar_habito nome do hábito"
        )

    async def cmd_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._authorized(update):
            return
        await update.message.reply_text("Atualizando o painel…")
        cmd = [sys.executable, "-m", "lifelog.cli", "build", "--events", str(EVENTS.resolve())]
        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        if result.returncode == 0:
            await update.message.reply_text(
                "📊 Painel atualizado. No PC: <code>make dev</code> → http://localhost:5173",
                parse_mode=ParseMode.HTML,
            )
        else:
            log.error("build failed: %s", result.stderr[-2000:])
            await update.message.reply_text("Não consegui atualizar o painel (veja o log do bot).")

    # ------------------------------------------------------------------ reminders

    async def remind_sleep(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        if self.store.count_today(EventType.SLEEP, _now().date().isoformat()) == 0:
            await self.start_flow(
                context.job.chat_id, STATIC_FLOWS["sleep"], context, "☀️ Bom dia! Como foi a noite?"
            )

    async def remind_affect(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.start_flow(
            context.job.chat_id, STATIC_FLOWS["affect"], context, "🌤️ Pausa rápida:"
        )

    async def remind_who5(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.start_flow(
            context.job.chat_id,
            STATIC_FLOWS["who5"],
            context,
            "📋 Domingo: 5 perguntas sobre as últimas duas semanas (1 min).",
        )

    async def remind_month(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        if is_last_day_of_month(_now()):
            await self.start_flow(
                context.job.chat_id,
                PSS10,
                context,
                "📋 Fim do mês: 10 perguntas rápidas sobre estresse.",
            )


def _clock(env: str, default: str) -> dtime:
    hh, mm = (int(x) for x in os.environ.get(env, default).split(":"))
    return dtime(hh, mm, tzinfo=TZ)


def build_application() -> Application:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        sys.exit("TELEGRAM_BOT_TOKEN is not set (see .env.example)")
    bot = LifelogBot()
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler(["start", "ajuda", "help"], bot.cmd_help))
    for command, key in (("sono", "sleep"), ("checkin", "affect"), ("fechar", "close"), ("who5", "who5"),
                         ("pss10", "pss10"), ("satisfacao", "life")):  # fmt: skip
        app.add_handler(CommandHandler(command, bot._flow_command(key)))
    app.add_handler(CommandHandler("desfazer", bot.cmd_undo))
    app.add_handler(CommandHandler("cancelar", bot.cmd_cancel))
    app.add_handler(CommandHandler("habitos", bot.cmd_habits))
    app.add_handler(CommandHandler("parar_habito", bot.cmd_stop_habit))
    app.add_handler(CommandHandler("painel", bot.cmd_dashboard))
    app.add_handler(CallbackQueryHandler(bot.on_callback))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, bot.on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.on_text))

    if bot.allowed is not None and app.job_queue is not None:
        jq, chat = app.job_queue, bot.allowed
        jq.run_daily(
            bot.remind_sleep, _clock("LIFELOG_MORNING", "08:00"), chat_id=chat, name="sleep"
        )
        jq.run_daily(
            bot.remind_affect, _clock("LIFELOG_AFTERNOON", "15:00"), chat_id=chat, name="affect"
        )
        jq.run_daily(
            bot.remind_who5, _clock("LIFELOG_WHO5", "20:00"), days=(0,), chat_id=chat, name="who5"
        )
        jq.run_daily(
            bot.remind_month, _clock("LIFELOG_MONTHLY", "21:00"), chat_id=chat, name="monthly"
        )
    return app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    app = build_application()
    log.info("bot started — events → %s", EVENTS)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
