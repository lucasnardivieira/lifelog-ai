# 3. Telegram bot runs locally; buttons first, Claude only for free text

Date: 2026-11-09

## Status
Accepted

## Context
The dashboard needs real data with very little friction. The data includes mental-health
self-reports, so privacy matters more than always-on availability.

## Decision
- **Local long-polling bot** (python-telegram-bot) on the owner's PC. Only `TELEGRAM_ALLOWED_CHAT_ID`
  is served. Events are appended to `data/private/events.jsonl` (gitignored). Cloud hosting is
  deferred to M7.
- **Validated check-ins use buttons, not AI:** the sleep diary, the affect grid with emotion words,
  the end-of-day needs, WHO-5 and PSS-10. They are deterministic, free, and never leave the machine.
- **Free text → Claude Haiku 5.5** with structured outputs (hand-written JSON schema). Output is
  re-validated by the event contract and shown as a **preview that the user confirms** before saving.
- **Voice → local faster-whisper.** Audio is deleted right after transcription.
- **Append-only:** `/desfazer` writes `retraction` events, and dbt drops retracted events in staging.
- **Safety first:** a keyword safety net plus Claude's `risk` field. A crisis reply (CVV 188 / SAMU 192)
  is sent before anything else, even if the API fails.
- **Quality:** a golden set of PT-BR messages (`make eval`) measures extraction. Tests use fake clients.

## Consequences
- \+ Zero infrastructure; private by default. Typed messages cost cents per month.
- − Reminders only fire while the PC is on. Messages sent meanwhile are processed when the bot starts.
- − Free-text content is sent to the Anthropic API (not used for training by default). Buttons and
  voice audio are not.
