.PHONY: all lint

all: lint

lint:
		poetry run mypy --non-interactive --install-types .
		poetry run black . --check
		poetry run ruff .
