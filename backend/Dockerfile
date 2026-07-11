# Stage 1: Build virtual environment
FROM python:3.12-slim AS builder
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Stage 2: Runtime image
FROM python:3.12-slim
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
COPY --from=builder /opt/venv /opt/venv
COPY backend/src/aether/ /app/aether/
COPY database/schema/ /app/database/schema/

RUN groupadd -r appgroup && useradd -r -g appgroup -u 1001 appuser && chown -R appuser:appgroup /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "aether.interfaces.http.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
