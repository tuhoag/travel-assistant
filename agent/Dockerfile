FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY main.py ./
COPY src ./src
COPY prompts ./prompts

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV HOSTNAME=0.0.0.0
EXPOSE 8000

# ---- dev: used by docker-compose for local dev (hot reload) ----
FROM base AS dev

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- prod: minimal runtime image (default target — used for deployment) ----
FROM base AS prod

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
