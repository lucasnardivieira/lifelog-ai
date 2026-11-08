# lifelog-ai · Trilhos

Personal life dashboard grounded in psychology. Events (synthetic now, Telegram bot later) → dbt on DuckDB → one JSON → static React + ECharts dashboard.

## Commands
- `make setup` · `make test` (pytest + vitest) · `make lint` · `make format`
- `make synth` (fictional events) · `make build` (dbt + export JSON) · `make private` (real data, gitignored) · `make dev`
- `make images` — optimize raw illustrations in `images/` (gitignored) into `web/public/img/*.webp`

## Layout
- `src/lifelog/events.py` — the event contract (every source emits it)
- `src/lifelog/synthetic.py` — fictional data with causal structure (tests assert the analysis recovers it)
- `src/lifelog/insights.py` — detrended, lag-aware within-person comparisons with bootstrap CIs
- `src/lifelog/export.py` — marts → `web/public/data/lifelog.json`
- `dbt/` — stg → int → marts (+ `seeds/emotion_vocabulary.csv`, kept in sync with `emotions.py` by a test)
- `web/` — React dashboard; tokens in `src/index.css` come from a CVD-validated palette (never color-alone)
- `docs/research/psychology-foundations.md` — why each field exists; read before adding constructs

## Conventions
- Never commit real personal data: `data/private/`, `*.duckdb`, `lifelog.local.json` are gitignored. The public demo is synthetic only.
- Nothing in the UI is diagnostic. Keep CVV 188 / SAMU 192 reachable; flags only suggest talking to someone.
- Insights are "associação, não causa"; new analyses must be within-person and report n + uncertainty.
- Tests never call live APIs. Conventional Commits.
