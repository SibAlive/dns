import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from services import db, _db, DATABASE_URL_FOR_FLASK
from extensions import db as database


def create_database_if_not_exists():
    """Создает базу данных, если она не существует"""
    # Подключаемся к служебной БД 'postgres'
    conn = psycopg2.connect(
        host=_db.host,
        port=_db.port,
        user=_db.user,
        password=_db.password,
        database=_db.database,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # Необходимо для создания БД
    cur = conn.cursor()

    try:
        # Проверяем, существует ли БД
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db.database,))
        db_exists = cur.fetchone()
        if not db_exists:
            # Создаем БД
            cur.execute(f"CREATE DATABASE {db.database}")
            print(f"База данных {db.database} успешно создана")
        else:
            print(f"База данных {db.database} уже существует")
    finally:
        cur.close()
        conn.close()


def create_tables():
    """Создает таблицы, если их нет"""
    from models import Category, SubCategory
    # Создаем синхронный движок
    engine = create_engine(DATABASE_URL_FOR_FLASK, echo=True)

    # Создаем все таблицы
    database.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы")

    # Закрываем движок
    engine.dispose()


def main():
    try:
        # Создает БД
        create_database_if_not_exists()
        # создаем таблицы

        create_tables()
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        raise


if __name__ == "__main__":
    (main())