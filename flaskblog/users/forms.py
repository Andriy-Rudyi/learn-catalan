from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_login import current_user
from flaskblog.i18n import gettext as _, lazy_gettext as _l
from flaskblog.models import User
from flaskblog.permissions import admin_username, is_admin


class RegistrationForm(FlaskForm):
    username = StringField(_l('Ім’я користувача'),
                            validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField(_l('Email'), 
                        validators=[DataRequired(), Email()])
    password = PasswordField(_l('Пароль'), validators=[DataRequired()])
    confirm_password = PasswordField(_l('Підтвердіть пароль'), 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Зареєструватися'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(_('Це ім’я вже зайняте. Оберіть інше.'))
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(_('Цей email уже зареєстровано. Оберіть інший.'))
    

class LoginForm(FlaskForm):
    email = StringField(_l('Email'), 
                        validators=[DataRequired(), Email()])
    password = PasswordField(_l('Пароль'), validators=[DataRequired()])
    remember = BooleanField(_l('Запам’ятати мене'))
    submit = SubmitField(_l('Увійти'))


class UpdateAccountForm(FlaskForm):
    username = StringField(_l('Ім’я користувача'),
                            validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField(_l('Email'), 
                        validators=[DataRequired(), Email()])
    picture = FileField(_l('Оновити фото профілю'), validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField(_l('Оновити'))

    def validate_username(self, username):
        if username.data != current_user.username:
            # Editing rights go with the editor's username: the editor keeps it,
            # and nobody else can take it, even when it is free.
            if is_admin():
                raise ValidationError(_('Ім’я редактора сайту змінити не можна.'))
            if username.data.strip().lower() == admin_username().lower():
                raise ValidationError(_('Це ім’я вже зайняте. Оберіть інше.'))
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(_('Це ім’я вже зайняте. Оберіть інше.'))
    
    def validate_email(self, email):
        if email.data != current_user.email:
            email = User.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError(_('Цей email уже зареєстровано. Оберіть інший.'))
            

class RequestResetForm(FlaskForm):
    email = StringField(_l('Email'), 
                        validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Скинути пароль'))

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email is None:
            raise ValidationError(_('Акаунта з таким email немає. Спершу зареєструйтеся.'))
        

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Пароль'), validators=[DataRequired()])
    confirm_password = PasswordField(_l('Підтвердіть пароль'), 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Змінити пароль'))