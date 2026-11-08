# lifelog-ai

Telegram life-log bot. Claude extracts typed events from free-form messages → GCS raw JSONL → BigQuery → dbt → weekly insights.

## Commands
- `make setup` · `make lint` · `make format` · `make test` · `make run` (M1)
- `make deploy` / `make destroy` — Terraform in `infra/terraform/` (ask Lucas before applying: billable)

## Layout
- `src/lifelog/bot/` — webhook/polling app, handlers, chat-id auth
- `src/lifelog/extract/` — Pydantic event models, Claude extraction, prompts
- `src/lifelog/storage/` — raw writers (local DuckDB, GCS JSONL)
- `src/lifelog/report/` — weekly job: dbt build + insights + send
- `dbt/` — stg → int → marts (lowercase snake_case)
- `evals/` — golden set + accuracy scorer
- `docs/adr/` — architecture decisions

## Conventions
- Never commit real personal data or secrets: synthetic data only; `.env` is gitignored.
- Tests must not call live APIs — use recorded fixtures.
- Raw layer is immutable/append-only; corrections are new events, not updates.
- Conventional Commits.
