from datetime import datetime
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask import current_app
from flaskblog import db, login_manager
from flaskblog.permissions import is_admin
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
    saved_words = db.relationship('UserWord', backref='owner', lazy=True, cascade="all, delete-orphan")

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete="CASCADE"), nullable=False)

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

class Word(db.Model):
    """An entry of the shared Catalan-Ukrainian dictionary."""

    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(100), nullable=False, index=True)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    translation = db.Column(db.String(255), nullable=False)
    part_of_speech = db.Column(db.String(20), nullable=True, index=True)
    gender = db.Column(db.String(10), nullable=True)
    pronunciation = db.Column(db.String(100), nullable=True)
    topic = db.Column(db.String(50), nullable=True, index=True)
    level = db.Column(db.String(5), nullable=True, index=True)
    example_ca = db.Column(db.String(255), nullable=True)
    example_uk = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    added_by = db.relationship('User', backref='added_words')
    saved_by = db.relationship(
        'UserWord', backref='word', lazy=True, cascade="all, delete-orphan"
    )

    def __init__(self, *args, **kwargs):
        super(Word, self).__init__(*args, **kwargs)
        if not self.slug and self.term:
            self.slug = slugify(self.term)

    @property
    def is_verb(self):
        return self.part_of_speech == 'verb'

    def __repr__(self):
        return f"Word('{self.term}', '{self.translation}')"

    def __str__(self):
        return f"{self.term} — {self.translation}"


class UserWord(db.Model):
    """A word in someone's personal dictionary.

    Either a word saved from the shared dictionary (``word_id``) or one
    the user typed in themselves (``term`` and ``translation``).
    """

    STATUS_LEARNING = 'learning'
    STATUS_KNOWN = 'known'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False, index=True
    )
    word_id = db.Column(
        db.Integer, db.ForeignKey('word.id'), nullable=True, index=True
    )
    term = db.Column(db.String(100), nullable=True)
    translation = db.Column(db.String(255), nullable=True)
    note = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(10), nullable=False, default=STATUS_LEARNING)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'word_id', name='uq_user_word'),
    )

    @property
    def display_term(self):
        return self.word.term if self.word else self.term

    @property
    def display_translation(self):
        if self.translation:
            return self.translation
        return self.word.translation if self.word else ''

    @property
    def is_known(self):
        return self.status == self.STATUS_KNOWN

    def __repr__(self):
        return f"UserWord('{self.display_term}', '{self.status}')"


class WordView(ModelView):
    form_columns = [
        'term', 'translation', 'part_of_speech', 'gender', 'pronunciation',
        'topic', 'level', 'example_ca', 'example_uk', 'notes',
    ]
    column_list = ['term', 'translation', 'part_of_speech', 'topic', 'level']
    column_searchable_list = ['term', 'translation']
    column_filters = ['part_of_speech', 'topic', 'level']
    column_default_sort = 'term'

    def is_accessible(self):
        return is_admin()

    def on_model_change(self, form, model, is_created):
        if not model.slug and model.term:
            model.slug = slugify(model.term)


class UserWordView(ModelView):
    column_list = ['id', 'user_id', 'word_id', 'term', 'translation', 'status']
    column_filters = ['status']

    def is_accessible(self):
        return is_admin()


class GrammarUnit(db.Model):
    """One unit of the grammar course.

    Modelled on the layout of Raymond Murphy's grammar books: a short
    explanation with examples, then exercises whose answers the learner
    can check. Examples and exercises are kept as JSON, the way Post
    keeps its video links.
    """

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False, index=True)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    section = db.Column(db.String(80), nullable=False, index=True)
    level = db.Column(db.String(5), nullable=True, index=True)
    summary = db.Column(db.String(300), nullable=True)
    explanation = db.Column(db.Text, nullable=False)
    examples = db.Column(db.Text, nullable=True)
    exercises = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super(GrammarUnit, self).__init__(*args, **kwargs)
        if not self.slug and self.title:
            self.slug = slugify(self.title)

    # -- examples: [{"ca": ..., "uk": ..., "note": ...}] ----------------
    def get_examples(self):
        return json.loads(self.examples) if self.examples else []

    def set_examples(self, examples):
        self.examples = json.dumps(examples, ensure_ascii=False)

    # -- exercises: [{"instruction": ..., "items": [{"q": ..., "a": ...}]}]
    def get_exercises(self):
        return json.loads(self.exercises) if self.exercises else []

    def set_exercises(self, exercises):
        self.exercises = json.dumps(exercises, ensure_ascii=False)

    @property
    def exercise_count(self):
        return sum(len(block.get('items', [])) for block in self.get_exercises())

    def __repr__(self):
        return f"GrammarUnit({self.number}, '{self.title}')"

    def __str__(self):
        return f"{self.number}. {self.title}"


class GrammarUnitView(ModelView):
    form_columns = [
        'number', 'title', 'section', 'level', 'summary', 'explanation',
        'examples', 'exercises',
    ]
    column_list = ['number', 'title', 'section', 'level']
    column_searchable_list = ['title', 'section']
    column_filters = ['section', 'level']
    column_default_sort = 'number'

    def is_accessible(self):
        return is_admin()

    def on_model_change(self, form, model, is_created):
        if not model.slug and model.title:
            model.slug = slugify(model.title)
