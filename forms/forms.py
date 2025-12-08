from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired, MultipleFileField
from wtforms import (StringField, SubmitField, BooleanField, PasswordField, FileField,
                     DecimalField, IntegerField, TelField, RadioField, EmailField)
from wtforms.fields.simple import TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, Regexp, ValidationError


class RegisterForm(FlaskForm):
    surname = StringField("Фамилия: ", validators=[DataRequired(), Length(min=3, max=20)])
    name = StringField("Имя: ", validators=[DataRequired(), Length(min=2, max=20)])
    email = EmailField("Email: ", validators=[Email("Некорректный email")])
    phone = TelField('Телефон:',
                     validators=[
        Optional(),
        Regexp(r'^\+?\d{11}$', message='Введите корректный номер телефона'),
                    ])
    psw = PasswordField("Пароль: ", validators=[DataRequired(), Length(min=6, max=20)])
    psw2 = PasswordField(
        "Повтор пароля: ",
        validators=[DataRequired(),
        EqualTo("psw", message="Пароли не совпадают")]
    )
    submit = SubmitField("Регистрация")


class LoginForm(FlaskForm):
    login_type = RadioField(
        'Тип входа',
        choices=[('email', 'Email'), ('phone', 'Телефон')],
        default='email'
    )
    email = StringField("Email: ", validators=[Optional(), Email("Некорректный email")])
    phone = TelField('Телефон:',
                     validators=[
                         Optional(),
                         Regexp(r'^\+?\d{11}$', message='Введите корректный номер телефона'),
                     ]
                     )
    psw = PasswordField("Пароль: ", validators=[DataRequired(), Length(min=6, max=20)])
    remember = BooleanField("Запомнить", default=False)
    submit = SubmitField("Войти")


class EditProfileForm(FlaskForm):
    surname = StringField("Фамилия: ", validators=[DataRequired(), Length(min=3, max=20)])
    name = StringField("Имя: ", validators=[DataRequired(), Length(min=2, max=20)])
    email = EmailField("Email: ", validators=[Email("Некорректный email")])
    phone = TelField('Телефон:',
                     validators=[
                         DataRequired(),
                         Regexp(r'^\+?\d{11}$', message='Введите корректный номер телефона'),
                     ])


class CategoryForm(FlaskForm):
    """Форма для создания категории/подкатегории"""
    name = StringField("Наименование категории: ", validators=[
        DataRequired(),
        Length(min=5, max=50)
    ])
    picture = FileField("Загрузите фото", validators=[
        FileRequired(message='Выберите файл!'),
        FileAllowed(['png', 'jpg', 'jpeg'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')


class CategoryEditForm(FlaskForm):
    """Форма для редактирования категории/подкатегории"""
    name = StringField("Наименование категории: ", validators=[
        DataRequired(),
        Length(min=5, max=50)
    ])
    picture = FileField("Загрузите фото", validators=[
        FileAllowed(['png', 'jpg', 'jpeg'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')


class ProductForm(FlaskForm):
    name = StringField("Наименование Товара: ", validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField("Описание товара: ", validators=[
        DataRequired(),
        Length(min=10, max=1000)
    ])
    main_image = FileField("Главное фото", validators=[
        FileRequired(message='Выберите файл!'),
        FileAllowed(['png', 'jpg', 'jpeg'], 'Только изображения!')
    ])
    extra_images = MultipleFileField("Дополнительные фото", validators=[
        FileAllowed(['png', 'jpg', 'jpeg'], 'Только изображения!')
    ])
    price = DecimalField(
        "Стоимость товара",
        places=2,
        validators=[DataRequired(), NumberRange(min=0)],
    )
    stock_quantity = IntegerField(
        "Остаток на складе",
        default=0,
        validators=[NumberRange(min=0)]
    )
    sku = IntegerField(
        "Артикул",
        validators=[Optional(),
                    NumberRange(min=1, message="Артикул должен быть положительным числом")],
        render_kw={'placeholder': "Необязательно"},
    )
    weight = DecimalField(
        "Масса товара, кг",
        places=3,
        validators=[Optional(),
                    NumberRange(min=0, message="Масса должна быть положительным числом")],
        render_kw={'placeholder': "Необязательно"}
    )


class ProductEditForm(FlaskForm):
    """Форма для редактирования продукта (отличается необязательностью наличия фото)"""
    name = StringField("Наименование Товара: ", validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField("Описание товара: ", validators=[
        DataRequired(),
        Length(min=10, max=1000)
    ])
    main_image = FileField("Главное фото", validators=[
        FileAllowed(['png', 'jpg', 'jpeg'], 'Только изображения!')
    ])
    extra_images = MultipleFileField("Дополнительные фото", validators=[
        FileAllowed(['png', 'jpg', 'jpeg'], 'Только изображения!')
    ])
    price = DecimalField(
        "Стоимость товара",
        places=2,
        validators=[DataRequired(), NumberRange(min=0)]
    )
    stock_quantity = IntegerField("Остаток на складе", validators=[NumberRange(min=0)])
    sku = IntegerField(
        "Артикул (необязательно)",
        validators=[Optional(),
                    NumberRange(min=1, message="Артикул должен быть положительным числом")],
    )
    weight = DecimalField(
        "Масса товара, кг (необязательно)",
        places=3,
        validators=[Optional(),
                    NumberRange(min=0, message="Масса должна быть положительным числом")],
    )

class OrderForm(FlaskForm):
    """Форма для создания заказа"""
    phone = TelField('Телефон:',
                     validators=[
                         DataRequired(),
                         Regexp(r'^\+?\d{11}$', message='Введите корректный номер телефона'),
                     ])
    email = EmailField('E-mail:', validators=[
        Optional(),
        Email(message="Некорректный email")
    ])
    payment_method = RadioField('Способ оплаты', choices=[
        ('Онлайн', 'Онлайн'),
        ('При получении', 'При получении')
    ], default='online', validators=[DataRequired()])
    delivery_method = RadioField('Способ получения', choices=[
        ('Самовывоз', 'Самовывоз'),
        ('Доставка', 'Доставка')
    ], default='self_pickup', validators=[DataRequired()])
    shipping_address = StringField('Адрес доставки', validators=[Optional()])
    comment = TextAreaField("Комментарий: ", validators=[
        Optional(),
        Length(max=100)
        ])
    total_amount = HiddenField()
    submit = SubmitField('Оформить заказ')

    def validate_address(self, field):
        if self.delivery_method.data == 'delivery' and not field.data.strip():
            raise ValidationError("Адрес обязателен для доставки")