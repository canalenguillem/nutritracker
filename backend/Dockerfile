# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

FROM base AS development

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts

RUN pip install ".[dev]" && \
    chmod +x /app/scripts/start.sh && \
    chown -R app:app /app

COPY --chown=app:app tests ./tests

USER app

EXPOSE 8000

CMD ["/app/scripts/start.sh"]

FROM base AS production

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts

RUN pip install . && chmod +x /app/scripts/start.sh

USER app

EXPOSE 8000

CMD ["/app/scripts/start.sh"]
