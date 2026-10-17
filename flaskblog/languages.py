"""Languages the Catalan dictionary is translated into.

The dictionary keeps one Catalan entry per word (``Word``) and one row per
language for its translation, example and notes (``WordTranslation``). A new
language needs no database change: add it here and put its translations in
``vocabulary/data/translations/<code>.csv`` (or the admin panel), then run
``flask vocabulary seed --update``.

The interface itself is translated separately (flaskblog/i18n); a language
can have dictionary translations before it has an interface.
"""

from collections import namedtuple

Language = namedtuple('Language', 'code name native rtl')

# The language being learnt.
SOURCE = 'ca'

# ISO 639-1 codes. Order is the order of the lists shown to people.
_ALL = (
    Language('uk', 'Ukrainian', 'Українська', False),
    Language('en', 'English', 'English', False),
    Language('fr', 'French', 'Français', False),
    Language('it', 'Italian', 'Italiano', False),
    Language('es', 'Spanish', 'Español', False),
    Language('pl', 'Polish', 'Polski', False),
    Language('de', 'German', 'Deutsch', False),
    Language('ar', 'Arabic', 'العربية', True),
    Language('zh', 'Chinese', '中文', False),
)

LANGUAGES = {language.code: language for language in _ALL}
CODES = tuple(language.code for language in _ALL)

# Where a missing translation is taken from, after the language asked for.
FALLBACK = ('en', 'uk')


def is_known(code):
    return code in LANGUAGES


def fallback_chain(code):
    """``code`` first, then the fallbacks, without repeats."""
    chain = [code] if code else []
    return chain + [lang for lang in FALLBACK if lang not in chain]
