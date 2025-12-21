import os
import logging
import shutil

from flask import (Blueprint, request, redirect, url_for, flash,
                   render_template, session, current_app)
from werkzeug.utils import secure_filename

from extensions import db
from models import Category, SubCategory
from services import (ProductService, create_path_for_file, build_admin_orders_sort_column,
                      CartService, UserService, AdminService)
from forms import (CategoryForm, CategoryEditForm, ProductForm, ProductEditForm,
                   EditProfileForm)

logger = logging.getLogger(__name__)


admin = Blueprint(
    'admin',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/admin_static'
)


def login_admin():
    session['admin_logged'] = 1

def isLogged():
    return True if session.get('admin_logged') else False

def logout_admin():
    session.pop('admin_logged', None)


@admin.route('/login', methods=['GET', 'POST'])
def login():
    if isLogged():
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        if request.form['user'] == 'admin' and request.form['psw'] == '12345':
            login_admin()
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Неверный логин и/или пароль", category="error")

    return render_template('admin/login.html')

@admin.route('/logout', methods=['GET', 'POST'])
def logout():
    if not isLogged():
        return redirect(url_for('admin.login'))
    logout_admin()
    return redirect(url_for('admin.login'))

@admin.before_request
def require_login():
    """Функция запрещает вход НЕ администратору на любую страницу админ-панели (кроме выбранных)"""
    allowed_endpoints = ('admin.login', 'admin.static')
    if not isLogged() and request.endpoint not in allowed_endpoints:
        return redirect(url_for('admin.login'))


@admin.route('/')
def index():
    return render_template('admin/dashboard.html')

@admin.route('/dashboard')
def dashboard():
    admin_service = AdminService(db)
    count_users = len(admin_service.get_users_with_orders_count())
    count_products = len(admin_service.get_all_products())
    count_completed_order = len(admin_service.get_completed_orders())
    income_per_week = admin_service.get_week_income()
    last_orders = admin_service.get_last_5_orders()

    return render_template(
        'admin/dashboard.html',
        active_tab='dashboard',
        count_users=count_users,
        count_products=count_products,
        count_completed_order=count_completed_order,
        income_per_week=income_per_week,
        last_orders=last_orders
    )


@admin.route('/users')
def users():
    admin_service = AdminService(db)
    users_with_orders = admin_service.get_users_with_orders_count()
    return render_template(
        'admin/users.html',
        active_tab='users',
        users_with_orders=users_with_orders
    )

@admin.route('/user/<int:user_id>', methods=['GET', 'POST'])
def user_edit(user_id):
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id=user_id)

    form = EditProfileForm(data={
        'surname': user.surname,
        'name': user.name,
        'email': user.email,
        'phone': user.phone
    })

    if request.method == 'POST':
        form = EditProfileForm()
        if form.validate_on_submit():
            is_updated = user_service.edit_profile(user_id=user_id, form=form)
            if is_updated:
                return redirect(url_for('admin.users'))

    return render_template(
        'admin/user_edit.html',
        form=form,
        user=user
    )

@admin.route('/user/delete_user/<int:user_id>', methods=['GET', 'POST'])
def user_delete(user_id):
    admin_service = AdminService(db)

    admin_service.delete_profile(user_id=user_id)
    return redirect(url_for('admin.users'))


@admin.route('/products')
def products():
    """Функция генерирует страницу со всеми категориями, подкатегориями и товарами"""
    product_service = ProductService(db)
    categories = product_service.get_category_list()

    # Для каждой категории получаем ее подкатегории
    categories_with_products = []
    for cat in categories:
        subcategories = product_service.get_subcategories_by_category_slug(cat_slug=cat.slug)
        subcategories_data = []
        for subcategory in subcategories:
            products_list = product_service.get_products_by_subcategory_slug(subcat_slug=subcategory.slug)
            subcategories_data.append({
                'subcategory': subcategory,
                'products': products_list
            })
        categories_with_products.append({
            'category': cat,
            'subcategories': subcategories_data,
        })

    return render_template(
        'admin/products.html',
        active_tab='products',
        categories_data=categories_with_products,
    )

@admin.route('/create_category', methods=['GET', 'POST'])
@admin.route('/create_category/<cat_slug>', methods=['GET', 'POST'])
def create_category(cat_slug=None):
    if not isLogged():
        return redirect(url_for('admin.login'))
    """Функция создает категорию. Если передан аргумент cat_id, то создается подкатегория"""
    form = CategoryForm()
    product_service = ProductService(db)

    if form.validate_on_submit():
        if not cat_slug:
            ok = product_service.create_category(form=form, object=Category)
            if not ok:
                flash("Категория с указанным именем уже существует!", category="danger")
                return render_template(
                    'admin/category_form.html',
                    form=form,
                )
            flash("Категория создана!", category="success")
        else:
            cat_id = product_service.get_category_by_slug(cat_slug=cat_slug).id
            ok = product_service.create_category(form=form, object=SubCategory, cat_id=cat_id)
            if not ok:
                flash("Подкатегория с указанным именем уже существует!", category="danger")
                return render_template(
                    'admin/category_form.html',
                    form=form,
                )
            flash("Подкатегория создана!", category="success")

        # Сохраняем фото на диск
        file = form.picture.data
        file_name = secure_filename(file.filename)
        filepath = create_path_for_file(current_app,
                                        subfolders='categories',
                                        file_name=file_name) \
            if not cat_slug else create_path_for_file(current_app,
                                                      subfolders=['subcategories', cat_slug],
                                                      file_name=file_name
                                                      )
        file.save(filepath)
        flash('Фото успешно загружено!', category="success")

        return redirect(url_for('admin.products'))

    title = "Добавить категорию" if not cat_slug else "Добавить подкатегорию"
    return render_template(
        'admin/category_form.html',
        form=form,
        title=title
    )

@admin.route('/edit_category/<slug>', methods=['GET', 'POST'])
def edit_category(slug):
    product_service = ProductService(db)
    is_subcategory = request.args.get('is_subcategory')
    if not is_subcategory:
        category = product_service.get_category_by_slug(cat_slug=slug)
        title = "Редактировать категорию"
    else:
        category = product_service.get_subcategory_by_slug(subcat_slug=slug)
        title = "Редактировать подкатегорию"
        cat_slug = product_service.get_category_by_subcategory_slug(subcat_slug=slug).slug
    form = CategoryEditForm(obj=category)

    # Получаем путь к текущему фото
    file_path = create_path_for_file(current_app,
                                     subfolders='categories',
                                     file_name=category.picture
                                     ) \
        if not is_subcategory else create_path_for_file(current_app,
                                                        subfolders=['subcategories', cat_slug],
                                                        file_name=category.picture)


    if form.validate_on_submit():
        product_service.edit_category(form=form, category=category)
        # Если загружено новое фото
        if form.picture.data:
            # Удаляем старое фото
            try:
                os.remove(file_path)
            except FileNotFoundError:
                flash("Не удается найти указанный файл", category="error")

            # Загружаем новое фото
            file = form.picture.data
            file_name = secure_filename(file.filename)
            file_path = create_path_for_file(current_app,
                                            subfolders='categories',
                                            file_name=file_name
                                            ) \
                if not is_subcategory else create_path_for_file(current_app,
                                                          subfolders=['subcategories', cat_slug],
                                                          file_name=file_name)
            file.save(file_path)
            flash('Фото успешно обновлено!', category="success")

        return redirect(url_for('admin.products'))

    # Предзаполним текущие значения
    return render_template(
        'admin/category_form.html',
        form=form,
        title=title
    )


@admin.route('/delete_category/<slug>', methods=['POST'])
def delete_category(slug):
    product_service = ProductService(db)
    is_subcategory = request.args.get('is_subcategory')
    object = Category if not is_subcategory else SubCategory

    # Удаляем фото
    cat_slug = product_service.get_category_by_subcategory_slug(subcat_slug=slug).slug
    file_name = product_service.get_subcategory_by_slug(subcat_slug=slug).picture
    file_path = create_path_for_file(current_app,
                                     subfolders='categories',
                                     file_name=file_name
                                     ) \
        if not is_subcategory else create_path_for_file(current_app,
                                                        subfolders=['subcategories', cat_slug],
                                                        file_name=file_name)
    try:
        os.remove(file_path)
    except FileNotFoundError:
        flash("Не удается найти указанный файл", category="error")

    # Удаляем запись в БД
    product_service.delete_category(cat_slug=slug, object=object)

    # Проверяем, есть ли товары в категории
    if not file_name:
        return redirect(url_for('admin.products'))

    return redirect(url_for('admin.products'))


@admin.route('/create_product/<cat_slug>/<subcat_slug>', methods=['GET', 'POST'])
def create_product(cat_slug, subcat_slug):
    """Функция создает товар"""
    form = ProductForm()
    product_service = ProductService(db)
    subcat_name = product_service.get_subcategory_by_slug(subcat_slug=subcat_slug).name

    if form.validate_on_submit():
        cat_id = product_service.get_category_by_slug(cat_slug=cat_slug).id
        subcat_id = product_service.get_subcategory_by_slug(subcat_slug=subcat_slug).id

        # Проверяем уникальность наименования товара
        try:
            product = product_service.create_product(form=form, cat_id=cat_id, subcat_id=subcat_id)
            if not product:
                flash("Товар с указанным именем уже существует!", category="danger")
                return render_template(
                    'admin/product_form.html',
                    form=form,
                )

            # Сохраняем фото на диск
            files = [form.main_image.data] + list(request.files.getlist('extra_images'))
            create_path_for_file(current_app,
                                 subfolders=['products', cat_slug, subcat_slug, product.slug],
                                 file_name=files,
                                 product_id=product.id,
                                 db=db
            )
            flash("Товар создан!", category="success")
        except Exception:
            flash("Непредвиденная ошибка")
        return redirect(url_for('admin.products'))

    return render_template(
        'admin/product_form.html',
        form=form,
        title=subcat_name
    )

@admin.route('/edit_product/<product_slug>', methods=['GET', 'POST'])
def edit_product(product_slug):
    """Функция редактирует товар"""
    product_service = ProductService(db)

    product = product_service.get_product_by_slug(product_slug=product_slug)
    form = ProductEditForm(obj=product)

    if form.validate_on_submit():
        # Сохраняем изменения в данных товара
        product_service.edit_product(form=form, product=product)

        # Формируем путь до папки с изображениями
        catalog_bp = current_app.blueprints.get('catalog')
        product_folder = os.path.join(
            catalog_bp.root_path,
            'static', 'images', 'products',
            product.category.slug,
            product.subcategory.slug,
            product.slug
        )

        # Сохраняем новые изображения (если есть)
        all_files = []
        if form.main_image.data and form.main_image.data.filename:
            all_files.append(form.main_image.data)
        for img in request.files.getlist('extra_images'):
            if img.filename:
                all_files.append(img)

        if all_files:
            # Удаляем папку со старыми изображениями (только если загружены новые)
            if os.path.exists(product_folder):
                shutil.rmtree(product_folder)
            # Удаляем пути до фото в БД:
            product_service.delete_files_path(product_id=product.id)
            # Сохраняем новые фото
            create_path_for_file(current_app,
                                 subfolders=['products',
                                             product.category.slug,
                                             product.subcategory.slug,
                                             product.slug
                                             ],
                                 file_name=all_files,
                                 product_id=product.id,
                                 db=db
                                 )

        return redirect(url_for('admin.products'))

    # Предзаполним текущие значения
    return render_template(
        'admin/product_form.html',
        form=form,
        title="Редактировать товар"
    )

@admin.route('/delete_product/<product_slug>', methods=['POST'])
def delete_product(product_slug):
    product_service = ProductService(db)
    product = product_service.get_product_by_slug(product_slug=product_slug)

    # Удаляем папку с изображениями
    try:
        catalog_bp = current_app.blueprints.get('catalog')
        if catalog_bp is None:
            logger.error("Blueprint 'catalog' не найден!")
            flash("Blueprint 'catalog' не найден!", category="danger")
            return redirect(url_for('admin.products'))

        product_folder = os.path.join(
            catalog_bp.root_path,
            'static', 'images', 'products',
            product.category.slug,
            product.subcategory.slug,
            product.slug
        )

        if os.path.exists(product_folder):
            shutil.rmtree(product_folder)
            flash("Изображения товара удалены", category="success")
        else:
            flash("Папка с изображениями не найдена", category="warning")

    except Exception as e:
        logger.error(f"Ошибка при удалении папки товара: {e}")
        flash(f"Не удалось удалить файлы товара", category="error")

    # Удаляем продукт из БД
    product_service.delete_product(product_slug=product_slug)

    return redirect(url_for('admin.products'))


@admin.route('/orders')
@admin.route('/orders/<int:user_id>')
def orders(user_id=None):
    admin_service = AdminService(db)
    sort_column, sort_by, order = build_admin_orders_sort_column('time')
    # Получаем дату из параметров
    date_filter = request.args.get('date')

    if not user_id:
        list_orders = admin_service.get_orders_for_admin(
            sort_column=sort_column,
            date_filter=date_filter,
            user_id=user_id
        )
        title = 'Заказы'
    else:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id=user_id)
        list_orders = admin_service.get_orders_for_admin(
            sort_column=sort_column,
            date_filter=date_filter,
            user_id=user_id
        )
        title = f'{user.surname} {user.name}: заказы'

    return render_template(
        'admin/orders.html',
        title=title,
        orders=list_orders,
        sort_by=sort_by,
        order=order,
    )

"""Внедряем кастомный фильтр в Jinja2"""
@admin.app_template_filter('datetime')
def format_datetime(value, fmt='%d.%m.%Y %H:%M:%S'):
    if value is None:
        return ''
    return value.strftime(fmt)

@admin.app_template_filter('money')
def format_money(value):
    if value is None:
        return ''
    value = float(value)
    value = int(value)
    s = f'{value:,}'
    return s.replace(',', ' ')

@admin.route('/order/<int:order_id>')
def order(order_id):
    cart_service = CartService(db)
    admin_service = AdminService(db)

    order_items = cart_service.get_products_by_order_id(order_id=order_id)
    order_data = admin_service.get_order_by_id(order_id=order_id)
    return render_template(
        'admin/order.html',
        order_items=order_items,
        order=order_data,
    )