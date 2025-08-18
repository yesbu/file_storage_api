#!/bin/bash
set -e

# Ждем готовности PostgreSQL
while ! nc -z db 5432; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

# Применяем миграции (только для api сервиса)
if [ "$1" = "uvicorn" ]; then
    alembic upgrade head
fi

exec "$@"