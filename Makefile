.PHONY: check test lint lint-fix format

check: test

test:
	uv run pytest tests/

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .
