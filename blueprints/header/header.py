from flask import (Blueprint, request, redirect, url_for, flash,
                   render_template, make_response, session)
from flask_login import (login_user, login_required,
                         logout_user, current_user)
from werkzeug.security import check_password_hash

from extensions import db
from forms import RegisterForm, LoginForm, EditProfileForm
from services import (UserService, ProductService, transfer_guest_cart_to_user,
                      transfer_guest_favorite_to_user, CartService)
from services.UserLogin import UserLogin


header = Blueprint(
    'header',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/header_static',
)


@header.route('/')
def index():
    product_service = ProductService(db)
    cart_service = CartService(db)
    random_products = product_service.get_random_products()

    cart_len = len(cart_service.get_cart_items(user_id=current_user.get_id()))
    return render_template(
        "header/base.html",
        random_products=random_products,
        cart_len=cart_len
    )

@header.route('/register', methods=['GET', 'POST'])
def register():
    user_service = UserService(db)
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = user_service.user_register(form=form)
        if new_user:
            user_login = UserLogin().create(new_user)
            login_user(user_login, remember=False)
            # Перенос корзины гостя из сессии в БД
            transfer_guest_cart_to_user(db, user_id=user_login.get_id(), session=session)
            # Перенос избранного гостя из сессии в БД
            transfer_guest_favorite_to_user(db, user_id=user_login.get_id(), session=session)
            # Перенаправляем пользователя на страницу, с которой он перешел,
            # либо на страницу его профиля
            return redirect(request.args.get('next') or url_for('header.index'))
    return render_template("header/register.html", form=form)

@header.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('header.profile'))
    user_service = UserService(db)
    form = LoginForm()
    login_type = form.login_type.data or 'email'

    if form.validate_on_submit():
        user = user_service.get_user(form=form)
        if user and check_password_hash(user.psw, form.psw.data):
            user_login = UserLogin().create(user)
            rm = form.remember.data
            login_user(user_login, remember=rm)
            # Перенос корзины гостя из сессии в БД
            transfer_guest_cart_to_user(db, user_id=user_login.get_id(), session=session)
            # Перенос избранного гостя из сессии в БД
            transfer_guest_favorite_to_user(db, user_id=user_login.get_id(), session=session)
            # Перенаправляем пользователя на страницу, с которой он перешел,
            # либо на страницу его профиля
            return redirect(request.args.get('next') or url_for('header.profile'))
        flash("Неверный логин и/или пароль", category="error")
    return render_template(
        "header/login.html",
        form=form,
        login_type=login_type
    )

@header.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", category="success")
    return redirect(url_for('header.login'))

@header.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_service = UserService(db)
    edit_mode = False

    if request.method == "POST":
        if request.form.get('edit_mode'): # Переход в режим редактирования
            edit_mode = True
            form = EditProfileForm(data={
                'surname': current_user.getSurname(),
                'name': current_user.getName(),
                'email': current_user.getEmail(),
                'phone': current_user.getPhone(),
            })
        else: # Сохранение данных
            form = EditProfileForm()
            if form.validate_on_submit():
                is_updated = user_service.edit_profile(user_id=current_user.get_id(), form=form)
                if is_updated:
                    return redirect(url_for('header.profile'))
            edit_mode = True # Оставаться в режиме редактирования, если ошибки
    else:
        form = EditProfileForm(obj=current_user)

    return render_template(
        "header/profile.html",
        form=form,
        edit_mode=edit_mode,
        user=current_user,
    )

@header.route('/userava')
@login_required
def userava():
    """Функция отображения аватарки пользователя"""
    img = current_user.getAvatar(header)
    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = "image/png"
    return h

@header.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Функция загрузки установленного аватара в БД"""
    if request.method == 'POST':
        file = request.files.get('file')
        if file and current_user.verifyExt(file.filename):
            try:
                user_service = UserService(db)
                img = file.read()
                result = user_service.update_avatar(user_id = current_user.get_id(), avatar = img)
                if result:
                    flash("Аватар обновлен", category="success")
                else:
                    flash("Ошибка обновления аватара", category="error")
            except FileNotFoundError:
                flash("Ошибка чтения файла", category="error")
        else:
            flash("Файл не выбран или неверный формат (правильный формат .png)", category="error")

    return redirect(url_for('header.profile'))

@header.route('search')
def search():
    product_service = ProductService(db)
    query = request.args.get('q', '').strip()
    if not query:
        return render_template('header/search.html', products=[])
    products = product_service.product_search(string=query)
    return render_template(
        'header/search.html',
        products=products,
        query=query
    )