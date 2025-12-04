from flask import flash
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from werkzeug.security import generate_password_hash
from slugify import slugify
import logging

from models import (User, Category, SubCategory, Product, CartItem, Favorite,
                    Order, OrderItem)


logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db):
        self.db = db

    def user_register(self, *, form):
        """Функция регистрации пользователя"""
        try:
            psw_hash = generate_password_hash(form.psw.data)

            new_user = User(
                surname=form.surname.data,
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data if form.phone.data else None,
                psw=psw_hash,
            )

            self.db.session.add(new_user)
            self.db.session.commit()
            flash("Вы успешно зарегистрированы", category="success")
            return new_user
        except IntegrityError as e:
            self.db.session.rollback()
            if isinstance(e.orig, UniqueViolation):
                # Анализируем сообщение ошибки, чтобы определить какое поле нарушено
                error_message = str(e.orig)
                if "email" in error_message:
                    flash("Пользователь с таким email уже зарегистрирован", category="error")
                elif "phone" in error_message:
                    flash("Пользователь с таким номером телефона уже зарегистрирован", category="error")
            else:
                logger.error("Ошибка при добавлении в БД: " + str(e))
        except Exception as e:
            self.db.session.rollback()
            logger.error("Ошибка при добавлении в БД: " + str(e))
            return False

    def get_user_by_id(self, *, user_id):
        try:
            result = self.db.session.execute(
                select(User)
                .where(User.id == user_id)
            )
            user = result.scalar()
            if not user:
                logger.warning("Пользователь не найден")
                return False
            return user
        except Exception as e:
            logger.error("Ошибка получения данных из БД"+str(e))

        return False

    def get_user(self, *, form):
        """Функция для входа - возвращает пользователя по email или номеру телефона"""
        login_type = form.login_type.data
        if login_type == 'email':
            email = form.email.data
            user = self.db.session.execute(
                select(User).where(User.email == email)
            ).scalars().first()
        elif login_type == 'phone':
            phone = form.phone.data
            user = self.db.session.execute(
                select(User).where(User.phone == phone)
            ).scalars().first()

        if user:
            return user
        return False

    def update_avatar(self, *, user_id, avatar):
        """Функция обновляет аватарку пользователя"""
        if not avatar:
            return False

        try:
            user = self.db.session.execute(
                    select(User).where(User.id == user_id)
            ).scalars().first()

            if not user:
                logger.warning("Пользователь не найден")
                return False
            user.avatar = avatar
            self.db.session.commit()
        except Exception as e:
            logger.error("Ошибка обновления аватара в БД " + str(e))
            return False
        return True

    def check_phone(self, *, user_id, user_phone):
        """Функция проверяет, соответствует ли указанный телефон и сохраненный в БД"""
        db_phone = self.db.session.execute(
            select(User.phone).where(User.id == user_id)
        ).first()
        logger.info(f"У пользователя {user_id} номер телефона: {user_phone}")

        if not (db_phone and db_phone == user_phone):
            return False
        return True

    def update_phone(self, *, user_id, user_phone):
        """Вносим/обновляем телефон пользователя"""
        user = self.db.session.execute(
            select(User).where(User.id == user_id)
        ).scalars().first()
        user.phone = user_phone
        self.db.session.commit()
        logger.info(f"Телефон {user_phone} обновлен для пользователя {user.surname} {user.name}")

    def edit_profile(self, *, user_id, form):
        """Функция редактирует данные пользователя"""
        # Проверяем уникальность email
        email = self.db.session.execute(
            select(User.email).where(User.id != user_id, User.email == form.email.data)
        ).scalars().first()
        if email:
            flash("Данный emal адрес уже занят")
            return False
        # Проверяем уникальность телефона
        phone = self.db.session.execute(
            select(User.phone).where(User.id != user_id, User.phone == form.phone.data)
        ).scalars().first()
        if phone:
            flash("Данный номер телефона уже занят")
            return False

        user = self.db.session.execute(
            select(User).where(User.id == user_id)
        ).scalars().first()
        user.surname = form.surname.data
        user.name = form.name.data
        user.email = form.email.data
        user.phone = form.phone.data
        self.db.session.commit()
        logger.info(f"Данные обновлены. Пользователь: {user_id}, фамилия: {form.surname.data}, "
                    f"имя: {form.name.data}, email: {form.email.data}, телефон: {form.phone.data}")
        flash("Данные сохранены", category="success")
        return True

    def get_users(self):
        """Функция возвращает всех пользователей"""
        users = self.db.session.execute(
            select(User).order_by(User.id)
        )


class ProductService:
    def __init__(self, db):
        self.db = db

    """Категории"""
    def get_category_list(self):
        """Функция возвращает список всех категорий"""
        try:
            result = self.db.session.execute(
                select(Category)
                .order_by(Category.id)
            )
            categories = result.scalars()
            if not categories:
                logger.warning("Категории отсутствуют")
                return False
            return categories
        except Exception as e:
            logger.error("Ошибка получения данных из БД" + str(e))

        return False

    def get_category_by_slug(self, *, cat_slug):
        """Возвращает категорию по ее slug"""
        category = self.db.session.execute(
            select(Category).where(Category.slug == cat_slug)
        ).scalar()
        return category

    def get_category_by_product_slug(self, *, product_slug):
        """Возвращает категорию по slug продукта"""
        category = self.db.session.execute(
            select(Category)
            .join(Product)
            .where(Product.slug == product_slug)
        ).scalar()
        return category

    def get_category_by_subcategory_slug(self, *, subcat_slug):
        """Возвращает категорию по slug подкатегории"""
        category = self.db.session.execute(
            select(Category).
            join(SubCategory)
            .where(SubCategory.slug == subcat_slug)
        ).scalar()
        return category

    def create_category(self, *, form, object, cat_id=None):
        """Функция создает новую категорию"""
        # Проверка уникальности наименования
        if self.db.session.execute(
                select(object).where(object.name == form.name.data)).first():
            return False

        if object is Category:
            category = object(
                name=form.name.data,
                slug=slugify(form.name.data),
                picture=form.picture.data.filename,
            )
        else:
            category = object(
                category_id=cat_id,
                name=form.name.data,
                slug=slugify(form.name.data),
                picture=form.picture.data.filename,
            )
        self.db.session.add(category)
        self.db.session.commit()
        return True

    def edit_category(self, *, form, category):
        """Функция редактирует существующую категорию"""
        if category is Category:
            message = 'Категория обновлена!'
        else:
            message = 'Подкатегория обновлена!'
        category.name = form.name.data
        category.slug = slugify(form.name.data),

        # Обновляем имя файла только если загружен новый файл
        if form.picture.data:
            category.picture = form.picture.data.filename
        self.db.session.commit()
        flash(message=message, category="success")

    def delete_category(self, *, cat_slug, object):
        """Функция удаляет выбранную категорию"""
        category = self.db.session.execute(
            select(object).where(object.slug == cat_slug)
        ).scalar_one()

        if category.products:
            flash("Нельзя удалить категорию - в ней есть товары!")
            return False

        self.db.session.delete(category)
        self.db.session.commit()
        message = "Категория удалена!" if object is Category else "Подкатегория удалена!"
        flash(message=message, category="success")

        return True


    """Подкатегории"""
    def get_subcategories_by_category_slug(self, *, cat_slug):
        """Возвращает список подкатегорий, по slug категории"""
        subcategories = self.db.session.execute(
            select(SubCategory)
            .join(SubCategory.category)
            .where(Category.slug == cat_slug)
            .order_by(SubCategory.id)
        ).scalars().all()
        return subcategories

    def get_subcategory_by_slug(self, *, subcat_slug):
        """Возвращает подкатегорию по ее slug"""
        subcategory = self.db.session.execute(
            select(SubCategory).where(SubCategory.slug == subcat_slug)
        ).scalar()
        return subcategory

    def get_subcategory_by_product_slug(self, *, product_slug):
        """Возвращает подкатегорию по slug продукта"""
        subcategory = self.db.session.execute(
            select(SubCategory)
            .join(Product)
            .where(Product.slug == product_slug)
        ).scalar()
        return subcategory

    """Товары"""
    def get_product_by_slug(self, *, product_slug):
        """Возвращает продукт по его slug"""
        product = self.db.session.execute(
            select(Product).where(Product.slug == product_slug)
        ).scalar()
        return product

    def get_products_by_subcategory_slug(self, *, subcat_slug, order=Product.name):
        """Возвращает список продуктов, входящих в выбранную подкатегорию (по slug)"""
        products = self.db.session.execute(
            select(Product)
            .join(Product.subcategory)
            .where(SubCategory.slug == subcat_slug)
            .order_by(order)
        ).scalars().all()
        return products

    def get_random_products(self):
        """Возвращает список 16 случайных товаров для главной страницы"""
        random_products = self.db.session.execute(
            select(Product)
            .order_by(func.random())
            .limit(16)
        ).scalars().all()
        return random_products

    def create_product(self, *, form, cat_id, subcat_id):
        """Функция создает новый товар"""
        # Проверка уникальности наименования
        if self.db.session.execute(
                select(Product).where(Product.name == form.name.data)).first():
            return False

        product = Product(
            category_id=cat_id,
            subcategory_id=subcat_id,
            name=form.name.data,
            slug=slugify(form.name.data),
            description=form.description.data,
            picture=form.picture.data.filename,
            price=form.price.data,
            stock_quantity=form.stock_quantity.data,
            sku=form.sku.data,
            weight=form.weight.data
        )
        self.db.session.add(product)
        self.db.session.commit()
        return True

    def edit_product(self, *, form, product):
        """Функция редактирует существующий товар"""
        product.name = form.name.data
        product.slug = slugify(form.name.data),
        product.description = form.description.data
        product.price = form.price.data
        product.stock_quantity = form.stock_quantity.data
        product.sku = form.sku.data
        product.weight = form.weight.data

        # Обновляем имя файла только если загружен новый файл
        if form.picture.data:
            product.picture = form.picture.data.filename
        self.db.session.commit()
        flash(message="Товар обновлен", category="success")

    def delete_product(self, *, product_slug):
        """Функция удаляет выбранный товар"""
        product = self.db.session.execute(
            select(Product).where(Product.slug == product_slug)
        ).scalar_one()

        file_name = product.picture

        self.db.session.delete(product)
        self.db.session.commit()

        flash(message="Товар удален!", category="success")
        return file_name

    def get_product_balance(self, *, product_id):
        """Функция возвращает количество оставшегося товара"""
        product = self.db.session.execute(
            select(Product).where(Product.id == product_id)).scalar()
        stock_quantity = product.stock_quantity
        return stock_quantity


class CartService:
    def __init__(self, db):
        self.db = db

    """Корзина"""
    def add_product(self, *, user_id, product_id, quantity=1):
        """Функция добавляет товар в корзину (1 шт.)"""
        cart_item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )
        self.db.session.add(cart_item)
        self.db.session.commit()
        flash("Товар добавлен в корзину", category="success")

    def check_product(self, *, user_id, product_id):
        """Функция проверяет есть ли уже товар в корзине пользователя"""
        cart_item = self.db.session.execute(
            select(CartItem).where(
                CartItem.user_id==user_id,
                CartItem.product_id==product_id)).scalar()
        if cart_item:
            return cart_item.quantity
        return False

    def increase_product(self, *, user_id, product_id, quantity=1):
        """Функция увеличивает количество товара в корзине на 1"""
        cart_item = self.db.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id)).scalar()
        cart_item.quantity += quantity
        self.db.session.commit()
        flash("Количество товара увеличено", category="success")

    def remove_product(self, *, user_id, product_id):
        """Функция удаляет товар из корзины (1 шт.)"""
        cart_item = self.db.session.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id, CartItem.product_id == product_id)
        ).scalar()
        cart_item.quantity -= 1
        if cart_item.quantity == 0:
            self.db.session.delete(cart_item)
        flash("Товар удален", category="success")
        self.db.session.commit()

    def get_cart_items(self, *, user_id):
        """Возвращает все товары в корзине пользователя"""
        cart_items = self.db.session.execute(
            select(CartItem).where(CartItem.user_id == user_id)
        ).scalars().all()
        return cart_items


    """Избранное"""
    def get_favorites(self, *, user_id):
        """Возвращает список продуктов, которые находятся в избранном"""
        favorites = self.db.session.execute(
            select(Favorite).where(Favorite.user_id == user_id)
        ).scalars().all()
        return favorites

    def get_favorites_ids(self, *, user_id):
        """Возвращает список id продуктов, которые находятся в избранном"""
        favorites = self.db.session.execute(
            select(Favorite).where(Favorite.user_id == user_id)
        ).scalars().all()
        favorite_ids = [favorite.product_id for favorite in favorites]
        return favorite_ids

    def is_favorite(self, *, user_id, product_id):
        """Функция проверяет, находится ли товар в избранном"""
        favorite = self.db.session.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id, Favorite.product_id == product_id)
        ).first()
        if favorite:
            return True
        return False

    def add_to_favorite(self, *, user_id, product_id):
        """Добавляет товар в избранное"""
        favorite = Favorite(
            user_id=user_id,
            product_id=product_id,
        )
        self.db.session.add(favorite)
        self.db.session.commit()

    def remove_from_favorite(self, *, user_id, product_id):
        """Удаляет товар из избранного"""
        favorite = self.db.session.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id, Favorite.product_id == product_id)
        ).scalars().first()
        self.db.session.delete(favorite)
        self.db.session.commit()


    """Заказ"""
    def create_order(self, *, user_id, form, order_items):
        """Функция бронирования заказа"""
        try:
            # Создаем заказ
            new_order = Order(
                user_id=user_id,
                status="Забронирован",
                total_amount=form.total_amount.data,
                payment_method=form.payment_method.data,
                shipping_method=form.delivery_method.data,
                shipping_address=form.shipping_address.data,
                comment=form.comment.data,
            )
            self.db.session.add(new_order)
            self.db.session.flush() # Временно сохраняем данные в БД

            # Очищаем корзину пользователя
            cart_items = self.db.session.execute(
                select(CartItem).where(CartItem.user_id == user_id)
            ).scalars().all()
            for cart_item in cart_items:
                self.db.session.delete(cart_item)

            # Создаем список товаров в заказе
            for item in order_items:
                new_order_item = OrderItem(
                    order_id = new_order.id,
                    product_id = item.product_id,
                    name = item.products.name,
                    price = item.products.price,
                    quantity = item.quantity,
                    total_price = item.products.price * item.quantity,
                )
                self.db.session.add(new_order_item)

                # Уменьшаем остатки товара
                product = self.db.session.execute(
                    select(Product).where(Product.id == item.product_id).with_for_update()
                ).scalar_one_or_none()

                if product is None:
                    raise ValueError(f"Товар {item.name} больше не доступен")
                if product.stock_quantity < item.quantity:
                    raise ValueError(f"Недостаточно товара {product.name} в наличии")

                product.stock_quantity -= item.quantity

            self.db.session.commit()
            flash("Заказ зарезервирован на 24 часа", category="success")
        except Exception as e:
            self.db.session.rollback()
            logger.error("Ошибка оформления заказа " + str(e))

    def get_orders(self, *, user_id):
        """Возвращает список заказов пользователя"""
        orders = self.db.session.execute(
            select(Order).where(Order.user_id == user_id)
        ).scalars().all()
        return orders

    def buy_order(self, *, order_id):
        """Функция оплаты заказа"""
        # Меняем статус заказа
        order = self.db.session.execute(
            select(Order).where(Order.id == order_id)
        ).scalar_one_or_none()
        order.status = "Оплачен"

        self.db.session.commit()
        flash("Заказ оплачен", category="success")

    def cancel_order(self, *, order_id):
        """Функция отмены заказ"""
        try:
            # Меняем статус заказа
            order = self.db.session.execute(
                select(Order).where(Order.id == order_id)
            ).scalar_one_or_none()
            order.status = "Отменен"

            # Создаем список товаров в заказе
            order_items = self.db.session.execute(
                select(OrderItem).where(OrderItem.order_id == order.id)
            ).scalars().all()

            # Увеличиваем остатки товара
            for item in order_items:
                product = self.db.session.execute(
                    select(Product).where(Product.id == item.product_id)
                ).scalar_one_or_none()
                product.stock_quantity += item.quantity

            self.db.session.commit()
            logger.info(f"Заказ {order_id} отменен")

        except Exception as e:
            self.db.session.rollback()
            logger.error("Ошибка отмены заказа " + str(e))

    def get_expired_orders(self, *, cutoff):
        """Функция возвращает список истекших заказов"""
        expired_orders = self.db.session.execute(
            select(Order).where(Order.status == "Забронирован", Order.updated_at < cutoff)
        ).scalars().all()
        return expired_orders

    def get_products_by_order_id(self, *, order_id):
        """Функция возвращает список продуктов по id заказа (для повторного заказа)"""
        order_items = self.db.session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).scalars().all()
        return order_items
