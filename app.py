import os
import logging
from flask import Flask, g
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

from extensions import db
from services import DATABASE_URL_FOR_FLASK, create_inject_cart_len, UserService
from blueprints import header, catalog, admin
from services.UserLogin import UserLogin
from sheduler import setup_scheduler


# Инициализируем логгер
logger = logging.getLogger(__name__)


def create_app():
    # Задаем базовую конфигурацию логирования
    logging.basicConfig(
        level=logging.getLevelName(level=logging.DEBUG),
        format="[%(asctime)s] #%(levelname)-8s %(filename)s:%(lineno)d - %(name)s - %(message)s"
    )

    # Указываем путь для сохранения файлов
    upload_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images')

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'super_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL_FOR_FLASK
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['CATALOG_UPLOAD_FOLDER'] = os.path.join(upload_folder, 'catalog')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 МБ максимальный размер файла
    app.config['SCHEDULER_API_ENABLED'] = True

    # Активируем глобальную защиту от CSRF-атак (необходимо для AJAX-запросов)
    csrf = CSRFProtect(app)

    # Это гарантирует, что CSRF токен будет доступен в шаблонах
    @app.before_request
    def before_request():
        g.csrf_token=generate_csrf()

    # Создаем папку для загрузок, если ее нет
    os.makedirs(app.config['CATALOG_UPLOAD_FOLDER'], exist_ok=True)

    # Подключаем blueprints
    app.register_blueprint(header, url_prefix='/')
    app.register_blueprint(catalog, url_prefix='/catalog')
    app.register_blueprint(admin, url_prefix='/admin')

    # Подключаем контекстный процессор (определяет переменную в каждом html шаблоне)
    app.context_processor(create_inject_cart_len(db))

    # Инициализируем расширения
    db.init_app(app)

    # Настройка доступа к страницам неавторизованным пользователям
    login_manager = LoginManager(app)
    login_manager.login_view = 'header.login'
    login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
    login_manager.login_message_category = 'success'
    @login_manager.user_loader
    def load_user(user_id):
        # Получаем пользователя из БД
        return UserLogin().fromDB(db, user_id)

    # Настройка планировщика задач
    scheduler = setup_scheduler(db, app)
    scheduler.init_app(app)
    scheduler.start()
    logging.info("Планировщик задач запущен")

    return app