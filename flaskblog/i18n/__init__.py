"""Site languages: English (the main one), Ukrainian and French.

Strings in the code and templates are written in Ukrainian and wrapped in
``_()``; other languages look them up in their catalogue (en.MESSAGES,
fr.MESSAGES). English is the default and the fallback for everything:
visitors whose browser asks for none of the site's languages get English,
a string missing from the French catalogue is shown in English, and so is
course content that has no French version yet (grammar, pronunciation,
FAQ). The dictionary shows French translations where they exist.

The test suite checks that English and French pages contain no Cyrillic,
so gaps in the catalogues are caught.

The language comes from ``?lang=`` (remembered in a cookie), then the cookie,
then the browser's Accept-Language header.
"""

from flask import current_app, has_request_context, request

from flaskblog.i18n.en import MESSAGES as EN_MESSAGES
from flaskblog.i18n.fr import MESSAGES as FR_MESSAGES

LANGUAGES = ('en', 'uk', 'fr')
SOURCE_LANGUAGE = 'uk'   # the language the strings are written in
FALLBACK_LANGUAGE = 'en'  # used for anything missing in the chosen language
DEFAULT_LANGUAGE = 'en'   # when nothing tells us what the visitor reads
COOKIE_NAME = 'lang'
COOKIE_MAX_AGE = 365 * 24 * 3600
_ENVIRON_KEY = 'learn_catalan.locale'

LANGUAGE_NAMES = {'en': 'English', 'uk': 'Українська', 'fr': 'Français'}
LANGUAGE_SHORT = {'en': 'EN', 'uk': 'UA', 'fr': 'FR'}

_CATALOGS = {'en': EN_MESSAGES, 'fr': FR_MESSAGES}
# Languages the courses (grammar, pronunciation, FAQ) are written for; the
# others are shown the English course.
COURSE_LANGUAGES = ('uk', 'en')

# Shown by static/speak.js when the device has no Catalan voice.
SPEAK_HINT = (
    'На цьому пристрої немає каталонського голосу для озвучення. '
    'Додайте його в налаштуваннях: <strong>Android</strong>: «Синтез мовлення» Google → мова «Català»; '
    '<strong>iPhone</strong>: Універсальний доступ → Озвучений вміст → Голоси → Català; '
    '<strong>Windows</strong>: Час і мова → Мовлення → додати каталонську, або відкрийте сайт у браузері Edge.'
)


def _default_language():
    if has_request_context():
        return current_app.config.get('DEFAULT_LANGUAGE', DEFAULT_LANGUAGE)
    return DEFAULT_LANGUAGE


def _from_browser():
    header = request.headers.get('Accept-Language')
    if not header:
        return _default_language()
    # Russian-speaking Ukrainians usually prefer the Ukrainian interface;
    # anyone else gets their language if the site has it, English if not.
    best = request.accept_languages.best_match(('uk', 'ru') + LANGUAGES)
    if best in ('uk', 'ru'):
        return 'uk'
    return best if best in LANGUAGES else FALLBACK_LANGUAGE


def get_locale():
    """Language of the current request."""
    if not has_request_context():
        return SOURCE_LANGUAGE
    locale = request.environ.get(_ENVIRON_KEY)
    if locale is None:
        chosen = request.args.get('lang') or request.cookies.get(COOKIE_NAME)
        locale = chosen if chosen in LANGUAGES else _from_browser()
        request.environ[_ENVIRON_KEY] = locale
    return locale


def content_language(locale=None):
    """The language of the courses (grammar, pronunciation, FAQ): the chosen
    one when there is a course for it, English otherwise."""
    locale = locale or get_locale()
    return locale if locale in COURSE_LANGUAGES else FALLBACK_LANGUAGE


def gettext(text, **kwargs):
    """Translate a Ukrainian source string into the current language,
    falling back to English."""
    locale = get_locale()
    if locale != SOURCE_LANGUAGE:
        translated = _CATALOGS.get(locale, {}).get(text)
        if translated is None:
            translated = _CATALOGS[FALLBACK_LANGUAGE].get(text, text)
        text = translated
    return text.format(**kwargs) if kwargs else text


_ = gettext


def plural(count, uk_forms, en_forms=None):
    """``"5 юнітів"`` / ``"5 units"`` / ``"5 unités"``.

    ``uk_forms`` is (one, few, many): юніт, юніти, юнітів;
    ``en_forms`` is (one, other). Other languages translate the Ukrainian
    forms through their catalogue, falling back to ``en_forms``.
    """
    locale = get_locale()
    if locale != SOURCE_LANGUAGE:
        catalog = _CATALOGS.get(locale, {})
        forms = None
        if locale != FALLBACK_LANGUAGE and uk_forms[0] in catalog and uk_forms[2] in catalog:
            forms = (catalog[uk_forms[0]], catalog[uk_forms[2]])
        if forms is None:
            forms = en_forms or (gettext(uk_forms[0]), gettext(uk_forms[2]))
        # French counts 0 and 1 as singular; English only 1.
        singular = abs(count) < 2 if locale == 'fr' else count == 1
        word = forms[0] if singular else forms[1]
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
            'content_lang': content_language(locale),
            'site_languages': LANGUAGES,
            'language_names': LANGUAGE_NAMES,
            'language_short': LANGUAGE_SHORT,
            'url_with_lang': url_with_lang,
            'speak_hint': gettext(SPEAK_HINT),
        }

    @app.after_request
    def remember_language(response):
        if request.blueprint == 'api':
            return response  # ?lang= there picks translations, not the interface
        chosen = request.args.get('lang')
        if chosen in LANGUAGES and request.cookies.get(COOKIE_NAME) != chosen:
            response.set_cookie(COOKIE_NAME, chosen, max_age=COOKIE_MAX_AGE,
                                samesite='Lax')
        response.vary.add('Cookie')
        response.vary.add('Accept-Language')
        return response
