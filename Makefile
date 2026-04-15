.PHONY: serve build progress sync
sync:
	uv sync

serve:
	uv run mkdocs serve

build:
	uv run mkdocs build

progress:
	uv run python hooks/progress.py
