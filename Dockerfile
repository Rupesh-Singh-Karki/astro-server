# Builder stage
FROM python:3.11-slim AS builder

WORKDIR /src

# Install uv (modern pip replacement)
RUN pip install --upgrade pip
RUN pip install --no-cache-dir uv

# Copy pyproject.toml file
COPY pyproject.toml .

# Create venv and install dependencies
RUN uv venv
RUN . .venv/bin/activate && uv sync --dev

# Final stage
FROM python:3.11-slim

WORKDIR /src

# Copy venv from builder
COPY --from=builder /src/.venv /src/.venv

# Copy application files
COPY . .

# Activate virtual environment and set PYTHONPATH
ENV PATH="/src/.venv/bin:$PATH"
ENV PYTHONPATH="/src"
# Default port, but Render will override with PORT env var
ENV PORT=10000

# Use ENTRYPOINT to run gunicorn with multi worker for production
ENTRYPOINT ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:$PORT --workers 1"]