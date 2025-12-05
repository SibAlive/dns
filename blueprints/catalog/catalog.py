from flask import (Blueprint, request, redirect, render_template,
                   jsonify, url_for, session, flash)
from flask_login import current_user, login_required
from sqlalchemy import desc, asc

from services import UserService, ProductService, CartService, add_product_to_cart
from extensions import db
from models import Product
from forms import OrderForm


catalog = Blueprint(
    'catalog',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/catalog_static',
)


@catalog.route('/')
def catalog_index():
    product_service = ProductService(db)
    categories = product_service.get_category_list()
    cats_with_subcats = []
    breadcrumbs = [
        {'name': 'DNS', 'endpoint': 'header.index'},
        {'name': 'Каталог', 'endpoint': None}
    ]
    for category in categories:
        subcategories = product_service.get_subcategories_by_category_slug(cat_slug=category.slug)
        cats_with_subcats.append({'cat': category,
                                  'subcat': subcategories})

    return render_template(
        "catalog/catalog.html",
        categories=cats_with_subcats,
        breadcrumbs=breadcrumbs
    )

@catalog.route('/category/<category_slug>')
def subcategory(category_slug):
    product_service = ProductService(db)
    subcategories = product_service.get_subcategories_by_category_slug(cat_slug=category_slug)

    category_name =  product_service.get_category_by_slug(cat_slug=category_slug).name
    breadcrumbs = [
        {'name': 'DNS', 'endpoint': 'header.index'},
        {'name': 'Каталог', 'endpoint': 'catalog.catalog_index'},
        {'name': category_name, 'endpoint': None},
    ]
    return render_template(
        'catalog/catalog.html',
        categories=subcategories,
        cat_slug_if_subcats=category_slug,
        breadcrumbs=breadcrumbs,
    )

@catalog.route('/subcategory/<subcategory_slug>')
def products(subcategory_slug):
    product_service = ProductService(db)
    cart_service = CartService(db)

    list_products = product_service.get_products_by_subcategory_slug(subcat_slug=subcategory_slug)
    category = product_service.get_category_by_subcategory_slug(subcat_slug=subcategory_slug)
    category_name = category.name
    category_slug = category.slug

    if current_user.is_authenticated:
        favorite_ids = cart_service.get_favorites_ids(user_id=current_user.get_id())
    else:
        favorite_items = session.get('favorite', [])
        favorite_ids = [int(item['product_id']) for item in favorite_items]

    subcategory_name = product_service.get_subcategory_by_slug(subcat_slug=subcategory_slug).name
    breadcrumbs = [
        {'name': 'DNS', 'endpoint': 'header.index', 'params': {}},
        {'name': 'Каталог', 'endpoint': 'catalog.catalog_index', 'params': {}},
        {'name': category_name, 'endpoint': 'catalog.subcategory', 'params': {'category_slug': category_slug}},
        {'name': subcategory_name, 'endpoint': None, 'params': {}},
    ]
    return render_template(
        'catalog/products.html',
        products=list_products,
        subcategory_slug=subcategory_slug,
        favorite_ids=favorite_ids,
        breadcrumbs=breadcrumbs,
        title=category_name
    )

@catalog.route('/product/<product_slug>')
def product(product_slug):
    product_service = ProductService(db)
    cart_service = CartService(db)

    product_card = product_service.get_product_by_slug(product_slug=product_slug)

    if current_user.is_authenticated:
        favorite_ids = cart_service.get_favorites_ids(user_id=current_user.get_id())
    else:
        favorite_items = session.get('favorite', [])
        favorite_ids = [int(item['product_id']) for item in favorite_items]

    category = product_service.get_category_by_product_slug(product_slug=product_slug)
    category_slug = category.slug
    category_name = category.name

    subcategory = product_service.get_subcategory_by_product_slug(product_slug=product_slug)
    subcategory_slug = subcategory.slug
    subcategory_name = subcategory.name

    product_name = product_service.get_product_by_slug(product_slug=product_slug).name
    breadcrumbs = [
        {'name': 'DNS', 'endpoint': 'header.index', 'params': {}},
        {'name': 'Каталог', 'endpoint': 'catalog.catalog_index', 'params': {}},
        {'name': category_name, 'endpoint': 'catalog.subcategory', 'params': {'category_slug': category_slug}},
        {'name': subcategory_name, 'endpoint': 'catalog.products', 'params': {'subcategory_slug': subcategory_slug}},
        {'name': product_name, 'endpoint': None, 'params': {}},
    ]

    return render_template(
        'catalog/product.html',
        product=product_card,
        favorite_ids=favorite_ids,
        breadcrumbs=breadcrumbs,
    )

@catalog.route('/product_sort/<subcategory_slug>')
def product_sort(subcategory_slug):
    """Функция сортировки товаров"""
    product_service = ProductService(db)
    sort_by = request.args.get('sort_by', 'name')
    order_direction = request.args.get('order', 'asc')
    cat_slug = product_service.get_category_by_subcategory_slug(subcat_slug=subcategory_slug).slug

    valid_sort = {'price': Product.price, 'name': Product.name}
    order_field = valid_sort.get(sort_by, Product.name)

    # Выбираем направление сортировки
    if order_direction.lower() == 'desc':
        order_field = desc(order_field)
    else:
        order_field = asc(order_field)

    list_products = product_service.get_products_by_subcategory_slug(
        subcat_slug=subcategory_slug,
        order=order_field
    )

    result = []
    for p in list_products:
        # Строим полный URL к изображению
        image_filename = f"images/{product_service.get_main_image(product_id=p.id).image_path}"
        image_url = url_for('catalog.static', filename=image_filename)
        print(image_url)
        result.append({
            'id': p.id,
            'category_id': p.category_id,
            'subcategory_id': p.subcategory_id,
            'name': p.name,
            'slug': p.slug,
            'description': p.description,
            'price': float(p.price),
            'stock_quantity': p.stock_quantity,
            'created_at': p.created_at,
            'updated_at': p.updated_at,
            'sku': p.sku,
            'weight': p.weight,
            'image_url': image_url
        })
    return jsonify({'products': result})


@catalog.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Функция добавляет товар в корзину или увеличивает его количество на 1"""
    if current_user.is_authenticated:   # Для авторизованных пользователей
        user_id = current_user.get_id()
        add_product_to_cart(db, user_id=user_id, product_id=product_id)
    else:   # Для гостей сохраняем товар в сессию, а не в БД
        cart = session.get('cart', [])
        # Проверяем, есть ли товар уже в корзине
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] += 1
                break
        else:
            cart.append({'product_id': product_id, 'quantity': 1})
        session['cart'] = cart
        session.modified = True
        flash("Товар добавлен в корзину", category='success')

    return redirect(request.referrer)


@catalog.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Функция уменьшает количество товара на 1 или удаляет его из корзины"""
    if current_user.is_authenticated:  # Для авторизованных пользователей
        user_id = current_user.get_id()
        cart_service = CartService(db)
        cart_service.remove_product(user_id=user_id, product_id=product_id)
    else: # Для гостей удаляем товар из сессии, а не из БД
        cart = session.get('cart', [])
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] -= 1
                if item['quantity'] == 0:
                    cart.remove(item)
        session['cart'] = cart
        session.modified = True
        flash("Количество товара уменьшено", category='success')

    return redirect(request.referrer)


@catalog.route('/cart')
def cart():
    """Функция отображения корзины для гостя и пользователя"""
    if current_user.is_authenticated:
        cart_service = CartService(db)
        cart_items = cart_service.get_cart_items(user_id = current_user.get_id())
    else:
        # Извлекаем корзину из сессии (список словарей)
        cart_data = session.get('cart', [])
        cart_items = []
        # Для каждого item получаем объект продукта
        # и создаем динамический класс CartItem на лету
        for item in cart_data:
            product = db.session.get(Product, item['product_id'])
            if product:
                cart_items.append(
                    type('CartItem', (), { # Создаем мета класс с именем 'CartItem'
                        'product_id': item['product_id'],
                        'quantity': item['quantity'],
                        'products': product
                    })() # () - создаем экземпляр класса
                )

    # Количество товаров в корзине
    cart_quantity = sum(item.quantity for item in cart_items)
    # Общая стоимость
    cart_total = sum(item.products.price * item.quantity for item in cart_items)
    return render_template(
        'catalog/cart.html',
        cart_items=cart_items,
        cart_quantity=cart_quantity,
        cart_total=cart_total,
    )


@catalog.route('/favorite')
def favorite():
    if current_user.is_authenticated:
        cart_service = CartService(db)
        favorite_items = cart_service.get_favorites(user_id=current_user.get_id())
        favorite_ids = cart_service.get_favorites_ids(user_id=current_user.get_id())
    else:
        # Извлекаем избранное из сессии (список словарей)
        favorite_data = session.get('favorite', [])
        favorite_items = []
        # Для каждого item получаем объект продукта
        # и создаем динамический класс Favorite на лету
        for item in favorite_data:
            product = db.session.get(Product, item['product_id'])
            if product:
                favorite_items.append(
                    type('Favorite', (), { # Создаем мета класс с именем 'Favorite'
                        'product_id': item['product_id'],
                        'products': product
                    })() # () - создаем экземпляр класса
                )
        favorite_ids = [favorite.product_id for favorite in favorite_items]

    return render_template(
        'catalog/favorite.html',
        favorite_items=favorite_items,
        favorite_ids = favorite_ids
    )

@catalog.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    product_id = request.json.get('product_id')
    user_id = current_user.get_id()
    if current_user.is_authenticated: # Для авторизованных пользователей
        cart_service = CartService(db)
        # Проверяем, находится ли товар в избранном
        is_favorite = cart_service.is_favorite(user_id=user_id, product_id=product_id)
        if is_favorite:
            # Удаляем товар из избранного
            cart_service.remove_from_favorite(user_id=user_id, product_id=product_id)
            status = 'removed'
        else:
            # Добавляем товар в избранное
            cart_service.add_to_favorite(user_id=user_id, product_id=product_id)
            status = 'added'
    else: # Для гостей
        # Проверяем, находится ли товар в избранном
        favorite_items = session.get('favorite', [])
        for item in favorite_items:
            if item['product_id'] == product_id:
                favorite_items.remove(item)
                status = 'removed'
                break
        else:
            favorite_items.append({'product_id': product_id})
            status = 'added'
        session['favorite'] = favorite_items
        session.modified = True

    return jsonify({'status': status})

@catalog.route('/order', methods=['GET', 'POST'])
@login_required
def order():
    """Функция отображения оформления заказа"""
    cart_service = CartService(db)
    user_service = UserService(db)

    user_id = current_user.get_id()
    order_items = cart_service.get_cart_items(user_id=user_id)

    # Количество товаров в корзине
    order_quantity = sum(item.quantity for item in order_items)
    # Общая стоимость
    order_total = sum(item.products.price * item.quantity for item in order_items)

    user = user_service.get_user_by_id(user_id=current_user.get_id())
    user_phone, user_email = user.phone, user.email
    form = OrderForm()
    form.email.data = user.email
    form.total_amount.data = order_total
    if user_phone:
        form.phone.data = user_phone
        phone_readonly = True
    else:
        phone_readonly = False

    if form.validate_on_submit():
        user_phone = request.form.get('phone')
        # Проверяем, есть ли телефон в БД (и соответствует ли он)
        is_phone = user_service.check_phone(user_id=user_id, user_phone=user_phone)
        if not is_phone:
            # Здесь должна быть валидация номера телефона
            # После валидации вносим телефон в БД
            user_service.update_phone(user_id=user_id, user_phone=user_phone)

        cart_service.create_order(user_id=user_id, form=form, order_items=order_items)
        return render_template(
            'catalog/orders.html',
            order_items=order_items
        )

    return render_template(
        'catalog/order.html',
        form=form,
        phone_readonly=phone_readonly,
        order_items=order_items,
        order_quantity=order_quantity,
        order_total=order_total,
    )

@catalog.route('/orders', methods=['GET', 'POST'])
@login_required
def orders():
    """Отображает страницу со всеми заказами пользователя"""
    cart_service = CartService(db)
    orders_list = cart_service.get_orders(user_id=current_user.get_id())
    return render_template(
        'catalog/orders.html',
        orders=orders_list
    )

@catalog.route('/order/buy_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def buy_order(order_id):
    """Оплата заказа"""
    cart_service = CartService(db)
    cart_service.buy_order(order_id=order_id)
    return redirect(request.referrer)

@catalog.route('/order/cancel_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def cancel_order(order_id):
    """Отмена заказа"""
    cart_service = CartService(db)
    cart_service.cancel_order(order_id=order_id)

    return redirect(request.referrer)

@catalog.route('/order/repeat_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def repeat_order(order_id):
    user_id = current_user.get_id()
    cart_service = CartService(db)
    order_items = cart_service.get_products_by_order_id(order_id=order_id)

    for product in order_items:
        for _ in range(product.quantity):
            add_product_to_cart(db, user_id=user_id, product_id=product.id)

    return redirect(url_for('catalog.cart'))