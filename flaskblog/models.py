from datetime import datetime
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask import current_app
from flaskblog import db, login_manager
from flask_login import UserMixin, current_user
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from slugify import slugify
import json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == 'Andriy'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', lazy=True, cascade="all, delete-orphan")

    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=1800)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"
    
    def __str__(self):
        return f"{self.id}. {self.username}"
    
class UserView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == 'Andriy'
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")
    slug = db.Column(db.String(100), unique=True, nullable=False)
    video_links = db.Column(db.Text, nullable=True)

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        if not self.slug:
            self.slug = slugify(self.title)

    def set_video_links(self, links):
        self.video_links = json.dumps(links)

    def get_video_links(self):
        if self.video_links:
            return json.loads(self.video_links)
        return []

    def __repr__(self):
        return f"User('{self.title}', '{self.date_posted}')"


class PostView(ModelView):
    form_columns = ['title', 'content', 'user_id', 'video_links']
    column_list = ['title', 'author']

    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == 'Andriy'


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(250), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', on_delete="CASCADE"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', on_delete="CASCADE"), nullable=False)

class CommentView(ModelView):
    form_columns = ['text', 'date_posted', 'user_id', 'post_id']
    column_list = ['id', 'text', 'date_posted', 'user_id', 'post_id']


    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == 'Andriy'
    
class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)

class UpdateView(ModelView):
    form_columns = ['title', 'content']
    column_list = ['title', 'date_posted']

    column_default_sort = ('date_posted', True)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == 'Andriy'
    
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)

class AnnouncementView(ModelView):
    form_columns = ['title', 'content']
    column_list = ['title', 'date_posted']

    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == 'Andriy'