# 2. Dashboard first, grounded in psychology, local-first data

Date: 2026-11-08

## Status
Accepted. Changes the milestone order in the README and supersedes the "Looker Studio" idea.

## Context
The goal shifted from "a bot that logs events" to "a beautiful, organized, complex interface to see the
tracks of my life". Self-tracking of mood and mental health is sensitive. It needs validated constructs, honest
statistics and safety rails, and the data is personal while the repository is public.

## Decision
- **Interface first** on realistic synthetic data. The Telegram capture bot comes later (M6) and emits the
  same event contract, so the dashboard won't change when real data arrives.
- **Psychology grounding** (docs/research/psychology-foundations.md): circumplex affect and emotion words,
  Consensus Sleep Diary, SDT needs, WHO-5, PSS-10 and life satisfaction, behavioral-activation ratings, habit
  strength curves with if-then plans. Analysis is within-person, detrended, lag-aware, and reports CIs.
- **Local-first:** DuckDB + dbt run on the laptop. The public GitHub Pages site only ever ships synthetic
  data. Real data lives in `data/private/` and `lifelog.local.json`, both gitignored. GCP (Terraform) is
  optional for a future private online view (M7).
- **Static dashboard:** React + ECharts reads one exported JSON file. There is no backend.
- **Safety:** nothing is diagnostic. CVV 188 / SAMU 192 are always one click away and highlighted after a low WHO-5.

## Consequences
- \+ Zero cost, nothing to operate, and the public demo is shareable without privacy risk.
- \+ dbt marts are the single source for every number on screen.
- − No phone access to real data until M7. The insights are computed over the full history, not per period.
