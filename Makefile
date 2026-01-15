default: check

check:
	uv run pytest -v --tb=short tests/

lint:
	uv run ruff check .
	uv run ruff format --check .

lint-fix:
	uv run ruff check --fix .
	uv run ruff format .

.PHONY: default check lint lint-fix
