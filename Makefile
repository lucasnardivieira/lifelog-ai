.PHONY: setup lint format test run deploy destroy

setup:  ## Install deps and git hooks
	uv sync
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest

run:  ## Run the bot locally in polling mode (M1)
	@echo "Not implemented yet — see Roadmap in README.md (M1)"

deploy:  ## terraform apply (M3) — creates billable GCP resources
	cd infra/terraform && terraform init && terraform apply

destroy:  ## Tear down every GCP resource
	cd infra/terraform && terraform destroy
