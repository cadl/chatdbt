.PHONY: all lint

all: lint

lint:
		mypy .
		black . --check
		ruff .
