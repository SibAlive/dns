"""Данный модуль необходим для запуска админ панели на удаленном сервере"""
# Чтобы запустить админ панель через терминал, необходимо ввести:
# waitress-serve --host=localhost --port=5000 "wsgi:application"

from app import create_app


# Создаем приложение
application = create_app()