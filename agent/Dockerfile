FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY main.py ./
COPY src ./src

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# ---- development: used by docker-compose for local development (hot reload) ----
FROM base AS development

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- production: minimal runtime image (default target — used for deployment) ----
FROM base AS production

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
