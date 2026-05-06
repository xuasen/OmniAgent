FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir .

FROM base AS development

COPY . .
RUN pip install -e ".[dev]"

CMD ["uvicorn", "omniagent.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production

COPY src/ src/
COPY config/ config/
COPY schemas/ schemas/
COPY migrations/ migrations/
COPY alembic.ini .

RUN pip install --no-cache-dir .

CMD ["uvicorn", "omniagent.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
