.PHONY: setup lint format test synth build private dev web-build images deploy destroy

setup:  ## install Python + web deps and git hooks
	uv sync
	cd web && npm install
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .
	cd web && npm run lint && npm run typecheck

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest
	cd web && npm test

synth:  ## regenerate 6 months of fictional events (public demo)
	uv run lifelog synth

build:  ## dbt build (DuckDB) + export web/public/data/lifelog.json
	uv run lifelog build

private:  ## build YOUR data (data/private/events.jsonl) → lifelog.local.json, never committed
	uv run lifelog build --events data/private/events.jsonl

dev:  ## dashboard with hot reload at http://localhost:5173
	cd web && npm run dev

web-build:
	cd web && npm run build

images:  ## optimize raw illustrations in images/ into web/public/img
	uv run --with pillow python scripts/prepare_images.py

deploy:  ## (M7, optional) private cloud — creates billable GCP resources
	cd infra/terraform && terraform init && terraform apply

destroy:
	cd infra/terraform && terraform destroy
