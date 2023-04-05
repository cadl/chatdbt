.PHONY: all lint

all: lint

lint:
		poetry run mypy .
		poetry run black . --check
		poetry run ruff .
