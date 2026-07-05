.PHONY: dev api seed test verify web-install web-dev web-build

dev:
	uv run recallops-api

api:
	uv run recallops-api

seed:
	uv run recallops-seed

test:
	uv run pytest

verify:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy
	uv run pytest
	npm --prefix web run typecheck
	npm --prefix web run build

web-install:
	npm --prefix web install

web-dev:
	npm --prefix web run dev

web-build:
	npm --prefix web run build

