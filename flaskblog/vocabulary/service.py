"""Dictionary queries, CSV import and CSV export."""

import csv
import io
import os
import re

from slugify import slugify
from sqlalchemy import case, or_

from flaskblog import db
from flaskblog.languages import CODES as LANGUAGE_CODES, is_known
from flaskblog.models import UserWord, Word, WordTranslation
from flaskblog.i18n import gettext
from flaskblog.vocabulary import varieties
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
_COLUMN = re.compile(r'^(translation|example|notes)_([a-z]{2,3})$')


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


def search(query_text=None, topic=None, level=None, part_of_speech=None, variety=None):
    """A Word query narrowed by the dictionary filters.

    *variety* is 'central' (hide regional and archaic words) or 'regional'
    (only those). With *query_text* the best matches come first: the word
    itself, then words starting with it, then words containing it, then
    matches in the translations and finally in the examples.
    """
    query = Word.query
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


def import_rows(rows, author=None, update_existing=False):
    """Create (or update) dictionary entries from CSV-style rows.

    Columns are the Catalan fields (WORD_FIELDS) and, per language,
    ``translation_<lang>``, ``example_<lang>`` and ``notes_<lang>`` (or the
    legacy names: translation, example_uk, notes, translation_en...). Rows
    without a term or without a translation in any language are reported
    as errors; a term that already exists is skipped unless
    *update_existing* is set, and then only the columns in the row change.
    The caller commits.
    """
    report = ImportReport()
    existing_words = {word.term.lower(): word for word in Word.query.all()}
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
            _apply_translations(word, translations)
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
        _apply_translations(word, translations)
        db.session.add(word)
        # Flush so that the next row's slug check sees this word.
        db.session.flush()
        existing_words[term.lower()] = word
        report.created += 1
    return report


def _apply_translations(word, translations):
    for lang, fields in translations.items():
        for field, value in fields.items():
            word._set(lang, field, value)


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
            for field in TRANSLATION_FIELDS:
                row[column_name(lang, field)] = entry.get(field) or ''
    return rows


def import_seed(author=None, update_existing=False):
    """Load the dictionary that ships with the project."""
    report = import_rows(seed_rows(), author=author, update_existing=update_existing)
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
        column_name(lang, field) for lang in others for field in TRANSLATION_FIELDS
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for word in words:
        row = {}
        for column in columns:
            parsed = parse_column(column)
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
