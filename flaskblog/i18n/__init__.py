"""Interface languages: Ukrainian (the source language) and English.

Strings in the code and templates are written in Ukrainian and wrapped in
``_()``; the English text is looked up in ``en.MESSAGES``. A missing English
entry falls back to the Ukrainian text, and the test suite checks that the
English pages contain no Cyrillic, so gaps are caught.

The language comes from ``?lang=`` (remembered in a cookie), then the cookie,
then the browser's Accept-Language header.
"""

from flask import has_request_context, request

from flaskblog.i18n.en import MESSAGES as EN_MESSAGES

LANGUAGES = ('uk', 'en')
DEFAULT_LANGUAGE = 'uk'
COOKIE_NAME = 'lang'
COOKIE_MAX_AGE = 365 * 24 * 3600
_ENVIRON_KEY = 'learn_catalan.locale'

LANGUAGE_NAMES = {'uk': 'Українська', 'en': 'English'}
LANGUAGE_SHORT = {'uk': 'UA', 'en': 'EN'}

_CATALOGS = {'en': EN_MESSAGES}

# Shown by static/speak.js when the device has no Catalan voice.
SPEAK_HINT = (
    'На цьому пристрої немає каталонського голосу для озвучення. '
    'Додайте його в налаштуваннях: <strong>Android</strong> — «Синтез мовлення» Google → мова «Català»; '
    '<strong>iPhone</strong> — Універсальний доступ → Озвучений вміст → Голоси → Català; '
    '<strong>Windows</strong> — Час і мова → Мовлення → додати каталонську, або відкрийте сайт у браузері Edge.'
)


def _from_browser():
    header = request.headers.get('Accept-Language')
    if not header:
        return DEFAULT_LANGUAGE
    # Russian-speaking Ukrainians usually prefer the Ukrainian interface;
    # anyone else is more likely to read English than Ukrainian.
    best = request.accept_languages.best_match(('uk', 'ru', 'en'))
    if best in ('uk', 'ru'):
        return 'uk'
    return 'en'


def get_locale():
    """Language of the current request."""
    if not has_request_context():
        return DEFAULT_LANGUAGE
    locale = request.environ.get(_ENVIRON_KEY)
    if locale is None:
        chosen = request.args.get('lang') or request.cookies.get(COOKIE_NAME)
        locale = chosen if chosen in LANGUAGES else _from_browser()
        request.environ[_ENVIRON_KEY] = locale
    return locale


def gettext(text, **kwargs):
    """Translate a Ukrainian source string into the current language."""
    locale = get_locale()
    if locale != DEFAULT_LANGUAGE:
        text = _CATALOGS.get(locale, {}).get(text, text)
    return text.format(**kwargs) if kwargs else text


_ = gettext


def plural(count, uk_forms, en_forms=None):
    """``"5 юнітів"`` / ``"5 units"``.

    ``uk_forms`` is (one, few, many) — юніт, юніти, юнітів;
    ``en_forms`` is (one, other). Without ``en_forms`` the Ukrainian forms are
    translated through the catalogue.
    """
    if get_locale() == 'en':
        if en_forms is None:
            en_forms = (gettext(uk_forms[0]), gettext(uk_forms[2]))
        word = en_forms[0] if count == 1 else en_forms[1]
    else:
        n = abs(count)
        if n % 10 == 1 and n % 100 != 11:
            word = uk_forms[0]
        elif 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
            word = uk_forms[1]
        else:
            word = uk_forms[2]
    return '{} {}'.format(count, word)


class LazyString:
    """A string translated when it is used, for module-level labels."""

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return gettext(self.text)

    def __html__(self):
        from markupsafe import escape
        return str(escape(str(self)))

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.text)

    def __add__(self, other):
        return str(self) + str(other)

    def __radd__(self, other):
        return str(other) + str(self)

    def __mod__(self, other):
        return str(self) % other

    def format(self, *args, **kwargs):
        return str(self).format(*args, **kwargs)

    def __repr__(self):
        return 'LazyString({!r})'.format(self.text)


def lazy_gettext(text):
    return LazyString(text)


def url_with_lang(lang):
    """The current page in another language."""
    args = request.args.to_dict(flat=False)
    args['lang'] = [lang]
    from urllib.parse import urlencode
    return request.path + '?' + urlencode(args, doseq=True)


def _localize_forms(app):
    """Built-in WTForms messages ("This field is required.") follow the
    interface language, using the translations bundled with WTForms."""
    from flask_wtf import FlaskForm

    app.config['WTF_I18N_ENABLED'] = False  # Flask-WTF's own hook needs Flask-Babel
    FlaskForm.Meta.locales = property(lambda meta: [get_locale()])


def init_app(app):
    _localize_forms(app)

    @app.context_processor
    def inject_i18n():
        locale = get_locale()
        return {
            '_': gettext,
            'plural': plural,
            'current_lang': locale,
            'other_lang': 'en' if locale == 'uk' else 'uk',
            'language_names': LANGUAGE_NAMES,
            'language_short': LANGUAGE_SHORT,
            'url_with_lang': url_with_lang,
            'speak_hint': gettext(SPEAK_HINT),
        }

    @app.after_request
    def remember_language(response):
        chosen = request.args.get('lang')
        if chosen in LANGUAGES and request.cookies.get(COOKIE_NAME) != chosen:
            response.set_cookie(COOKIE_NAME, chosen, max_age=COOKIE_MAX_AGE,
                                samesite='Lax')
        response.vary.add('Cookie')
        response.vary.add('Accept-Language')
        return response
