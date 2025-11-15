# Development Commands

This file documents commonly used commands for development, testing, linting, and running the application locally.

## Setup: UV (optional)
`uv` is a lightweight tool used by CI to manage dependencies and create reproducible environments. It provides `uvx` as a way to run commands inside the managed environment.

Install `uv` and add dev dependencies:
```bash
python -m pip install --upgrade pip
pip install uv
uv add --group dev black mypy ruff
```

Sync the `uv` environment (ensures the pinned environment and requirements are installed):
```bash
uv sync
```

You can run commands inside the `uv` environment with `uvx`.

## CLI Commands

The `fastappear` command provides CLI functionality:

- Initialize a new FastAppear project in the current directory:
```bash
fastappear init <name>
```

This will create all project files and replace `astro-server` with the provided name.

---

## Running the app

1. Development mode using uvicorn (recommended for local development):
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

2. Production-style using Gunicorn with the Uvicorn worker:
```bash
gunicorn -k uvicorn.workers.UvicornWorker -c gunicorn_conf.py src.main:app
```

Note: If you use `uv`, you can run the above inside `uv` via `uv run`.

---

## Running tests

Run tests with coverage for `src`:
```bash
pytest test/ --cov=src --cov-report=term-missing
```

If your CI expects `tests/`, update accordingly. The repository uses `test/` by default; adjust the path if your tests live elsewhere.

---

## Development tools

Linting:
```bash
uvx ruff check
```

Formatting:
```bash
uvx black .
```

Type checking:
```bash
uvx mypy .
```

If you're not using `uv`/`uvx`, run these commands directly (make sure the tools are installed).

---

## Scaffolding / helper scripts

Create a new module under `src` (scaffolded structure):
```bash
uv run scripts/generate_module.py <name>
```

Create a new test module under `test` (scaffolded structure):
```bash
uv run scripts/generate_test_module.py <name>
```

These scripts generate the directory layout and empty modules for you to customize.

---

If you want me to add `make` targets or `docker-compose` command wrappers for the above commands (for easier, consistent local usage) I can add them next.

