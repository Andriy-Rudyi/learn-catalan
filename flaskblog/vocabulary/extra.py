"""Words the dictionary was missing, from a check against a printed dictionary.

``data/extra_words.txt`` lists Catalan words, one a line, that a printed
Catalan-Spanish dictionary has and the site's dictionary (with the words
from DACCO and Apertium) did not. Only the words were taken: each one is
also in an open source (the Softcatalà thesaurus, the English Wiktionary's
translation tables or the conjugator's verb list), and nothing else of the
book, its translations or its notes, is used.

``flask vocabulary extra-words`` (:func:`import_words`) adds them, marked
``Word.source = 'extra'``. Where Wiktionary lists a word in an English
word's translation table, that English word and the Spanish words of the
same table go in as drafts, and the Ukrainian is derived from them like for
the other words (``pivot-import``). The others are added without a
translation: their page says so and they wait on the translation platform.
"""

import io
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'extra_words.txt')
SOURCE_TAG = 'extra'

# Wiktionary's and the thesaurus's parts of speech -> the site's.
_THESAURUS_POS = {'n': 'noun', 'v': 'verb', 'adj': 'adjective', 'adj/n': 'adjective',
                  'adv': 'adverb', 'ij': 'interjection', 'loc': 'phrase'}


def words():
    try:
        with io.open(DATA_FILE, encoding='utf-8') as handle:
            return [line.strip() for line in handle if line.strip() and not line.startswith('#')]
    except OSError:
        return []


def _part_of_speech(term, wiktionary_pos):
    from flaskblog.reader import morphology

    if wiktionary_pos:
        return wiktionary_pos
    base = term[:-3] if term.endswith('-se') else term
    if morphology.verbs().service.resolve(base) == base:
        return 'verb'
    groups = morphology.thesaurus().groups_of(term)
    return _THESAURUS_POS.get(groups[0][0]) if groups else None


def _join(items, limit=255):
    text = ''
    for item in items:
        candidate = item if not text else text + ', ' + item
        if len(candidate) > limit:
            break
        text = candidate
    return text


def import_words(terms=None):
    """Add the words (*terms*, by default the file's) the dictionary does not
    have. Safe to run again. Returns how many were added. The caller commits."""
    from flaskblog import db
    from flaskblog.models import Word
    from flaskblog.vocabulary import senses, wiktionary
    from flaskblog.vocabulary.dacco import _existing_keys, _free_slug

    known = _existing_keys(term for (term,) in Word.query.with_entities(Word.term))
    slugs = {slug for (slug,) in Word.query.with_entities(Word.slug)}
    added = 0
    for term in words() if terms is None else terms:
        if term.lower() in known:
            continue
        known.update(_existing_keys([term]))
        entry = wiktionary.catalan_entry(term)
        pos = _part_of_speech(term, entry[0] if entry else None)
        word = Word(term=term, slug=_free_slug(term, slugs), part_of_speech=pos, source=SOURCE_TAG)
        slugs.add(word.slug)
        if entry:
            english, spanish = [], []
            for en, es_words in entry[1]:
                if en not in english:
                    english.append(en)
                spanish.extend(es for es in es_words if es not in spanish)
            word.set_translation('en', _join(english[:3]))
            word.translations['en'].reviewed = False
            if spanish:
                word.set_translation('es', _join(spanish[:3]))
                word.translations['es'].reviewed = False
        db.session.add(word)
        if word.translations:
            senses.sync_from_flat(word)
        added += 1
    return added


def remove_words():
    """Take the words added by :func:`import_words` away again."""
    from flaskblog import db
    from flaskblog.models import Word

    found = Word.query.filter_by(source=SOURCE_TAG).all()
    for word in found:
        db.session.delete(word)
    return len(found)
