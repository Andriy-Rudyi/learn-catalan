from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from flaskblog import bcrypt, db
from flaskblog.i18n import gettext as _
from flaskblog.models import Post, User
from flaskblog.users.forms import (LoginForm, RegistrationForm,
                                   RequestResetForm, ResetPasswordForm,
                                   UpdateAccountForm)
from flaskblog.users.utils import save_picture, send_reset_email
from flaskblog.vocabulary.service import user_word_counts

users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(_('Акаунт створено! Тепер можна увійти.'), 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title=_('Реєстрація'), form=form)


@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash(_('Не вдалося увійти. Перевірте email і пароль.'), 'danger')
    return render_template('login.html', title=_('Вхід'), form=form)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash(_('Акаунт оновлено!'), 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for(
        'static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title=_('Моя сторінка'),
                           image_file=image_file, form=form,
                           counts=user_word_counts(current_user.id))


@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    # posts = Post.query.filter_by(author=user)\
    #     .order_by(Post.date_posted.desc())\
    #     .paginate(page=page, per_page=5)
    posts = Post.query.filter_by(author=user)\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash(_('Ми надіслали лист з інструкцією, як змінити пароль.'), 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title=_('Зміна пароля'), form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash(_('Посилання недійсне або застаріло.'), 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(_('Пароль змінено! Тепер можна увійти.'), 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title=_('Зміна пароля'), form=form)
