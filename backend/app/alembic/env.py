"""
backend/app/alembic/env.py
This REPLACES the generic file that `alembic init` just generated.
Uses ALEMBIC_DATABASE_URL (sync psycopg2, port 5432 direct connection)
NOT the asyncpg pooler URL — Alembic's migration runner is synchronous.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.config import settings
from app.db.base import Base

# Import every model module so Base.metadata is fully populated before autogenerate
from app.models import user, learning, marketplace  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.ALEMBIC_DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()