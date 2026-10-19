from datetime import datetime
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask import current_app
from flaskblog import db, login_manager
from flaskblog.i18n import content_language, get_locale, gettext
from flaskblog.languages import CODES as LANGUAGE_CODES, fallback_chain
from flaskblog.permissions import is_admin
from flask_login import UserMixin
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from slugify import slugify
from sqlalchemy.orm import attribute_keyed_dict, declared_attr
import json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return is_admin()

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
        return is_admin()
    
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
        return is_admin()


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
        return is_admin()
    
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
        return is_admin()
    
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)

class AnnouncementView(ModelView):
    form_columns = ['title', 'content']
    column_list = ['title', 'date_posted']

    def is_accessible(self):
        return is_admin()

class Word(db.Model):
    """A Catalan entry of the shared dictionary.

    Everything about the Catalan word lives here; its translation, example
    and notes in each language are WordTranslation rows (``word.translations``
    is a dict by language code). ``translation``, ``example_uk``, ``notes``
    and the ``*_en`` attributes read and write the Ukrainian and English rows,
    as the columns of the same names did before.
    """

    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(100), nullable=False, index=True)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    part_of_speech = db.Column(db.String(20), nullable=True, index=True)
    gender = db.Column(db.String(10), nullable=True)
    pronunciation = db.Column(db.String(100), nullable=True)
    topic = db.Column(db.String(50), nullable=True, index=True)
    level = db.Column(db.String(5), nullable=True, index=True)
    example_ca = db.Column(db.String(255), nullable=True)
    # Not used in Central Catalan: comma-separated codes from
    # flaskblog.vocabulary.varieties ("valencian,balearic"), and where the mark
    # comes from ("review", "wiktionary-en", "wiktionary-ca", "manual").
    variety = db.Column(db.String(80), nullable=True, index=True)
    variety_source = db.Column(db.String(20), nullable=True)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    added_by = db.relationship('User', backref='added_words')
    saved_by = db.relationship(
        'UserWord', backref='word', lazy=True, cascade="all, delete-orphan"
    )
    # {'uk': WordTranslation, 'en': ...}; loaded together with lists of words.
    translations = db.relationship(
        'WordTranslation', back_populates='word', lazy='selectin',
        cascade='all, delete-orphan',
        collection_class=attribute_keyed_dict('lang'),
    )
    # Its meanings, in order (flaskblog/vocabulary/senses.py).
    senses = db.relationship(
        'WordSense', back_populates='word', lazy='selectin',
        cascade='all, delete-orphan', order_by='WordSense.position',
    )

    def __init__(self, *args, **kwargs):
        super(Word, self).__init__(*args, **kwargs)
        if not self.slug and self.term:
            self.slug = slugify(self.term)

    @property
    def is_verb(self):
        return self.part_of_speech == 'verb'

    # -- translations ------------------------------------------------------
    def translation_in(self, lang, fallback=True):
        """The WordTranslation for *lang*, or for the first fallback that has one."""
        chain = fallback_chain(lang) if fallback else [lang]
        for code in chain:
            entry = self.translations.get(code)
            if entry is not None and entry.translation:
                return entry
        return None

    def _get(self, lang, field):
        entry = self.translations.get(lang)
        return getattr(entry, field) if entry is not None else None

    def _set(self, lang, field, value):
        value = value or None
        entry = self.translations.get(lang)
        if entry is None:
            if value is None:
                return
            entry = self.translations[lang] = WordTranslation(lang=lang, translation='')
        setattr(entry, field, value if field != 'translation' else (value or ''))
        if not (entry.translation or entry.example or entry.notes):
            del self.translations[lang]

    def set_translation(self, lang, translation=None, example=None, notes=None):
        self._set(lang, 'translation', translation)
        self._set(lang, 'example', example)
        self._set(lang, 'notes', notes)

    @property
    def languages(self):
        """Codes of the languages this word is translated into."""
        return [code for code in LANGUAGE_CODES if self._get(code, 'translation')]

    # The Ukrainian and English rows under their former column names.
    translation = property(lambda self: self._get('uk', 'translation'),
                           lambda self, value: self._set('uk', 'translation', value))
    example_uk = property(lambda self: self._get('uk', 'example'),
                          lambda self, value: self._set('uk', 'example', value))
    notes = property(lambda self: self._get('uk', 'notes'),
                     lambda self, value: self._set('uk', 'notes', value))
    translation_en = property(lambda self: self._get('en', 'translation'),
                              lambda self, value: self._set('en', 'translation', value))
    example_en = property(lambda self: self._get('en', 'example'),
                          lambda self, value: self._set('en', 'example', value))
    notes_en = property(lambda self: self._get('en', 'notes'),
                        lambda self, value: self._set('en', 'notes', value))

    @property
    def variety_codes(self):
        from flaskblog.vocabulary.varieties import parse_codes
        return parse_codes(self.variety)

    @property
    def is_central(self):
        return not self.variety_codes

    @property
    def central_alternative(self):
        """What Central Catalan says instead, from data/varieties.json."""
        from flaskblog.vocabulary import varieties
        return (varieties.load().get(self.term) or {}).get('central')

    # -- text in the interface language, or the nearest one there is ----------
    def t_translation(self):
        entry = self.translation_in(get_locale())
        return entry.translation if entry else ''

    def t_example(self):
        entry = self.translation_in(get_locale())
        return entry.example if entry else None

    def t_notes(self):
        entry = self.translation_in(get_locale())
        return entry.notes if entry else None

    def __repr__(self):
        return f"Word('{self.term}', '{self.translation}')"

    def __str__(self):
        return f"{self.term}: {self.translation}"


class WordTranslation(db.Model):
    """A dictionary word in one language: translation, example and notes."""

    __tablename__ = 'word_translation'
    __table_args__ = (
        db.UniqueConstraint('word_id', 'lang', name='uq_word_translation_lang'),
    )

    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(
        db.Integer, db.ForeignKey('word.id', ondelete='CASCADE'), nullable=False, index=True
    )
    lang = db.Column(db.String(10), nullable=False, index=True)
    translation = db.Column(db.String(255), nullable=False, default='')
    example = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    # False for a draft (e.g. a machine translation) nobody has checked yet.
    reviewed = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    # Changed on the site (editor, translation platform, CSV upload): the
    # bundled files no longer overwrite it on deploy.
    edited = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())

    word = db.relationship('Word', back_populates='translations')

    def __repr__(self):
        return f"WordTranslation({self.lang!r}, {self.translation!r})"

    def __str__(self):
        return f"{self.lang}: {self.translation}"


class WordSense(db.Model):
    """One meaning of a dictionary word ("tocar": 1. touch, 2. play).

    Translations are attached to meanings: ``sense.translations`` is a dict
    by language code. The meanings of a word follow its English translation
    (the pivot language); WordTranslation.translation keeps every
    language's meanings joined with ";" (flaskblog/vocabulary/senses.py
    keeps the two in step).
    """

    __tablename__ = 'word_sense'

    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(
        db.Integer, db.ForeignKey('word.id', ondelete='CASCADE'), nullable=False, index=True
    )
    position = db.Column(db.Integer, nullable=False, default=1)

    word = db.relationship('Word', back_populates='senses')
    translations = db.relationship(
        'SenseTranslation', back_populates='sense', lazy='selectin',
        cascade='all, delete-orphan',
        collection_class=attribute_keyed_dict('lang'),
    )

    def text_in(self, lang, fallback=True):
        """The SenseTranslation for *lang*, or for the first fallback that has one."""
        for code in (fallback_chain(lang) if fallback else [lang]):
            entry = self.translations.get(code)
            if entry is not None and entry.text:
                return entry
        return None

    def __repr__(self):
        return f"WordSense({self.word_id!r}, {self.position!r})"


class SenseTranslation(db.Model):
    """A meaning of a word in one language."""

    __tablename__ = 'sense_translation'
    __table_args__ = (
        db.UniqueConstraint('sense_id', 'lang', name='uq_sense_translation_lang'),
    )

    id = db.Column(db.Integer, primary_key=True)
    sense_id = db.Column(
        db.Integer, db.ForeignKey('word_sense.id', ondelete='CASCADE'), nullable=False, index=True
    )
    lang = db.Column(db.String(10), nullable=False, index=True)
    text = db.Column(db.String(255), nullable=False, default='')
    reviewed = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())

    sense = db.relationship('WordSense', back_populates='translations')

    def __repr__(self):
        return f"SenseTranslation({self.lang!r}, {self.text!r})"


class Translator(db.Model):
    """Someone who may translate and review one language on /translate
    (``lang`` '*' for all of them). Granted in the admin panel."""

    __tablename__ = 'translator'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'lang', name='uq_translator_lang'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True
    )
    lang = db.Column(db.String(10), nullable=False)

    user = db.relationship(
        'User', backref=db.backref('translator_roles', cascade='all, delete-orphan')
    )

    def __str__(self):
        return f"{self.user.username if self.user else self.user_id}: {self.lang}"


class UiTranslation(db.Model):
    """An interface string translated on /translate. It overrides the
    catalogue in flaskblog/i18n (``flask translations export`` writes it
    back there)."""

    __tablename__ = 'ui_translation'
    __table_args__ = (
        db.UniqueConstraint('lang', 'key', name='uq_ui_translation_key'),
    )

    id = db.Column(db.Integer, primary_key=True)
    lang = db.Column(db.String(10), nullable=False, index=True)
    # sha1 of the source (Ukrainian) string, which can be long.
    key = db.Column(db.String(40), nullable=False)
    source = db.Column(db.Text, nullable=False)
    text = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)


class TranslationMemory(db.Model):
    """A sentence and its translation for the translator (/translator):
    proposed by someone on the site, used once a translator of the language
    approves it (or straight away when they wrote it themselves). The
    sentences bundled with the course need no rows: they are read from the
    data files."""

    __tablename__ = 'translation_memory'

    PENDING, APPROVED, REJECTED = 'pending', 'approved', 'rejected'

    id = db.Column(db.Integer, primary_key=True)
    source_lang = db.Column(db.String(10), nullable=False)
    target_lang = db.Column(db.String(10), nullable=False)
    # sha1 of the normalised source sentence, to find it again.
    source_key = db.Column(db.String(40), nullable=False, index=True)
    source_text = db.Column(db.Text, nullable=False)
    target_text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), nullable=False, default=PENDING, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    decided_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)

    author = db.relationship('User', foreign_keys=[created_by])


class _TranslationTarget(object):
    """What a suggestion or a change is about: a meaning of a word
    (``kind`` 'sense'), the word's example or notes in a language
    ('example', 'notes'), or an interface string ('ui')."""

    lang = db.Column(db.String(10), nullable=False, index=True)
    kind = db.Column(db.String(10), nullable=False)

    @declared_attr
    def sense_id(cls):
        return db.Column(db.Integer, db.ForeignKey('word_sense.id', ondelete='CASCADE'),
                         nullable=True, index=True)

    @declared_attr
    def word_id(cls):
        return db.Column(db.Integer, db.ForeignKey('word.id', ondelete='CASCADE'),
                         nullable=True, index=True)

    ui_key = db.Column(db.String(40), nullable=True, index=True)
    ui_source = db.Column(db.Text, nullable=True)

    @declared_attr
    def user_id(cls):
        return db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    @declared_attr
    def sense(cls):
        return db.relationship('WordSense')

    @declared_attr
    def word(cls):
        return db.relationship('Word')

    @declared_attr
    def user(cls):
        return db.relationship('User', foreign_keys='{}.user_id'.format(cls.__name__))


class TranslationSuggestion(_TranslationTarget, db.Model):
    """A translation someone without translator rights proposes; a
    translator of the language accepts or rejects it."""

    __tablename__ = 'translation_suggestion'

    OPEN, ACCEPTED, REJECTED = 'open', 'accepted', 'rejected'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), nullable=False, default=OPEN, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    decided_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)


class TranslationChange(_TranslationTarget, db.Model):
    """History of /translate: every save, review, accepted suggestion and
    revert, with the text before and after, so any of them can be undone."""

    __tablename__ = 'translation_change'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(10), nullable=False)  # edit, review, accept, revert
    old_text = db.Column(db.Text, nullable=True)
    new_text = db.Column(db.Text, nullable=True)
    old_reviewed = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


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
        return self.word.t_translation() if self.word else ''

    @property
    def is_known(self):
        return self.status == self.STATUS_KNOWN

    def __repr__(self):
        return f"UserWord('{self.display_term}', '{self.status}')"


class WordView(ModelView):
    form_columns = [
        'term', 'part_of_speech', 'gender', 'pronunciation',
        'topic', 'level', 'example_ca', 'variety', 'variety_source',
    ]
    column_list = ['term', 'translation', 'translation_en', 'languages', 'part_of_speech', 'topic', 'level']
    column_searchable_list = ['term']
    column_filters = ['part_of_speech', 'topic', 'level', 'variety']
    column_default_sort = 'term'

    def is_accessible(self):
        return is_admin()

    def on_model_change(self, form, model, is_created):
        if not model.slug and model.term:
            model.slug = slugify(model.term)


class WordTranslationView(ModelView):
    """Translations of dictionary words, one row per language: add French,
    Polish... here (or in bulk with a CSV file)."""

    column_list = ['word', 'lang', 'translation', 'example', 'reviewed']
    column_filters = ['lang', 'reviewed']
    column_editable_list = ['reviewed']
    column_searchable_list = ['translation', 'word.term']
    column_default_sort = 'word_id'
    form_columns = ['word', 'lang', 'translation', 'example', 'notes', 'reviewed']
    form_ajax_refs = {'word': {'fields': ['term'], 'page_size': 20}}
    form_choices = {'lang': [(code, code) for code in LANGUAGE_CODES]}

    def is_accessible(self):
        return is_admin()

    def on_model_change(self, form, model, is_created):
        model.edited = True

    def after_model_change(self, form, model, is_created):
        self._resync(model.word_id, model.lang, model.reviewed)

    def after_model_delete(self, model):
        self._resync(model.word_id, model.lang)

    def _resync(self, word_id, lang, reviewed=None):
        # The word's meanings follow its translation string, and its
        # "reviewed" box, ticked or cleared here, applies to all of them.
        from flaskblog.vocabulary import senses
        word = db.session.get(Word, word_id)
        if word is not None:
            db.session.expire(word)
            senses.sync_from_flat(word, [lang])
            if reviewed is not None:
                for sense in word.senses:
                    if lang in sense.translations:
                        sense.translations[lang].reviewed = reviewed
            db.session.commit()


class TranslatorView(ModelView):
    """Who may translate and review which language on /translate
    ('*' for every language)."""

    column_list = ['user', 'lang']
    form_columns = ['user', 'lang']
    form_ajax_refs = {'user': {'fields': ['username'], 'page_size': 20}}
    form_choices = {'lang': [('*', '*')] + [(code, code) for code in LANGUAGE_CODES]}

    def is_accessible(self):
        return is_admin()


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
    # Versions for learners of other languages, as JSON:
    # {"en": {"title", "summary", "explanation", "examples", "exercises"}}.
    # Examples there are [{"ca": ..., "en": ...}].
    translations = db.Column(db.Text, nullable=True)
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

    # -- other languages -------------------------------------------------
    def get_translations(self):
        return json.loads(self.translations) if self.translations else {}

    def set_translation(self, lang, version):
        translations = self.get_translations()
        translations[lang] = version
        self.translations = json.dumps(translations, ensure_ascii=False)

    def _version(self):
        """The adapted version for the content language, if there is one."""
        locale = content_language()
        if locale == 'uk':
            return None
        return self.get_translations().get(locale)

    def _pick(self, field, default):
        version = self._version()
        if version and version.get(field):
            return version[field]
        return default

    @property
    def l_title(self):
        return self._pick('title', self.title)

    @property
    def l_summary(self):
        return self._pick('summary', self.summary)

    @property
    def l_explanation(self):
        return self._pick('explanation', self.explanation)

    @property
    def l_section(self):
        return gettext(self.section)

    def l_examples(self):
        """Examples as [{"ca", "tr"}] with the translation in the interface language."""
        version = self._version()
        if version and version.get('examples'):
            lang = content_language()
            return [{'ca': e['ca'], 'tr': e.get(lang, '')} for e in version['examples']]
        return [{'ca': e['ca'], 'tr': e.get('uk', '')} for e in self.get_examples()]

    def l_exercises(self):
        return self._pick('exercises', self.get_exercises())

    def __repr__(self):
        return f"GrammarUnit({self.number}, '{self.title}')"

    def __str__(self):
        return f"{self.number}. {self.title}"


class GrammarUnitView(ModelView):
    form_columns = [
        'number', 'title', 'section', 'level', 'summary', 'explanation',
        'examples', 'exercises', 'translations',
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
