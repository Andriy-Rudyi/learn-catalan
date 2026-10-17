"""The translation platform (/translate).

Two things are translated here, into any language of flaskblog/languages.py:

* the dictionary, meaning by meaning (WordSense), with English as the
  reference, plus each word's example and notes;
* the interface: the strings of flaskblog/i18n, whose source is Ukrainian.
  What is saved here (UiTranslation) overrides the catalogue files;
  ``flask translations export`` writes it back into them.

Translators of a language (Translator, granted in the admin panel; the
editor counts as one for every language) save directly and check drafts.
Anyone logged in may suggest a translation; a translator accepts or rejects
it. Every change is recorded (TranslationChange) and can be reverted.
"""

import re
from datetime import datetime

from sqlalchemy import and_, or_

from flaskblog import db
from flaskblog.i18n import (EN_MESSAGES, FALLBACK_LANGUAGE, SOURCE_LANGUAGE, _CATALOGS,
                            catalog_entry, forget_overrides, gettext as _, overrides, source_key)
from flaskblog.languages import CODES, LANGUAGES
from flaskblog.models import (SenseTranslation, TranslationChange, TranslationSuggestion,
                              Translator, UiTranslation, Word, WordSense, WordTranslation)
from flaskblog.permissions import is_admin
from flaskblog.vocabulary import senses

ALL_LANGUAGES = '*'
# Someone without translator rights may have this many suggestions waiting.
MAX_OPEN_SUGGESTIONS = 300
MAX_TEXT = 255        # a meaning, an example (the database columns)
MAX_UI_TEXT = 2000


def dictionary_languages():
    return list(CODES)


def interface_languages():
    """The interface is written in Ukrainian; every other language can be
    translated (the language menu shows the ones in flaskblog/i18n)."""
    return [code for code in CODES if code != SOURCE_LANGUAGE]


def language_exists(lang):
    return lang in LANGUAGES


def reference_languages(lang):
    """What a translator into *lang* sees next to the field: English, and
    Ukrainian for English itself."""
    return ['uk'] if lang == 'en' else ['en', 'uk']


# -- who may do what -------------------------------------------------------------

def _authenticated(user):
    return bool(user is not None and getattr(user, 'is_authenticated', False))


def translator_languages(user):
    """Codes *user* may translate, ['*'] for all."""
    if not _authenticated(user):
        return []
    if is_admin(user):
        return [ALL_LANGUAGES]
    return sorted(role.lang for role in Translator.query.filter_by(user_id=user.id))


def can_translate(lang, user):
    codes = translator_languages(user)
    return ALL_LANGUAGES in codes or lang in codes


def can_suggest(user):
    return _authenticated(user)


# -- checks ------------------------------------------------------------------------

_PLACEHOLDER = re.compile(r'\{[A-Za-z_]*\}')
_TAG = re.compile(r'<[^<>]*>')


def check_interface(source, text):
    """An error message when *text* cannot replace *source*, else None.

    The {placeholders} and HTML tags must stay as they are: some strings are
    shown as HTML, so a translation may not bring tags of its own."""
    if len(text) > MAX_UI_TEXT:
        return _('Задовгий текст.')
    # Braces only as the original's placeholders: anything else would be
    # read by str.format ("{term.__class__}").
    if (sorted(_PLACEHOLDER.findall(source)) != sorted(_PLACEHOLDER.findall(text))
            or _stray(_PLACEHOLDER, '{}', text) != _stray(_PLACEHOLDER, '{}', source)):
        return _('Залиште ті самі заповнювачі у фігурних дужках, що й в оригіналі: {items}.',
                 items=', '.join(_PLACEHOLDER.findall(source)) or '—')
    # The same tags, and no "<" or ">" besides them (a tag left open would
    # swallow the page's own markup).
    if (sorted(_TAG.findall(source)) != sorted(_TAG.findall(text))
            or _stray(_TAG, '<>', text) != _stray(_TAG, '<>', source)):
        return _('Залиште ті самі HTML-теги, що й в оригіналі, і не додавайте нових.')
    return None


def _stray(pattern, characters, text):
    """How many of *characters* are in *text* outside *pattern*'s matches."""
    rest = pattern.sub('', text)
    return sum(rest.count(character) for character in characters)


def check_dictionary(kind, text):
    if len(text) > MAX_TEXT:
        return _('Задовгий текст.')
    if kind == 'sense' and ';' in text:
        return _('Крапка з комою розділяє значення слова. Синоніми розділяйте комою.')
    return None


# -- what a suggestion or change is about ------------------------------------------

class Target(object):
    """One translatable thing in one language.

    kind: 'sense' (a meaning; *sense*), 'example' or 'notes' (of *word*),
    'word' (whether the word is checked in that language, no text),
    'ui' (*ui_source*, an interface string).
    """

    def __init__(self, kind, lang, sense=None, word=None, ui_source=None):
        self.kind = kind
        self.lang = lang
        self.sense = sense
        self.word = word if word is not None else (sense.word if sense is not None else None)
        self.ui_source = ui_source

    @classmethod
    def of(cls, row):
        """The target of a TranslationSuggestion or TranslationChange."""
        return cls(row.kind, row.lang, sense=row.sense, word=row.word, ui_source=row.ui_source)

    def columns(self):
        return {
            'kind': self.kind,
            'lang': self.lang,
            'sense_id': self.sense.id if self.sense is not None else None,
            'word_id': self.word.id if self.word is not None else None,
            'ui_key': source_key(self.ui_source) if self.ui_source is not None else None,
            'ui_source': self.ui_source,
        }

    @property
    def exists(self):
        if self.kind == 'ui':
            return self.ui_source in EN_MESSAGES
        if self.kind == 'sense':
            return self.sense is not None
        return self.word is not None

    def check(self, text):
        if self.kind == 'ui':
            return check_interface(self.ui_source, text)
        return check_dictionary(self.kind, text)

    def current(self):
        """(text, reviewed) now; None for what is not there."""
        if self.kind == 'ui':
            row = _ui_row(self.lang, self.ui_source)
            return (row.text if row is not None else None), None
        if self.kind == 'sense':
            entry = self.sense.translations.get(self.lang)
            return (entry.text, entry.reviewed) if entry is not None else (None, None)
        entry = self.word.translations.get(self.lang)
        if entry is None:
            return None, None
        if self.kind == 'word':
            return None, entry.reviewed
        return getattr(entry, self.kind), entry.reviewed

    def shown(self):
        """The text the page shows for it now (an interface string not
        translated on the site shows the catalogue file's)."""
        if self.kind == 'ui':
            return catalog_entry(self.lang, self.ui_source)
        return self.current()[0]

    def apply(self, text, reviewed=True, user=None):
        """Put *text* in place (None or '' removes it)."""
        text = (text or '').strip() or None
        if self.kind == 'ui':
            row = _ui_row(self.lang, self.ui_source)
            if text is None:
                if row is not None:
                    db.session.delete(row)
            else:
                if row is None:
                    row = UiTranslation(lang=self.lang, key=source_key(self.ui_source),
                                        source=self.ui_source, text=text)
                    db.session.add(row)
                row.text = text
                row.updated_at = datetime.utcnow()
                row.updated_by = getattr(user, 'id', None)
            db.session.flush()
            forget_overrides()
            return
        if self.kind == 'sense':
            entry = self.sense.translations.get(self.lang)
            if text is None:
                if entry is not None:
                    del self.sense.translations[self.lang]
            elif entry is None:
                self.sense.translations[self.lang] = SenseTranslation(
                    lang=self.lang, text=text, reviewed=bool(reviewed))
            else:
                entry.text = text
                entry.reviewed = bool(reviewed)
            senses.sync_to_flat(self.word, self.lang)
            return
        if self.kind in ('example', 'notes'):
            self.word._set(self.lang, self.kind, text)
        entry = self.word.translations.get(self.lang)
        if entry is not None:
            entry.edited = True
            if reviewed is not None and (self.kind == 'word' or text is not None):
                entry.reviewed = bool(reviewed)


def _ui_row(lang, source):
    return UiTranslation.query.filter_by(lang=lang, key=source_key(source)).first()


def change(target, text, user, action='edit', reviewed=True):
    """Apply *text* to *target* and record it. The caller commits."""
    old_text, old_reviewed = target.current()
    target.apply(text, reviewed=reviewed, user=user)
    new_text = (text or '').strip() or None
    if target.kind == 'word':
        new_text = old_text = None
    record = TranslationChange(
        action=action, old_text=old_text, new_text=new_text, old_reviewed=old_reviewed,
        user_id=getattr(user, 'id', None), **target.columns()
    )
    db.session.add(record)
    return record


def is_draft(word, lang):
    """True while anything of *word* in *lang* waits to be checked."""
    entry = word.translations.get(lang)
    return bool((entry is not None and not entry.reviewed)
                or not senses.sense_reviewed(word, lang))


def mark_checked(word, lang, user):
    """Translator's "checked": every meaning and the example/notes of *word*
    in *lang* stop being drafts. Returns how many things changed."""
    count = 0
    for sense in word.senses:
        entry = sense.translations.get(lang)
        if entry is not None and not entry.reviewed:
            change(Target('sense', lang, sense=sense), entry.text, user, action='review')
            count += 1
    entry = word.translations.get(lang)
    if entry is not None and not entry.reviewed:
        change(Target('word', lang, word=word), None, user, action='review')
        count += 1
    return count


def revert(record, user):
    """Undo *record*: put back the text (and checked state) it replaced."""
    target = Target.of(record)
    if not target.exists:
        return None
    if record.kind == 'word':
        return change(target, None, user, action='revert', reviewed=bool(record.old_reviewed))
    reviewed = True if record.old_reviewed is None else record.old_reviewed
    return change(target, record.old_text, user, action='revert', reviewed=reviewed)


# -- suggestions -------------------------------------------------------------------

def open_suggestions(user):
    return TranslationSuggestion.query.filter_by(
        user_id=user.id, status=TranslationSuggestion.OPEN).count()


def suggest(target, text, user):
    suggestion = TranslationSuggestion(
        text=text.strip(), status=TranslationSuggestion.OPEN, user_id=user.id, **target.columns()
    )
    db.session.add(suggestion)
    return suggestion


def decide(suggestion, accept, user):
    """Accept (apply, as checked) or reject a suggestion."""
    suggestion.status = TranslationSuggestion.ACCEPTED if accept else TranslationSuggestion.REJECTED
    suggestion.decided_by = user.id
    suggestion.decided_at = datetime.utcnow()
    if accept:
        target = Target.of(suggestion)
        if target.exists:
            change(target, suggestion.text, user, action='accept')


# -- lists ---------------------------------------------------------------------------

DICTIONARY_FILTERS = ('todo', 'missing', 'draft', 'suggestions', 'all')
INTERFACE_FILTERS = ('missing', 'done', 'suggestions', 'all')


def _sense_in(lang):
    return WordSense.translations.any(SenseTranslation.lang == lang)


def _suggested_word_ids(lang):
    return db.session.query(TranslationSuggestion.word_id).filter(
        TranslationSuggestion.lang == lang,
        TranslationSuggestion.status == TranslationSuggestion.OPEN,
        TranslationSuggestion.word_id.isnot(None),
    )


def dictionary_query(lang, status='todo', text=None):
    """Words to show on the dictionary page of *lang*."""
    missing = Word.senses.any(~_sense_in(lang))
    draft = or_(
        Word.senses.any(WordSense.translations.any(
            and_(SenseTranslation.lang == lang, SenseTranslation.reviewed.is_(False)))),
        Word.translations.any(
            and_(WordTranslation.lang == lang, WordTranslation.reviewed.is_(False))),
    )
    query = Word.query
    if status == 'missing':
        query = query.filter(missing)
    elif status == 'draft':
        query = query.filter(draft)
    elif status == 'suggestions':
        query = query.filter(Word.id.in_(_suggested_word_ids(lang)))
    elif status == 'todo':
        query = query.filter(or_(missing, draft))
    if text:
        pattern = '%{}%'.format(text.replace('%', '').replace('_', ''))
        query = query.filter(or_(
            Word.term.ilike(pattern),
            Word.translations.any(WordTranslation.translation.ilike(pattern)),
        ))
    return query.order_by(Word.term)


def suggestions_for_words(lang, words):
    """Open suggestions for these words: {(kind, sense_id or word_id): [...]}."""
    ids = [word.id for word in words]
    if not ids:
        return {}
    found = {}
    rows = (TranslationSuggestion.query
            .filter(TranslationSuggestion.lang == lang,
                    TranslationSuggestion.status == TranslationSuggestion.OPEN,
                    TranslationSuggestion.word_id.in_(ids))
            .order_by(TranslationSuggestion.created_at))
    for row in rows:
        key = (row.kind, row.sense_id if row.kind == 'sense' else row.word_id)
        found.setdefault(key, []).append(row)
    return found


def interface_strings():
    """Every interface string (the keys of the English catalogue)."""
    return list(EN_MESSAGES)


def interface_rows(lang, status='missing', text=None):
    """[(source, reference, current, on_site)] for the interface page."""
    site = overrides(lang)
    catalog = _CATALOGS.get(lang, {})
    suggested = set()
    if status == 'suggestions':
        suggested = {
            source for (source,) in db.session.query(TranslationSuggestion.ui_source).filter(
                TranslationSuggestion.lang == lang, TranslationSuggestion.kind == 'ui',
                TranslationSuggestion.status == TranslationSuggestion.OPEN)
        }
    needle = (text or '').strip().lower()
    rows = []
    for source in interface_strings():
        current = site.get(source, catalog.get(source))
        if status == 'missing' and current is not None:
            continue
        if status == 'done' and current is None:
            continue
        if status == 'suggestions' and source not in suggested:
            continue
        reference = EN_MESSAGES.get(source) if lang != FALLBACK_LANGUAGE else None
        if needle and not any(needle in (value or '').lower() for value in (source, reference, current)):
            continue
        rows.append((source, reference, current, source in site))
    return rows


def ui_suggestions(lang, sources):
    found = {}
    if not sources:
        return found
    keys = [source_key(source) for source in sources]
    rows = (TranslationSuggestion.query
            .filter(TranslationSuggestion.lang == lang, TranslationSuggestion.kind == 'ui',
                    TranslationSuggestion.status == TranslationSuggestion.OPEN,
                    TranslationSuggestion.ui_key.in_(keys))
            .order_by(TranslationSuggestion.created_at))
    for row in rows:
        found.setdefault(row.ui_source, []).append(row)
    return found


# -- progress --------------------------------------------------------------------------

def progress():
    """Per language: dictionary meanings translated and checked, interface
    strings translated, suggestions waiting."""
    total_senses = WordSense.query.count()
    sense_counts = {
        lang: (count, checked or 0)
        for lang, count, checked in db.session.query(
            SenseTranslation.lang,
            db.func.count(SenseTranslation.id),
            db.func.sum(db.case((SenseTranslation.reviewed.is_(True), 1), else_=0)),
        ).group_by(SenseTranslation.lang)
    }
    waiting = dict(
        db.session.query(TranslationSuggestion.lang, db.func.count(TranslationSuggestion.id))
        .filter(TranslationSuggestion.status == TranslationSuggestion.OPEN)
        .group_by(TranslationSuggestion.lang)
    )
    strings = interface_strings()
    rows = []
    for code in CODES:
        translated, checked = sense_counts.get(code, (0, 0))
        if code == SOURCE_LANGUAGE:
            ui_done = None
        else:
            site = overrides(code)
            catalog = _CATALOGS.get(code, {})
            ui_done = sum(1 for source in strings if source in site or source in catalog)
        rows.append({
            'language': LANGUAGES[code],
            'senses': translated,
            'checked': checked,
            'senses_total': total_senses,
            'interface': ui_done,
            'interface_total': len(strings),
            'suggestions': waiting.get(code, 0),
        })
    return rows


def percent(part, whole):
    if not whole:
        return 0
    value = 100.0 * part / whole
    return int(value) if value < 100 else 100


def recent_changes(lang=None, limit=50):
    query = TranslationChange.query
    if lang:
        query = query.filter(TranslationChange.lang == lang)
    return query.order_by(TranslationChange.created_at.desc(), TranslationChange.id.desc()).limit(limit).all()


# -- export (flask translations export) -------------------------------------------------

def export_dictionary(lang):
    """Rows of translations/<lang>.csv from the database."""
    rows = []
    entries = (WordTranslation.query.join(Word)
               .filter(WordTranslation.lang == lang).order_by(Word.term))
    for entry in entries:
        rows.append({
            'term': entry.word.term,
            'translation': entry.translation,
            'example': entry.example or '',
            'notes': entry.notes or '',
            'reviewed': '1' if entry.reviewed and senses.sense_reviewed(entry.word, lang) else '0',
        })
    return rows


def export_interface(lang):
    """The catalogue for *lang*: the file's strings, with the site's on top,
    in the order of the English catalogue."""
    merged = dict(_CATALOGS.get(lang, {}))
    merged.update(overrides(lang))
    order = [source for source in EN_MESSAGES if source in merged]
    order += [source for source in merged if source not in EN_MESSAGES]
    return [(source, merged[source]) for source in order]
