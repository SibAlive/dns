"""Формируем строку для подключения к БД"""
from environs import Env
from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

env = Env()
env.read_env()

@dataclass
class Database:
    database: str
    host: str
    port: int
    user: str
    password: str

# URL для подключения к служебной БД 'postgres' для создания новой базы данных
db_main = Database(
    database=env("POSTGRES_MAIN_DB"),
    host=env("POSTGRES_MAIN_HOST"),
    port=env.int("POSTGRES_MAIN_PORT", 5432),
    user=env("POSTGRES_MAIN_USER"),
    password=env("POSTGRES_MAIN_PASSWORD")
    )

db_new = Database(
    database=env("POSTGRES_DB"),
    host=env("POSTGRES_HOST"),
    port=env.int("POSTGRES_PORT", 5432),
    user=env("POSTGRES_USER"),
    password=env("POSTGRES_PASSWORD")
    )

DATABASE_URL_FOR_FLASK = (
    f"postgresql+psycopg2://"
    f"{db_new.user}:{db_new.password}@"
    f"{db_new.host}:{db_new.port}/{db_new.database}"
)

ADMIN_USERNAME = env("ADMIN_USERNAME", 'admin')
ADMIN_PASSWORD = env("ADMIN_PASSWORD", 'password')


# Создаем асинхронный движок SQLAlchemy
engine = create_engine(DATABASE_URL_FOR_FLASK)

# Создаем фабрику сессий
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)