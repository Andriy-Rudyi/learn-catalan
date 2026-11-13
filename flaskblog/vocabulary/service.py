"""Dictionary queries, CSV import and CSV export."""

import csv
import io
import os
import re

from flask import current_app
from slugify import slugify
from sqlalchemy import case, or_

from flaskblog import db
from flaskblog.languages import CODES as LANGUAGE_CODES, is_known
from flaskblog.models import UserWord, Word, WordTranslation
from flaskblog.i18n import gettext
from flaskblog.vocabulary import senses, varieties
from flaskblog.vocabulary.constants import CSV_COLUMNS

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
# The bundled dictionary: the Catalan side of every word, and one file per
# language with its translations (translations/uk.csv, translations/en.csv...),
# all matched by "term". A new language is a new file there.
WORDS_FILE = os.path.join(DATA_DIR, 'words.csv')
TRANSLATIONS_DIR = os.path.join(DATA_DIR, 'translations')

# Catalan fields of a word, as CSV columns.
WORD_FIELDS = ('term', 'part_of_speech', 'gender', 'pronunciation', 'topic', 'level', 'example_ca')
# Per-language fields, as columns "<field>_<lang>" (translation_fr, example_fr...).
TRANSLATION_FIELDS = ('translation', 'example', 'notes')
# Ukrainian and English keep the column names they had before.
LEGACY_COLUMNS = {
    'translation': ('uk', 'translation'),
    'example_uk': ('uk', 'example'),
    'notes': ('uk', 'notes'),
    'translation_en': ('en', 'translation'),
    'example_en': ('en', 'example'),
    'notes_en': ('en', 'notes'),
}
_COLUMN_NAMES = {value: key for key, value in LEGACY_COLUMNS.items()}
_COLUMN = re.compile(r'^(translation|example|notes|reviewed)_([a-z]{2,3})$')
# Values of a "reviewed" column that mark a draft.
_DRAFT = ('0', 'no', 'false', 'draft')


def column_name(lang, field):
    """The CSV column for *field* in *lang*: translation_fr, or a legacy name."""
    return _COLUMN_NAMES.get((lang, field), '{}_{}'.format(field, lang))


def parse_column(name):
    """(lang, field) for a translation column, None for anything else."""
    if name in LEGACY_COLUMNS:
        return LEGACY_COLUMNS[name]
    match = _COLUMN.match(name or '')
    if match and is_known(match.group(2)):
        return match.group(2), match.group(1)
    return None


class ImportReport(object):
    """What an import did, so the caller can report it."""

    def __init__(self):
        self.created = 0
        self.updated = 0
        self.skipped = 0
        self.errors = []

    @property
    def total(self):
        return self.created + self.updated + self.skipped

    def __repr__(self):
        return (
            "ImportReport(created={}, updated={}, skipped={}, errors={})".format(
                self.created, self.updated, self.skipped, len(self.errors)
            )
        )


def unique_slug(term):
    """A slug for *term* that no other word uses yet."""
    base = slugify(term) or 'word'
    slug = base
    counter = 1
    while Word.query.filter_by(slug=slug).first() is not None:
        slug = '{}-{}'.format(base, counter)
        counter += 1
    return slug


# Config flag -> the Word.source it shows.
SOURCE_FLAGS = (('DACCO', 'dacco'), ('APERTIUM_WORDS', 'apertium'))


def shown(query):
    """*query* without the imported words whose source is switched off
    (DACCO=False, APERTIUM_WORDS=False)."""
    hidden = [source for flag, source in SOURCE_FLAGS if not current_app.config.get(flag, True)]
    if not hidden:
        return query
    return query.filter(or_(Word.source.is_(None), Word.source.notin_(hidden)))


def search(query_text=None, topic=None, level=None, part_of_speech=None, variety=None):
    """A Word query narrowed by the dictionary filters.

    *variety* is 'central' (hide regional and archaic words) or 'regional'
    (only those). With *query_text* the best matches come first: the word
    itself, then words starting with it, then words containing it, then
    matches in the translations and finally in the examples.
    """
    query = shown(Word.query)
    rank = None
    in_translation = None
    if variety == 'central':
        query = query.filter(or_(Word.variety.is_(None), Word.variety == ''))
    elif variety == 'regional':
        query = query.filter(Word.variety.isnot(None), Word.variety != '')
    if query_text:
        text = query_text.strip().replace('%', '').replace('_', '')
        pattern = '%{}%'.format(text)
        # A translation in any language.
        in_translation = Word.translations.any(WordTranslation.translation.ilike(pattern))
        rank = case(
            (db.func.lower(Word.term) == text.lower(), 0),
            (Word.term.ilike(text + '%'), 1),
            (Word.term.ilike(pattern), 2),
            (in_translation, 3),
            else_=4,
        )
        query = query.filter(
            or_(
                Word.term.ilike(pattern),
                in_translation,
                Word.example_ca.ilike(pattern),
            )
        )
    if topic:
        query = query.filter(Word.topic == topic)
    if level:
        query = query.filter(Word.level == level)
    if part_of_speech:
        query = query.filter(Word.part_of_speech == part_of_speech)
    if rank is not None:
        return query.order_by(rank, db.func.length(Word.term), Word.term)
    return query.order_by(Word.term)


def similar_queries(query_text):
    """What to look for when *query_text* finds nothing: the dictionary
    form of a Catalan word ("maldestres" -> "maldestre", "anava" -> "anar"),
    then the word without its last letters ("deflection" -> "deflect"),
    which reaches related words in any language."""
    text = (query_text or '').strip()
    if not text or ' ' in text:
        return []
    out = []
    try:
        from flaskblog.reader import morphology
        for lemma, _kind, _slot in morphology.readings(text):
            if lemma.lower() != text.lower() and lemma not in out:
                out.append(lemma)
        for base, _kind, _plural in morphology.derived_readings(text, lambda lemma: False):
            if base not in out:
                out.append(base)
    except Exception:  # the reader's data is missing: only the shorter forms
        pass
    for cut in range(1, 5):
        if len(text) - cut >= 4:
            out.append(text[:-cut])
    return out


def base_words(query_text, limit=4):
    """Dictionary words *query_text* is a form of ("anava" -> anar,
    "maldestres" -> maldestre), for a line above the search results."""
    text = (query_text or '').strip()
    if not text or ' ' in text or len(text) > 40:
        return []
    try:
        from flaskblog.reader import morphology
        lemmas = [lemma.lower() for lemma, _kind, _slot in morphology.readings(text)]
    except Exception:
        return []
    lemmas = [lemma for lemma in dict.fromkeys(lemmas) if lemma != text.lower()][:8]
    if not lemmas:
        return []
    found = {word.term.lower(): word
             for word in shown(Word.query).filter(db.func.lower(Word.term).in_(lemmas))}
    return [found[lemma] for lemma in lemmas if lemma in found][:limit]


def search_with_fallback(query_text=None, **filters):
    """(query, None) as :func:`search`, or, when that finds nothing,
    (the query of the first similar search that finds something, what it
    looked for)."""
    query = search(query_text, **filters)
    if not query_text or query.limit(1).count():
        return query, None
    for candidate in similar_queries(query_text)[:8]:
        similar = search(candidate, **filters)
        if similar.limit(1).count():
            return similar, candidate
    return query, None


def suggestions(prefix, limit=8):
    """Words for the search box: Catalan words starting with *prefix*, then
    words with a translation, in any language, that starts with it."""
    text = prefix.replace('%', '').replace('_', '')
    words = (shown(Word.query).filter(Word.term.ilike(text + '%'))
             .order_by(db.func.length(Word.term), Word.term).limit(limit).all())
    if len(words) < limit:
        seen = {word.id for word in words}
        translated = (shown(Word.query)
                      .filter(Word.translations.any(WordTranslation.translation.ilike(text + '%')))
                      .order_by(db.func.length(Word.term), Word.term).limit(limit).all())
        words += [word for word in translated if word.id not in seen][:limit - len(words)]
    return words


def user_word_counts(user_id):
    """How many words someone has in "My dictionary": all, learning, known."""
    words = UserWord.query.filter_by(user_id=user_id)
    return {
        'all': words.count(),
        'learning': words.filter(UserWord.status == UserWord.STATUS_LEARNING).count(),
        'known': words.filter(UserWord.status == UserWord.STATUS_KNOWN).count(),
    }


def read_rows(stream):
    """Read dictionary rows from an open CSV stream."""
    if isinstance(stream, bytes):
        stream = io.StringIO(stream.decode('utf-8-sig'))
    elif isinstance(stream, str):
        stream = io.StringIO(stream)
    reader = csv.DictReader(stream)
    return [row for row in reader]


def import_rows(rows, author=None, update_existing=False, seed=False):
    """Create (or update) dictionary entries from CSV-style rows.

    Columns are the Catalan fields (WORD_FIELDS) and, per language,
    ``translation_<lang>``, ``example_<lang>`` and ``notes_<lang>`` (or the
    legacy names: translation, example_uk, notes, translation_en...). Rows
    without a term or without a translation in any language are reported
    as errors; a term that already exists is skipped unless
    *update_existing* is set, and then only the columns in the row change.

    A translation changed this way counts as edited on the site, except
    with *seed* (the bundled files, loaded on every deploy): those leave
    alone the languages of a word that were edited on the site.
    The caller commits.
    """
    report = ImportReport()
    # Only the words the rows name: the dictionary is far bigger than a file.
    wanted = sorted({(row.get('term') or '').strip().lower() for row in rows} - {''})
    existing_words = {}
    for start in range(0, len(wanted), 500):
        chunk = wanted[start:start + 500]
        for word in Word.query.filter(db.func.lower(Word.term).in_(chunk)):
            existing_words[word.term.lower()] = word
    for number, row in enumerate(rows, start=2):  # row 1 is the header
        values = {
            field: (row.get(field) or '').strip()
            for field in WORD_FIELDS
            if field in row
        }
        translations = {}
        for column, value in row.items():
            parsed = parse_column(column)
            if parsed:
                lang, field = parsed
                translations.setdefault(lang, {})[field] = (value or '').strip()
        term = values.get('term', '')
        if not term or not any(fields.get('translation') for fields in translations.values()):
            report.errors.append(
                gettext('рядок {number}: потрібні колонки term і translation', number=number)
            )
            continue

        word = existing_words.get(term.lower())
        if word is not None:
            if not update_existing:
                report.skipped += 1
                continue
            for field, value in values.items():
                if field != 'term':
                    setattr(word, field, value or None)
            word.source = None  # an imported word is now one of the site's own
            _apply_translations(word, translations, seed)
            report.updated += 1
            continue

        word = Word(
            term=term,
            slug=unique_slug(term),
            part_of_speech=values.get('part_of_speech') or None,
            gender=values.get('gender') or None,
            pronunciation=values.get('pronunciation') or None,
            topic=values.get('topic') or None,
            level=values.get('level') or None,
            example_ca=values.get('example_ca') or None,
            user_id=getattr(author, 'id', None),
        )
        _apply_translations(word, translations, seed)
        db.session.add(word)
        # Flush so that the next row's slug check sees this word.
        db.session.flush()
        existing_words[term.lower()] = word
        report.created += 1
    return report


def _apply_translations(word, translations, seed=False):
    changed = []
    for lang, fields in translations.items():
        before = word.translations.get(lang)
        if seed and before is not None and before.edited:
            continue  # edited on the site since: the site wins
        changed.append(lang)
        before = None if before is None else tuple(getattr(before, f) for f in TRANSLATION_FIELDS)
        for field, value in fields.items():
            if field != 'reviewed':
                word._set(lang, field, value)
        entry = word.translations.get(lang)
        if entry is None:
            continue
        if not seed and before != tuple(getattr(entry, f) for f in TRANSLATION_FIELDS):
            entry.edited = True
        if 'reviewed' not in fields:
            continue
        if fields['reviewed'].lower() not in _DRAFT:
            entry.reviewed = True
        elif before != tuple(getattr(entry, f) for f in TRANSLATION_FIELDS):
            # A draft mark only applies to new or changed text, so re-seeding
            # does not undo an editor's review of the same translation.
            entry.reviewed = False
    if changed:
        senses.sync_from_flat(word, changed)


def save_translations(word, translations):
    """Translations typed in on the site (the editor's form, the admin):
    {lang: {field: value}}. Changed languages are marked as edited on the
    site and their meanings follow. The caller commits."""
    changed = []
    for lang, fields in translations.items():
        before = word.translations.get(lang)
        before = None if before is None else tuple(getattr(before, f) for f in TRANSLATION_FIELDS)
        for field, value in fields.items():
            word._set(lang, field, (value or '').strip() or None)
        entry = word.translations.get(lang)
        after = None if entry is None else tuple(getattr(entry, f) for f in TRANSLATION_FIELDS)
        if before != after:
            changed.append(lang)
            if entry is not None:
                entry.edited = True
    if changed:
        senses.sync_from_flat(word, changed)
    return changed


def import_file(path, author=None, update_existing=False):
    with io.open(path, encoding='utf-8-sig', newline='') as handle:
        return import_rows(read_rows(handle), author, update_existing)


def _read_csv(path):
    with io.open(path, encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def seed_languages():
    """Codes of the languages that have a translations file."""
    names = os.listdir(TRANSLATIONS_DIR) if os.path.isdir(TRANSLATIONS_DIR) else []
    found = {name[:-4] for name in names if name.endswith('.csv')}
    return [code for code in LANGUAGE_CODES if code in found]


def seed_rows():
    """The bundled dictionary as import rows: words.csv joined with every
    translations/<lang>.csv by term."""
    rows = [dict(row) for row in _read_csv(WORDS_FILE)]
    by_term = {row['term']: row for row in rows}
    for lang in seed_languages():
        for entry in _read_csv(os.path.join(TRANSLATIONS_DIR, lang + '.csv')):
            row = by_term.get(entry.get('term'))
            if row is None:
                continue  # a translation of a word that is not in words.csv
            for field in TRANSLATION_FIELDS + ('reviewed',):
                if field in entry:
                    row[column_name(lang, field)] = entry.get(field) or ''
    return rows


def import_seed(author=None, update_existing=False):
    """Load the dictionary that ships with the project."""
    report = import_rows(seed_rows(), author=author, update_existing=update_existing, seed=True)
    apply_varieties()
    return report


# Marks that come from the data file; anything else was set by hand in the
# admin and is left alone.
GENERATED_SOURCES = ('review', 'wiktionary-en', 'wiktionary-ca')


def apply_varieties(entries=None):
    """Copy the regional marks from data/varieties.json onto the words.

    Returns the number of words whose mark changed. The caller commits.
    """
    entries = varieties.load() if entries is None else entries
    changed = 0
    for word in Word.query.all():
        entry = entries.get(word.term)
        if entry:
            value = ','.join(varieties.parse_codes(entry.get('variety'))) or None
            source = entry.get('source') or 'review'
        elif word.variety_source in GENERATED_SOURCES or not word.variety_source:
            value = source = None
        else:
            continue  # a manual mark
        if (word.variety, word.variety_source) != (value, source):
            word.variety, word.variety_source = value, source
            changed += 1
    return changed


def export_csv(words=None):
    """Serialise the dictionary (or *words*) as CSV text.

    Ukrainian and English come in the familiar columns (CSV_COLUMNS); every
    other language with translations adds translation_<lang>, example_<lang>
    and notes_<lang>, so the file imports back unchanged.
    """
    if words is None:
        words = Word.query.order_by(Word.term).all()
    others = [
        lang for lang in LANGUAGE_CODES
        if lang not in ('uk', 'en') and any(lang in word.translations for word in words)
    ]
    columns = list(CSV_COLUMNS) + [
        column_name(lang, field) for lang in others for field in TRANSLATION_FIELDS + ('reviewed',)
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for word in words:
        row = {}
        for column in columns:
            parsed = parse_column(column)
            if parsed and parsed[1] == 'reviewed':
                entry = word.translations.get(parsed[0])
                value = '' if entry is None else ('1' if entry.reviewed else '0')
            else:
                value = word._get(*parsed) if parsed else getattr(word, column, '')
            row[column] = value or ''
        writer.writerow(row)
    return buffer.getvalue()


def export_user_words_csv(user_words):
    """Serialise someone's personal dictionary as CSV text."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['term', 'translation', 'note', 'status', 'date_added'])
    for item in user_words:
        writer.writerow(
            [
                item.display_term or '',
                item.display_translation or '',
                item.note or '',
                item.status,
                item.date_added.strftime('%Y-%m-%d') if item.date_added else '',
            ]
        )
    return buffer.getvalue()
