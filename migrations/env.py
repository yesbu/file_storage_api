from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from file_storage_api.models import Base
from file_storage_api.database import Base as DBBase
import os


def run_migrations_online():
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,  # Используем метаданные из моделей
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()