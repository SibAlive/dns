import os
from flask import (Blueprint, request, redirect, url_for, flash,
                   render_template, session, current_app)
from werkzeug.utils import secure_filename

from extensions import db
from models import User, Category, SubCategory, Product
from services import ProductService, create_path_for_file
from forms import CategoryForm, CategoryEditForm, ProductForm, ProductEditForm

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
    """Функция запрещает вход НЕадминистратору на любую страницу админ-панели (кроме выбранных)"""
    allowed_endpoints = ('admin.login', 'admin.static')
    if not isLogged() and request.endpoint not in allowed_endpoints:
        return redirect(url_for('admin.login'))


@admin.route('/')
def index():
    return render_template('admin/dashboard.html')


@admin.route('/dashboard')
def dashboard():
    return render_template('admin/dashboard.html', active_tab='dashboard')


@admin.route('/users')
def users():
    return render_template('admin/users.html', active_tab='users')


"""--- Категории ---"""
cat_type = {
    'category': Category,
    'subcategory': SubCategory,
}


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
@admin.route('/create_category/<cat_id>', methods=['GET', 'POST'])
def create_category(cat_id=None):
    if not isLogged():
        return redirect(url_for('admin.login'))
    """Функция создает категорию. Если передан аргумент cat_id, то создается подкатегория"""
    form = CategoryForm()
    product_service = ProductService(db)

    if form.validate_on_submit():
        if not cat_id:
            ok = product_service.create_category(form=form, object=Category)
            if not ok:
                flash("Категория с указанным именем уже существует!", category="danger")
                return render_template(
                    'admin/category_form.html',
                    form=form,
                )
            flash("Категория создана!", category="success")
        else:
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
        filename = secure_filename(file.filename)
        filepath = create_path_for_file(current_app, 'catalog', filename)
        file.save(filepath)
        flash('Фото успешно загружено!', category="success")

        return redirect(url_for('admin.products'))

    title = "Добавить категорию" if not cat_id else "Добавить подкатегорию"
    return render_template(
        'admin/category_form.html',
        form=form,
        title=title
    )

@admin.route('/edit_category/<cat_slug>', methods=['GET', 'POST'])
def edit_category(cat_slug):
    product_service = ProductService(db)
    is_subcategory = request.args.get('is_subcategory')
    if not is_subcategory:
        category = product_service.get_category_by_slug(cat_slug=cat_slug)
        title = "Редактировать категорию"
    else:
        category = product_service.get_subcategory_by_slug(slug=cat_slug)
        title = "Редактировать подкатегорию"
    form = CategoryEditForm(obj=category)

    if form.validate_on_submit():
        product_service.edit_category(form=form, category=category)
        # Если загружено новое фото, сохраняем его
        if form.picture.data:
            file = form.picture.data
            filename = secure_filename(file.filename)
            filepath = create_path_for_file(current_app, 'catalog', filename)
            file.save(filepath)
            flash('Фото успешно обновлено!', category="success")

        return redirect(url_for('admin.products'))

    # Предзаполним текущие значения
    return render_template(
        'admin/category_form.html',
        form=form,
        title=title
    )


@admin.route('/delete_category/<int:cat_id>', methods=['POST'])
def delete_category(cat_id):
    product_service = ProductService(db)
    is_subcategory = request.args.get('is_subcategory')
    object = Category if not is_subcategory else SubCategory

    # Удаляем запись в БД и получаем название фото
    file_name = product_service.delete_category(cat_id=cat_id, object=object)

    # Проверяем, есть ли товары в категории
    if not file_name:
        return redirect(url_for('admin.products'))

    # Удаляем фото
    file_path = create_path_for_file(current_app, 'catalog', file_name)
    try:
        os.remove(file_path)
    except FileNotFoundError:
        flash("Не удается найти указанный файл", category="error")

    return redirect(url_for('admin.products'))


@admin.route('/create_product/<int:cat_id>/<int:subcat_id>', methods=['GET', 'POST'])
def create_product(cat_id, subcat_id):
    """Функция создает товар"""
    form = ProductForm()
    product_service = ProductService(db)

    if form.validate_on_submit():
        # Проверяем уникальность наименования товара
        ok = product_service.create_product(form=form, cat_id=cat_id, subcat_id=subcat_id)
        if not ok:
            flash("Товар с указанным именем уже существует!", category="danger")
            return render_template(
                'admin/product_form.html',
                form=form,
            )

        # Сохраняем фото на диск
        file = form.picture.data
        filename = secure_filename(file.filename)
        filepath = create_path_for_file(current_app, 'catalog', filename)
        file.save(filepath)
        flash('Фото успешно загружено!', category="success")

        flash("Товар создан!", category="success")
        return redirect(url_for('admin.products'))

    return render_template(
        'admin/product_form.html',
        form=form,
        title="Добавить товар"
    )

@admin.route('/edit_product/<product_slug>', methods=['GET', 'POST'])
def edit_product(product_slug):
    """Функция редактирует товар"""
    product_service = ProductService(db)

    product = product_service.get_product_by_slug(product_slug=product_slug)
    form = ProductEditForm(obj=product)

    if form.validate_on_submit():
        product_service.edit_product(form=form, product=product)
        # Если загружено новое фото, сохраняем его
        if form.picture.data:
            file = form.picture.data
            filename = secure_filename(file.filename)
            filepath = create_path_for_file(current_app, 'catalog', filename)
            file.save(filepath)
            flash('Фото успешно обновлено!', category="success")

        return redirect(url_for('admin.products'))

    # Предзаполним текущие значения
    return render_template(
        'admin/product_form.html',
        form=form,
        title="Редактировать товар"
    )

@admin.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product_service = ProductService(db)

    # Удаляем запись в БД и получаем название фото
    file_name = product_service.delete_product(product_id=product_id)

    # Удаляем фото
    file_path = create_path_for_file(current_app, 'catalog', file_name)
    try:
        os.remove(file_path)
    except FileNotFoundError:
        flash("Не удается найти указанный файл", category="error")

    return redirect(url_for('admin.products'))


@admin.route('/dashboard')
def orders():
    return 'orders'


