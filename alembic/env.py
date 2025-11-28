from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Добавляем корень проекта в PYTHONPATH, чтобы импортировать модули
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Импортируем db и модели
from extensions import db
from models import User, Category, SubCategory

# Импортируем URL из connections.py
try:
    from services import DATABASE_URL_FOR_FLASK
except ImportError as e:
    raise ImportError(
        "Не удалось импортировать DATABASE_URL_FOR_FLASK из services.connections. "
        "Проверьте структуру проекта и наличие файла."
    ) from e

# this is the Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Указываем метаданные для autogenerate
target_metadata = db.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL_FOR_FLASK, # ← Берём URL из connections.py
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Создаём синхронный движок с URL из connections.py
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=DATABASE_URL_FOR_FLASK,  # ← Ключевое изменение!
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()