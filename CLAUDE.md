# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`fhir-api`: a FastAPI service to fetch and upload FHIR data. Currently a boilerplate: only a `/health` endpoint exists.

## Commands

Managed with uv (`pyproject.toml`, `uv.lock`).

- Install: `uv sync`
- Run dev server (auto-reload): `uv run fastapi dev` (finds `app` in `app/main.py`)
- Tests: `uv run pytest`; single test: `uv run pytest tests/test_main.py::test_health`
- Lint/format: `uv run ruff check .` / `uv run ruff format .`
- Docker (dev, hot reload): `docker compose up --build`. `compose.yaml` bind-mounts `./app` and overrides the command to `fastapi dev`; the `Dockerfile` CMD itself is prod (`fastapi run`, no dev deps). Dependency changes need `--build`.

## Layout

- `app/main.py`: the `FastAPI` instance (`app`) and routes.
- `tests/`: pytest tests using `fastapi.testclient.TestClient` against `app.main.app`. `pythonpath = ["."]` in `pyproject.toml` makes `app` importable.
