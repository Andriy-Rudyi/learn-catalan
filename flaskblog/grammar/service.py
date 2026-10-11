"""Loading and querying the grammar course."""

import json
import os
from collections import OrderedDict

from slugify import slugify

from flaskblog import db
from flaskblog.models import GrammarUnit

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

REQUIRED_FIELDS = ('number', 'title', 'section', 'explanation')

# Adapted versions of the course for learners of other languages live in
# data/<lang>/ with the same file names; see GrammarUnit.translations.
TRANSLATION_LANGUAGES = ('en',)
TRANSLATED_FIELDS = ('title', 'summary', 'explanation', 'examples', 'exercises')


class SeedReport(object):
    def __init__(self):
        self.created = 0
        self.updated = 0
        self.errors = []

    def __repr__(self):
        return "SeedReport(created={}, updated={}, errors={})".format(
            self.created, self.updated, len(self.errors)
        )


def data_files():
    """The JSON files holding the course, in order."""
    if not os.path.isdir(DATA_DIR):
        return []
    return [
        os.path.join(DATA_DIR, name)
        for name in sorted(os.listdir(DATA_DIR))
        if name.endswith('.json')
    ]


def load_units(paths=None):
    """Read the course from its JSON files, newest definition winning."""
    units = OrderedDict()
    for path in paths if paths is not None else data_files():
        with open(path, encoding='utf-8') as handle:
            payload = json.load(handle)
        for unit in payload:
            missing = [field for field in REQUIRED_FIELDS if not unit.get(field)]
            if missing:
                raise ValueError(
                    'unit {} in {} is missing {}'.format(
                        unit.get('number'), os.path.basename(path), ', '.join(missing)
                    )
                )
            units[unit['number']] = unit
    return [units[number] for number in sorted(units)]


def load_translations(lang):
    """{number: version} for one language, read from data/<lang>/*.json."""
    folder = os.path.join(DATA_DIR, lang)
    versions = {}
    if not os.path.isdir(folder):
        return versions
    for name in sorted(os.listdir(folder)):
        if not name.endswith('.json'):
            continue
        with open(os.path.join(folder, name), encoding='utf-8') as handle:
            for unit in json.load(handle):
                versions[unit['number']] = {
                    field: unit[field] for field in TRANSLATED_FIELDS if field in unit
                }
    return versions


def unique_slug(title, number):
    """A slug for a unit, prefixed with its number so it stays stable."""
    return '{:03d}-{}'.format(number, slugify(title))


def seed(units=None):
    """Create or refresh the course in the database. The caller commits."""
    report = SeedReport()
    translations = {lang: load_translations(lang) for lang in TRANSLATION_LANGUAGES}
    for unit in units if units is not None else load_units():
        existing = GrammarUnit.query.filter_by(number=unit['number']).first()
        target = existing or GrammarUnit(number=unit['number'])
        target.title = unit['title']
        target.section = unit['section']
        target.level = unit.get('level')
        target.summary = unit.get('summary')
        target.explanation = unit['explanation']
        target.set_examples(unit.get('examples', []))
        target.set_exercises(unit.get('exercises', []))
        target.slug = unique_slug(unit['title'], unit['number'])
        target.translations = None
        for lang, versions in translations.items():
            if unit['number'] in versions:
                target.set_translation(lang, versions[unit['number']])
        if existing is None:
            db.session.add(target)
            report.created += 1
        else:
            report.updated += 1
        db.session.flush()
    return report


def sections():
    """Units grouped by section, in course order."""
    grouped = OrderedDict()
    for unit in GrammarUnit.query.order_by(GrammarUnit.number).all():
        grouped.setdefault(unit.section, []).append(unit)
    return grouped


def neighbours(unit):
    """The previous and next unit, for page navigation."""
    previous = (
        GrammarUnit.query.filter(GrammarUnit.number < unit.number)
        .order_by(GrammarUnit.number.desc())
        .first()
    )
    following = (
        GrammarUnit.query.filter(GrammarUnit.number > unit.number)
        .order_by(GrammarUnit.number)
        .first()
    )
    return previous, following
