import os
import logging
from flask import flash

from .db_functions import CartService, ProductService


logger = logging.getLogger(__name__)


def create_path_for_file(current_app, bp, filename):
    # Получаем объект catalog blueprint
    catalog_bp = current_app.blueprints.get(bp)
    # Путь до папки
    upload_folder = os.path.join(catalog_bp.root_path, 'static', 'images')
    os.makedirs(upload_folder, exist_ok=True)
    # Путь до файла
    filepath = os.path.join(upload_folder, filename)
    return filepath


def add_product_to_cart(db, *, user_id, product_id):
    cart_service = CartService(db)
    product_service = ProductService(db)
    # Проверяем есть ли товар в наличии
    item_left = product_service.get_product_balance(product_id=product_id)
    # Проверяем есть ли уже этот товар в корзине
    cart_item = cart_service.check_product(user_id=user_id, product_id=product_id)
    if item_left > cart_item:
        if cart_item:
            cart_service.increase_product(user_id=user_id, product_id=product_id)
        else:
            cart_service.add_product(user_id=user_id, product_id=product_id)
    else:
        flash("Извините, товар закончился", category="warning")


def transfer_guest_cart_to_user(db, *, user_id, session):
    """Перенос корзины гостя в БД пользователя"""
    if 'cart' not in session:
        return

    cart_service = CartService(db)
    for item in session['cart']:
        if cart_service.check_product(user_id=user_id, product_id=item['product_id']):
            cart_service.increase_product(
                user_id=user_id,
                product_id=item['product_id'],
                quantity=item['quantity'])
        else:
            cart_service.add_product(
                user_id=user_id,
                product_id=item['product_id'],
                quantity=item['quantity'],
            )

    del session['cart'] # Очищаем сессию
    session.modified = True
    logger.info("Корзина сохранена после входа")


def transfer_guest_favorite_to_user(db, *, user_id, session):
    """Перенос избранного гостя в БД пользователя"""
    if 'favorite' not in session:
        return

    cart_service = CartService(db)
    for item in session['favorite']:
        cart_service.add_to_favorite(user_id=user_id, product_id=item['product_id'])

    del session['favorite'] # Очищаем сессию
    session.modified = True
    logger.info("Избранное сохранено после входа")