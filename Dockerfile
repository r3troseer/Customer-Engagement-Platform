# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first (layer-cached unless deps change)
COPY pyproject.toml uv.lock ./

# Install production dependencies into a local virtualenv
RUN uv sync --frozen --no-dev

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy the virtualenv built in the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY . .

# Ensure the venv is on PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create uploads directory (used by local file storage)
RUN mkdir -p /app/uploads

# Railway injects PORT; fall back to 8000
EXPOSE 8000

# Run Alembic migrations then start Uvicorn.
# In Railway: set DATABASE_URL and JWT_SECRET_KEY as env vars in the dashboard.
CMD alembic upgrade head && \
    uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
