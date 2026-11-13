"""Spanish translations from Apertium's Spanish-Catalan dictionary.

Apertium (https://github.com/apertium/apertium-spa-cat, GPL-2.0) is an open
machine translation system; its bilingual dictionary
``apertium-spa-cat.spa-cat.metadix`` pairs Spanish and Catalan lemmas with
their part of speech. ``flask vocabulary apertium-convert <clone>``
(:func:`convert`) keeps the common words (no proper names, numbers or
internal entries) in ``data/sources/apertium/ca-es.jsonl``, one pair a line::

    {"ca": "fer mal", "es": "hacer daño", "pos": "vblex", "dir": "both"}
    {"ca": "moll", "es": "blando", "pos": "adj", "dir": "ca-es"}

``dir`` says which way the pair holds: both ways, only from Catalan to
Spanish, or only from Spanish to Catalan. Nouns also carry ``gender_ca`` /
``gender_es`` (m, f, mf).

``flask vocabulary apertium-import`` (:func:`import_translations`) gives
every dictionary word without a Spanish translation the Spanish words of
its pairs. ``flask vocabulary apertium-words`` (:func:`import_words`) adds
the Catalan words of the pairs that the dictionary does not have, marked
``Word.source = 'apertium'``. The file is also the start of a future
Spanish site. The data
and anything made from it stay under the GPL; credit Apertium.
"""

import functools
import io
import json
import os
import re
import xml.etree.ElementTree as ET

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'data', 'sources', 'apertium', 'ca-es.jsonl')
METADIX = 'apertium-spa-cat.spa-cat.metadix'

SOURCE = {
    'name': 'Apertium spa-cat bilingual dictionary',
    'url': 'https://github.com/apertium/apertium-spa-cat',
    'licence': 'GPL-2.0',
}

# Parts of speech kept, and the site's name for each.
POS = {
    'n': 'noun', 'vblex': 'verb', 'vbmod': 'verb', 'vbser': 'verb', 'vbhaver': 'verb',
    'adj': 'adjective', 'adv': 'adverb', 'preadv': 'adverb', 'pr': 'preposition',
    'prn': 'pronoun', 'det': 'pronoun', 'cnjcoo': 'conjunction', 'cnjsub': 'conjunction',
    'cnjadv': 'conjunction', 'ij': 'interjection',
}
_GENDERS = ('m', 'f', 'mf')
_DIRECTIONS = {None: 'both', 'RL': 'ca-es', 'LR': 'es-ca'}


def _side(element):
    """Text and symbols of an <l> or <r>: <b/> is a space, <g> keeps its words."""
    words, symbols = [element.text or ''], []

    def walk(node):
        for child in node:
            if child.tag == 'b':
                words.append(' ')
            elif child.tag == 'g':
                words.append(child.text or '')
                walk(child)
            elif child.tag == 's':
                symbols.append(child.get('n'))
            words.append(child.tail or '')

    walk(element)
    return re.sub(r'\s+', ' ', ''.join(words)).strip(), symbols


def _pair(entry):
    pairs = entry.findall('p')
    identity = entry.find('i')
    if len(pairs) == 1:
        es, es_tags = _side(pairs[0].find('l'))
        ca, ca_tags = _side(pairs[0].find('r'))
    elif identity is not None and not pairs:
        es, es_tags = _side(identity)
        ca, ca_tags = es, es_tags
    else:
        return None  # numbers, hours and other multi-part entries
    if not es or not ca or es.startswith('_') or ca.startswith('_'):
        return None
    pos = next((tag for tag in ca_tags if tag in POS), None)
    if pos is None or 'np' in ca_tags or 'np' in es_tags:
        return None
    pair = {'ca': ca, 'es': es, 'pos': pos, 'dir': _DIRECTIONS.get(entry.get('r'), 'both')}
    for key, tags in (('gender_ca', ca_tags), ('gender_es', es_tags)):
        gender = next((tag for tag in tags if tag in _GENDERS), None)
        if gender:
            pair[key] = gender
    if entry.get('w'):
        pair['weight'] = int(entry.get('w')) if entry.get('w').isdigit() else entry.get('w')
    return pair


def convert_file(path):
    """The pairs of an Apertium spa-cat metadix file, without duplicates."""
    root = ET.parse(path).getroot()
    found, seen = [], set()
    for section in root.findall('section'):
        for entry in section.findall('e'):
            pair = _pair(entry)
            if pair is None:
                continue
            key = (pair['ca'], pair['es'], pair['pos'], pair['dir'])
            if key not in seen:
                seen.add(key)
                found.append(pair)
    return found


def convert(repository, path=DATA_FILE):
    pairs = convert_file(os.path.join(repository, METADIX))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, 'w', encoding='utf-8') as handle:
        for pair in pairs:
            handle.write(json.dumps(pair, ensure_ascii=False, separators=(',', ':')) + '\n')
    load.cache_clear()
    _index.cache_clear()
    return len(pairs)


@functools.lru_cache(maxsize=1)
def load():
    try:
        with io.open(DATA_FILE, encoding='utf-8') as handle:
            return [json.loads(line) for line in handle if line.strip()]
    except OSError:
        return []


@functools.lru_cache(maxsize=1)
def _index():
    """{Catalan word: ((Spanish word, site part of speech), ...)}, the pairs
    that hold both ways first. Read straight from the file and kept small:
    the reader uses it on a server with little memory."""
    found = {}
    try:
        with io.open(DATA_FILE, encoding='utf-8') as handle:
            for line in handle:
                if not line.strip():
                    continue
                pair = json.loads(line)
                if pair['dir'] in ('both', 'ca-es'):
                    rank = (pair['dir'] != 'both', str(pair.get('weight', '')))
                    found.setdefault(pair['ca'].lower(), []).append((rank, pair['es'], POS[pair['pos']]))
    except OSError:
        return {}
    return {term: tuple((es, pos) for _rank, es, pos in sorted(rows)) for term, rows in found.items()}


def has(term):
    """True when Apertium pairs this Catalan word with a Spanish one."""
    return (term or '').strip().lower() in _index()


def spanish(term, part_of_speech=None):
    """The Spanish words for a Catalan term, the ones of its part of speech
    first (all of them when none matches)."""
    pairs = _index().get((term or '').strip().lower(), ())
    if not pairs and (term or '').endswith('-se'):
        pairs = _index().get(term[:-3].lower(), ())
    if part_of_speech:
        pairs = [pair for pair in pairs if pair[1] == part_of_speech] or pairs
    words = []
    for es, _pos in pairs:
        if es not in words:
            words.append(es)
    return words


SOURCE_TAG = 'apertium'
_WORD = re.compile(r"[A-Za-zÀ-ÿ·'’ -]{2,60}")
_GENDER_TO_SITE = {'m': 'm', 'f': 'f', 'mf': 'mf'}


def _join(words, limit=255):
    text = ''
    for word in words:
        candidate = word if not text else text + ', ' + word
        if len(candidate) > limit:
            break
        text = candidate
    return text


def import_words(pairs=None):
    """Add the Catalan words of Apertium (*pairs*, by default all) that the
    dictionary does not have, marked ``source='apertium'``: with their
    Spanish equivalents and, where Wiktionary lists the Catalan word next
    to one of them, the English word of that table, as a draft. Safe to
    run again. Returns how many were added. The caller commits."""
    from flaskblog import db
    from flaskblog.models import Word
    from flaskblog.vocabulary import senses, wiktionary
    from flaskblog.vocabulary.dacco import _existing_keys, _free_slug

    known = _existing_keys(term for (term,) in Word.query.with_entities(Word.term))
    slugs = {slug for (slug,) in Word.query.with_entities(Word.slug)}
    added = 0
    for pair in load() if pairs is None else pairs:
        term = pair['ca']
        if (pair['dir'] == 'es-ca' or term.lower() in known or not _WORD.fullmatch(term)
                or term.isupper()):   # abbreviations
            continue
        known.update(_existing_keys([term]))
        pos = 'phrase' if ' ' in term else POS[pair['pos']]
        found = spanish(term, POS[pair['pos']])
        if not found:
            continue
        word = Word(term=term, slug=_free_slug(term, slugs), part_of_speech=pos,
                    gender=_GENDER_TO_SITE.get(pair.get('gender_ca')) if pos == 'noun' else None,
                    source=SOURCE_TAG)
        slugs.add(word.slug)
        word.set_translation('es', _join(found))
        word.translations['es'].reviewed = True
        english = wiktionary.english(term, POS[pair['pos']], spanish=found)
        if english:
            word.set_translation('en', _join(english))
            word.translations['en'].reviewed = False
        db.session.add(word)
        senses.sync_from_flat(word)
        added += 1
        if added % 1000 == 0:
            db.session.flush()
    return added


def remove_words():
    """Take the words added by :func:`import_words` away again. Returns how
    many. The caller commits."""
    from flaskblog import db
    from flaskblog.models import Word

    words = Word.query.filter_by(source=SOURCE_TAG).all()
    for word in words:
        db.session.delete(word)
    return len(words)


def import_translations(words=None):
    """Give each word (all dictionary words by default) that has no Spanish
    translation yet the Spanish words Apertium pairs it with. Returns how
    many words got one. The caller commits."""
    from flaskblog.models import Word, WordTranslation
    from flaskblog.vocabulary import senses

    if words is None:
        words = Word.query.filter(~Word.translations.any(WordTranslation.lang == 'es')).all()
    added = 0
    for word in words:
        if word.translation_in('es', fallback=False) is not None:
            continue
        found = spanish(word.term, word.part_of_speech)
        if not found:
            continue
        text = ''
        for item in found:
            candidate = item if not text else text + ', ' + item
            if len(candidate) > 255:
                break
            text = candidate
        word.set_translation('es', text)
        entry = word.translations['es']
        entry.reviewed = True
        senses.sync_from_flat(word, ['es'])
        added += 1
    return added


def remove_translations():
    """Take away the Spanish translations nobody has edited on the site
    (those this import made). Returns how many. The caller commits."""
    from flaskblog.models import WordTranslation
    from flaskblog.vocabulary import senses

    removed = 0
    for entry in WordTranslation.query.filter_by(lang='es', edited=False).all():
        word = entry.word
        if word.source == SOURCE_TAG:
            continue  # the word itself came from Apertium: remove_words()
        del word.translations['es']
        senses.sync_from_flat(word, ['es'])
        removed += 1
    return removed


def stats(terms=()):
    pairs = load()
    lemmas = {p['ca'].lower() for p in pairs if p['dir'] in ('both', 'ca-es')}
    numbers = {'pairs': len(pairs), 'catalan_lemmas': len(lemmas),
               'spanish_lemmas': len({p['es'].lower() for p in pairs})}
    if terms:
        numbers['words'] = len(terms)
        numbers['words_found'] = sum(1 for t in terms if spanish(t))
    return numbers
