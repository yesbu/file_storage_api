# Builder stage
FROM python:3.12-alpine AS builder

RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    postgresql-dev \
    python3-dev \
    curl

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Установка зависимостей без установки текущего проекта
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root && \
    poetry cache clear pypi --all --no-interaction

# Runtime stage
FROM python:3.12-alpine

RUN apk add --no-cache libpq curl

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

ENV LANG=C.UTF-8

ENV PYTHONPATH=/app:/src \
    PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]