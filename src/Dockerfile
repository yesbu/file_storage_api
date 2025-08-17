FROM python:3.12.2-slim as builder

ENV POETRY_VERSION=2.1.4

WORKDIR /app

RUN pip install --upgrade pip \
    && pip install "poetry==$POETRY_VERSION"

RUN python -m venv .venv

COPY ../README.md README.md
COPY ../poetry.lock poetry.lock
COPY ../pyproject.toml pyproject.toml
COPY src/ ./src

RUN poetry install --only main  # Без dev-зависимостей, по-современному!
RUN poetry build
RUN /app/.venv/bin/pip install /app/dist/*.tar.gz && /app/.venv/bin/pip check

FROM python:3.12.2-slim as api

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

RUN apt-get update && \
    rm -rf /var/lib/apt/lists/*

COPY ../migrations ./migrations
COPY alembic.ini alembic.ini
COPY ../entrypoint.sh entrypoint.sh

RUN chmod +x /app/entrypoint.sh

RUN ln -snf /app/.venv/bin/alembic /usr/local/bin/
RUN ln -snf /app/.venv/bin/run-api /usr/local/bin/

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["fastapi", "run", "app/.venv/site-packages/file_storage_api/main.py", "--port", "80"]