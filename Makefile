.PHONY: check test lint lint-fix format

default: check

check:
	uv run pytest tests/

lint:
	uv run ruff check .
	uv run ruff format --check .

lint-fix:
	uv run ruff check --fix .
	uv run ruff format .
