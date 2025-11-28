"""Данный модуль необходим, чтобы избежать циклических импортов"""
from flask_sqlalchemy import SQLAlchemy


# Создаем объект db, но НЕ привязываем его к приложению сразу
db = SQLAlchemy()