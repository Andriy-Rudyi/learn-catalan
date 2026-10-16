"""Dictionary queries, CSV import and CSV export."""

import csv
import io
import os

from slugify import slugify
from sqlalchemy import case, or_

from flaskblog import db
from flaskblog.models import Word
from flaskblog.i18n import gettext
from flaskblog.vocabulary import varieties
from flaskblog.vocabulary.constants import CSV_COLUMNS

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
SEED_FILE = os.path.join(DATA_DIR, 'seed_words.csv')

# Only these may be set from a CSV row; anything else in the file is ignored.
IMPORTABLE_FIELDS = CSV_COLUMNS


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
    if variety == 'central':
        query = query.filter(or_(Word.variety.is_(None), Word.variety == ''))
    elif variety == 'regional':
        query = query.filter(Word.variety.isnot(None), Word.variety != '')
    if query_text:
        text = query_text.strip().replace('%', '').replace('_', '')
        pattern = '%{}%'.format(text)
        rank = case(
            (db.func.lower(Word.term) == text.lower(), 0),
            (Word.term.ilike(text + '%'), 1),
            (Word.term.ilike(pattern), 2),
            (or_(Word.translation.ilike(pattern), Word.translation_en.ilike(pattern)), 3),
            else_=4,
        )
        query = query.filter(
            or_(
                Word.term.ilike(pattern),
                Word.translation.ilike(pattern),
                Word.translation_en.ilike(pattern),
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

    Rows without a term and a translation are reported as errors; a term
    that already exists is skipped unless *update_existing* is set.  The
    caller commits.
    """
    report = ImportReport()
    for number, row in enumerate(rows, start=2):  # row 1 is the header
        values = {
            field: (row.get(field) or '').strip()
            for field in IMPORTABLE_FIELDS
            if field in row
        }
        term = values.get('term', '')
        translation = values.get('translation', '')
        if not term or not translation:
            report.errors.append(
                gettext('рядок {number}: потрібні колонки term і translation', number=number)
            )
            continue

        existing = Word.query.filter(db.func.lower(Word.term) == term.lower()).first()
        if existing is not None:
            if not update_existing:
                report.skipped += 1
                continue
            for field, value in values.items():
                if field != 'term':
                    setattr(existing, field, value or None)
            report.updated += 1
            continue

        word = Word(
            term=term,
            translation=translation,
            slug=unique_slug(term),
            part_of_speech=values.get('part_of_speech') or None,
            gender=values.get('gender') or None,
            pronunciation=values.get('pronunciation') or None,
            topic=values.get('topic') or None,
            level=values.get('level') or None,
            example_ca=values.get('example_ca') or None,
            example_uk=values.get('example_uk') or None,
            notes=values.get('notes') or None,
            translation_en=values.get('translation_en') or None,
            example_en=values.get('example_en') or None,
            notes_en=values.get('notes_en') or None,
            user_id=getattr(author, 'id', None),
        )
        db.session.add(word)
        # Flush so that the next row's uniqueness checks see this term.
        db.session.flush()
        report.created += 1
    return report


def import_file(path, author=None, update_existing=False):
    with io.open(path, encoding='utf-8-sig', newline='') as handle:
        return import_rows(read_rows(handle), author, update_existing)


def import_seed(author=None, update_existing=False):
    """Load the dictionary that ships with the project."""
    report = import_file(SEED_FILE, author=author, update_existing=update_existing)
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
    """Serialise the dictionary (or *words*) as CSV text."""
    if words is None:
        words = Word.query.order_by(Word.term).all()
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(CSV_COLUMNS))
    writer.writeheader()
    for word in words:
        writer.writerow(
            {field: getattr(word, field, '') or '' for field in CSV_COLUMNS}
        )
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
