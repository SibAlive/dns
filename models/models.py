from flask import url_for
from sqlalchemy.orm import relationship

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    surname = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    phone = db.Column(db.String, nullable=True, unique=True)
    psw = db.Column(db.Text, nullable=False)
    avatar = db.Column(db.LargeBinary, default=None)
    time = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    cart_item = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    favorite = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    order = relationship("Order", back_populates="user", cascade="all, delete-orphan")


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    slug = db.Column(db.Text, nullable=False, unique=True, index=True)
    picture = db.Column(db.Text, nullable=False)

    subcategory = relationship("SubCategory", back_populates="category", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")

    def get_absolute_url(self):
        return url_for('catalog.subcategory', category_slug=self.slug)


class SubCategory(db.Model):
    __tablename__ = "sub_categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.Text, nullable=False)
    slug = db.Column(db.Text, nullable=False, unique=True, index=True)
    picture = db.Column(db.Text, nullable=False)

    category = relationship("Category", back_populates="subcategory")
    products = relationship("Product", back_populates="subcategory", cascade="all, delete-orphan")

    def get_absolute_url(self):
        return url_for('catalog.products', subcategory_slug=self.slug)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    subcategory_id = db.Column(db.Integer, db.ForeignKey("sub_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.Text, nullable=False)
    slug = db.Column(db.Text, nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0) # Остатки на складе
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now()) # Дата создания
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now()) # Дата посл. обновления
    sku = db.Column(db.String, nullable=True) # Артикул товара
    weight = db.Column(db.Float, nullable=True) # Вес товара

    cart_item = relationship("CartItem", back_populates="products")
    favorite = relationship("Favorite", back_populates="products")
    order_item = relationship("OrderItem", back_populates="products", cascade="all, delete-orphan")
    images = relationship("ProductImage",
                          back_populates="product",
                          order_by="ProductImage.sort_order",
                          cascade="all, delete-orphan")
    old_price = relationship("ProductPrice", back_populates="product", cascade="all, delete-orphan")

    category = relationship("Category", back_populates="products")
    subcategory = relationship("SubCategory", back_populates="products")

    @property
    def latest_price(self):
        """Последня цена или none"""
        if self.old_price:
            return max(self.old_price, key=lambda p: p.created_at)
        return None

    def get_absolute_url(self):
        return url_for('catalog.product', product_slug=self.slug)


class ProductImage(db.Model):
    __tablename__ = "product_images"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = db.Column(db.String(255), nullable=False)
    sort_order = db.Column(db.Integer, default=False) # Порядок отображения
    is_main = db.Column(db.Boolean, default=False) # Главное фото
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    product = relationship("Product", back_populates="images")


class ProductPrice(db.Model):
    __tablename__ = "product_prices"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    product = relationship("Product", back_populates="old_price")


class CartItem(db.Model):
    """Корзина товаров"""
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, server_default='1')

    user = relationship("User", back_populates="cart_item")
    products = relationship("Product", back_populates="cart_item")


class Favorite(db.Model):
    """Избранное"""
    __tablename__ = "favorites"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    user = relationship("User", back_populates="favorite")
    products = relationship("Product", back_populates="favorite")

class Order(db.Model):
    """Заказы"""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    status = db.Column(db.String, nullable=False)
    total_amount = db.Column(db.Float, nullable=False) # Общая стоимость заказа
    payment_method = db.Column(db.String, nullable=False) # Способ оплаты
    shipping_method = db.Column(db.String, nullable=False) # Способ доставки
    shipping_address = db.Column(db.String, nullable=True) # Адрес доставки
    comment = db.Column(db.Text, nullable=True) # Комментарий к заказу
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())  # Дата создания
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(),
                           onupdate=db.func.now())  # Дата посл. обновления
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)  # Дата оплаты

    order_item = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    user = relationship("User", back_populates="order")

class OrderItem(db.Model):
    """Список товаров в заказе"""
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    name = db.Column(db.String, nullable=False) # Наименование товара на момент заказа
    price = db.Column(db.Float, nullable=False) # Цена товара на момент заказа
    quantity = db.Column(db.Integer, nullable=False) # Количество
    total_price = db.Column(db.Float, nullable=False)

    order = relationship("Order", back_populates="order_item")
    products = relationship("Product", back_populates="order_item")