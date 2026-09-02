FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8080

# ---- dev: used by docker-compose for local dev ----
FROM base AS dev

CMD ["python", "-m", "src.server"]

# ---- prod: minimal runtime image (default target — used for deployment) ----
FROM base AS prod

CMD ["python", "-m", "src.server"]
