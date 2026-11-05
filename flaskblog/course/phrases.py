"""Frases fetes (Catalan idioms) for the C1/C2 course, from
course/data/frases_fetes.json:

    {"ca": "ploure a bots i barrals", "type": "frase feta" | "refrany",
     "theme": "temps", "level": "B2", "meaning_ca": "...",
     "uk": "...", "uk_idiom": "...", "en": "...", "fr": "...",
     "literal_uk": "...", "example_ca": "...", "example_uk": "...",
     "example_en": "...", "register": "col·loquial"}

Each entry was written and then checked by a second, independent pass;
only the ones both were sure about are in the file.
"""

import functools
import io
import json
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'frases_fetes.json')

# Order of the themes on the page, with their Ukrainian names.
THEMES = [
    ("emocions i estats d'ànim", 'Емоції та настрій'),
    ('caràcter i manera de ser', 'Характер'),
    ('temps', 'Погода, час і поспіх'),
    ('diners, feina i esforç', 'Гроші, робота і зусилля'),
    ('parlar, callar i comunicar-se', 'Говорити й мовчати'),
    ('problemes, errors i èxit', 'Проблеми, помилки й успіх'),
    ('menjar i beure', 'Їжа і напої'),
    ('el cos', 'Тіло'),
    ('animals', 'Тварини'),
    ('relacions, engany i sorpresa', 'Стосунки, обман і здивування'),
]


@functools.lru_cache(maxsize=1)
def load():
    try:
        with io.open(DATA_FILE, encoding='utf-8') as handle:
            return json.load(handle)
    except OSError:
        return []


def meaning(phrase, lang):
    """The meaning of a phrase in the reader's language (French falls back
    to English, which every entry has)."""
    if lang == 'uk':
        return phrase.get('uk') or phrase.get('en', '')
    return phrase.get(lang) or phrase.get('en', '')


def themes():
    """[(key, Ukrainian name, count)] for the themes that have phrases."""
    counts = {}
    for phrase in load():
        counts[phrase['theme']] = counts.get(phrase['theme'], 0) + 1
    return [(key, name, counts[key]) for key, name in THEMES if counts.get(key)]
