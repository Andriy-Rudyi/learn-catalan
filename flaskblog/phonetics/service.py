"""Phonetics lessons live in a JSON file next to the code.

They are reference material rather than user content, so unlike the grammar
units they are not stored in the database: the file is read once and kept in
memory.
"""

import json
import os
from collections import OrderedDict

from flaskblog.i18n import content_language

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATA_FILE = os.path.join(DATA_DIR, 'lessons.json')
# The same lessons adapted for learners of other languages: lessons_<lang>.json,
# with the explanations of sounds and words under the key <lang> instead of "uk".
LANGUAGE_FILES = {'en': os.path.join(DATA_DIR, 'lessons_en.json')}

# Order of the sections on the index page.
SECTION_ORDER = (
    'Основи',
    'Голосні',
    'Приголосні',
    'Наголос і склад',
    'Вимова у мовленні',
)

_cache = {}


def lessons_file(lang=None):
    """The lessons file for a language, Ukrainian when there is no adaptation."""
    path = LANGUAGE_FILES.get(lang or content_language())
    return path if path and os.path.exists(path) else DATA_FILE


def load_lessons(path=None):
    """All lessons sorted by number (cached per file path)."""
    path = path or lessons_file()
    if path not in _cache:
        with open(path, encoding='utf-8') as handle:
            lessons = json.load(handle)
        _cache[path] = sorted(lessons, key=lambda lesson: lesson['number'])
    return _cache[path]


def get_lesson(slug):
    for lesson in load_lessons():
        if lesson['slug'] == slug:
            return lesson
    return None


def neighbours(lesson):
    lessons = load_lessons()
    index = lessons.index(lesson)
    previous = lessons[index - 1] if index > 0 else None
    following = lessons[index + 1] if index + 1 < len(lessons) else None
    return previous, following


def sections():
    """Lessons grouped by section, sections in course order."""
    grouped = OrderedDict((name, []) for name in SECTION_ORDER)
    for lesson in load_lessons():
        grouped.setdefault(lesson['section'], []).append(lesson)
    return [(name, items) for name, items in grouped.items() if items]
